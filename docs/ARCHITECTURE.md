# TestTrace System Architecture & Engineering Blueprint

This document details the architectural design, component interactions, security model, and data flow of **TestTrace**.

---

## 1. High-Level Architecture

TestTrace is organized as a decoupled, client-server system with real-time bidirectional telemetry:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        STUDENT CLIENT BROWSER                          │
│                                                                        │
│   ┌─────────────────────┐   ┌─────────────────┐   ┌────────────────┐   │
│   │   Exam UI (React)   │   │  Monaco Editor  │   │ Pyodide (WASM) │   │
│   │ MCQ / Coding / Viva │   │  Code Editor    │   │ Local Sandbox  │   │
│   └──────────┬──────────┘   └────────┬────────┘   └───────┬────────┘   │
│              │                       │                    │            │
│              └───────────────────────┼────────────────────┘            │
│                                      │                                 │
│   ┌──────────────────────────────────┴─────────────────────────────┐   │
│   │                      Client Telemetry Layer                    │   │
│   │  • Fullscreen API Listener     • Visibility / Tab Switch Hook  │   │
│   │  • Clipboard Burst Monitor     • Canvas Video Frame Compressor │   │
│   └──────────────────────────────────┬─────────────────────────────┘   │
└──────────────────────────────────────┼─────────────────────────────────┘
                                       │ HTTPS (REST) & WSS (WebSockets)
                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       TESTTRACE FASTAPI BACKEND                        │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                     API Gateway & Auth Layer                   │   │
│   │   • JWT Auth Bearer Guard  • Role Guard (STUDENT/TEACHER/ADMIN)│   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌────────────────────────────────┼───────────────────────────────┐   │
│   │ Core Assessment Services       │ CV Proctoring Subsystem       │   │
│   │ • Server-Side Timer Engine     │ • MediaPipe FaceMesh / Iris   │   │
│   │ • Question Randomizer          │ • 3D Head Pose (PnP / Euler)  │   │
│   │ • Answer & Testcase Evaluator  │ • YOLOv8 Object Detector      │   │
│   │ • Post-Submission Viva Engine  │ • Attempt Violation Aggregator│   │
│   └────────────────────────────────┴───────────────┬───────────────┘   │
│                                                    │                   │
│   ┌────────────────────────────────────────────────┴───────────────┐   │
│   │ WebSocket Manager (Real-time Broadcast to Examiner Console)    │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
└────────────────────────────────────┼───────────────────────────────────┘
                                     │ SQLAlchemy ORM 2.0
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     PERSISTENCE LAYER (PostgreSQL)                     │
│                                                                        │
│   • users        • exams             • questions                       │
│   • exam_attempts• student_answers   • proctoring_events               │
│   • explanation_responses            • audit_logs                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Server-Authoritative Timer & Anti-Tampering Engine

A fundamental vulnerability in conventional web-based test software is trusting the browser's JavaScript clock (`Date.now()`, `setInterval`). Students can tamper with system time, pause the JS execution thread via browser devtools, or spoof submission timestamps.

TestTrace eliminates this vulnerability using **server-authoritative time anchoring**:

1. **Attempt Genesis (`POST /attempts/start`):**
   - The server marks `start_time = UTC_TIMESTAMP`.
   - The server calculates `scheduled_end_time = start_time + duration_minutes`.
   - The response delivers `server_time_utc` and `remaining_seconds`.
2. **Periodic Synchronization Heartbeat (`GET /attempts/{id}/time-sync`):**
   - The client timer acts purely as a local display proxy.
   - Every 30 seconds (or on question transition), the client syncs with the server's remaining duration.
3. **Hard Server Enforcement (`POST /attempts/{id}/submit` or `POST /attempts/{id}/answer`):**
   - Any answer payload arriving where `current_utc_time > scheduled_end_time + grace_period (e.g. 15s)` is rejected with `403 Forbidden` (`EXAM_TIME_EXPIRED`).
   - If an attempt expires before explicit student submission, background cron or the next request automatically transitions the attempt status to `TIME_EXPIRED` and triggers automated final grading.

---

## 3. Computer Vision & Integrity Telemetry Pipeline

### 3.1 Edge-to-Cloud Video Stream Handling
To prevent requiring high-bandwidth raw WebRTC video servers and to operate seamlessly on standard cloud hosts (Vercel + Render/Neon), TestTrace uses **periodic compressed frame sampling**:
1. Client requests user camera via `navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: 640, height: 480 } })`.
2. Every 2 to 3 seconds, a frame is projected onto an off-screen HTML5 `<canvas>` element and exported as a lightweight compressed JPEG blob (`quality: 0.6`, ~25–40 KB).
3. The blob is sent to `POST /proctor/analyze-frame` with `attempt_id`.
4. Inference takes ~25–60 ms on CPU, generating structured telemetry before the response returns to the client.

### 3.2 Vision Pipelines & Models

#### A. Face Detection & Presence (MediaPipe Face Detection)
- **Zero Faces:** Trigger `FACE_MISSING` if absent for consecutive frames (Points: +1).
- **One Face:** Nominal condition.
- **$\ge 2$ Faces:** Trigger `MULTIPLE_FACES` (Points: +5).

#### B. 3D Head Pose & Gaze Tracking (MediaPipe FaceMesh)
- Uses key facial landmarks (nose tip, chin, eye corners, mouth corners).
- Calculates rotation angles (Pitch, Yaw, Roll) via Perspective-n-Point (`cv2.solvePnP`):
  - **Yaw $> +25^\circ$:** Flag `LOOKING_RIGHT` (Points: +2).
  - **Yaw $< -25^\circ$:** Flag `LOOKING_LEFT` (Points: +2).
  - **Pitch $> +20^\circ$:** Flag `LOOKING_DOWN` (Points: +2).
  - **Pitch $< -20^\circ$:** Flag `LOOKING_UP` (Points: +2).
- Iris tracking determines if eyes are deviated while the head remains still (`LOOKING_AWAY`, Points: +2).

#### C. Mobile Device Detection (Ultralytics YOLOv8)
- Model: `yolov8n.pt` (Nano model, COCO weights, Class ID 67: `cell phone`).
- If confidence threshold $\ge 0.55$: Flag `PHONE_DETECTED` (Points: +10).
- Configurable via `ENABLE_PHONE_DETECTION=true/false` in `.env` to operate smoothly on low-memory servers (e.g., Render Free 512 MB).

### 3.3 Browser-Level Violation Detection
- **Tab Switching:** Monitored via HTML5 Page Visibility API (`document.visibilityState === 'hidden'`). Points: +5.
  - *Hard Stop Rule:* 3rd tab switch triggers immediate automated exam submission.
- **Fullscreen Exit:** Monitored via `fullscreenchange` events. Points: +5.
- **Clipboard Burst:** Text inputs track pasted character volume. A sudden paste of $> 50$ characters in a single keystroke triggers `PASTE_BURST` (Points: +3).

---

## 4. Concurrency & Scalability Model

### Resolving Multi-Student Concurrency
Legacy implementations often store the current score in global Python variables (e.g., `current_attempt_id = None`, `suspicious_score = 0`). This fails under concurrent student sessions or multi-worker ASGI environments.

TestTrace enforces **strict isolation keyed by `attempt_id`**:
1. All proctoring events are persisted immediately to the `proctoring_events` table under foreign key `attempt_id`.
2. Live attempt states are tracked in-memory using an `AttemptSessionRegistry` dictionary keyed by `attempt_id` (or Redis in multi-instance clusters).
3. The cumulative `suspicious_score` and risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) are computed dynamically via SQL aggregation:
   $$\text{suspicious\_score} = \sum \text{points}(\text{event}_i)$$
4. WebSocket rooms are segmented per attempt (`/ws/attempts/{attempt_id}`) and per teacher (`/ws/teacher/{exam_id}`), ensuring zero cross-student data leakage.

---

## 5. Security, Authorization & Privacy Matrix

### 5.1 Role-Based Access Control (RBAC)

| Role | Access Permissions |
| :--- | :--- |
| **STUDENT** | Read assigned exams; start attempt; read questions for active attempt; submit answers; view own completed results. Cannot view other attempts, hidden test cases, or correct answer keys. |
| **TEACHER** | Create/edit/delete exams and questions; view all student attempts for their exams; view real-time proctoring streams and violation timelines; override scores; generate PDF reports. |
| **ADMIN** | Full system administration; manage user accounts, assign roles, access global analytics, and review system-wide audit logs. |

### 5.2 Privacy Safeguards
1. **No Raw Video Storage:** TestTrace does **not** record or store continuous video streams. Only lightweight numerical event logs (timestamps, event type, penalty points) are saved permanently.
2. **Optional Violation Keyframes:** If configured by the institution, only single-frame thumbnail snapshots at the exact instant of a critical violation (e.g., `PHONE_DETECTED`) are cached for examiner audit, with automatic expiration after 30 days.
3. **Transparent Consent:** A pre-test system check screen informs the candidate of all monitored parameters before entering fullscreen mode.
