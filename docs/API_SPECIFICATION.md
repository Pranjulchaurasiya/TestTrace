# TestTrace API Specification & Protocols

This document defines the REST and WebSocket API contracts for the TestTrace platform.

---

## 1. Authentication & User Management

### `POST /auth/register`
Creates a new user account.
- **Request Body:**
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "StrongPassword123!",
    "role": "STUDENT" // Allowed: "STUDENT", "TEACHER" (ADMIN requires admin token)
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane@example.com",
    "role": "STUDENT",
    "created_at": "2026-10-03T08:00:00Z"
  }
  ```

### `POST /auth/login`
Authenticates simple username (or email) and password, returning a JWT Bearer token.
- **Request Body (JSON):**
  ```json
  {
    "username": "student", // accepts either username or email
    "password": "Student@12345"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 3,
      "username": "student",
      "name": "Rahul Sharma",
      "email": "student@testtrace.org",
      "role": "STUDENT",
      "is_active": true
    }
  }
  ```

### `GET /auth/me`
Retrieves current authenticated profile. Header: `Authorization: Bearer <token>`.

---

## 2. Exam Management (Teacher / Admin)

### `GET /exams`
Lists available exams. Filterable by `subject`, `status`. Students only receive active/published exams.

### `POST /exams`
Creates an assessment. (Requires `TEACHER` or `ADMIN`).
- **Request Body:**
  ```json
  {
    "title": "Python Programming & Data Structures",
    "subject": "Python",
    "description": "Mid-term coding and theory assessment.",
    "duration_minutes": 45,
    "total_marks": 50,
    "passing_marks": 25,
    "proctoring_enabled": true,
    "auto_submit_on_violations": true,
    "max_violations_threshold": 100,
    "max_tab_switches_threshold": 3
  }
  ```

### `POST /exams/{id}/questions`
Appends a question to an exam.
- **Question Types:** `MCQ`, `TRUE_FALSE`, `SHORT_ANSWER`, `CODING`, `DEBUGGING`.
- **Request Body (Coding Example):**
  ```json
  {
    "question_text": "Write a function `reverse_words(s)` that reverses words in a sentence.",
    "question_type": "CODING",
    "marks": 10,
    "order_num": 1,
    "coding_language": "python",
    "starter_code": "def reverse_words(s: str) -> str:\n    # Your code here\n    pass",
    "test_cases": [
      { "input": "\"hello world\"", "expected_output": "\"world hello\"", "is_hidden": false },
      { "input": "\"Python is fun\"", "expected_output": "\"fun is Python\"", "is_hidden": true }
    ],
    "explanation_prompts": [
      { "prompt": "What is the time complexity of your string split and reverse logic?", "timer_seconds": 45 },
      { "prompt": "How does your code handle multiple consecutive spaces?", "timer_seconds": 45 }
    ]
  }
  ```

---

## 3. Examination Attempt Flow (Student)

### `POST /exams/{id}/attempts/start`
Initializes a secure attempt session and establishes the server-side time anchor.
- **Response (200 OK):**
  ```json
  {
    "attempt_id": 1024,
    "exam_id": 12,
    "title": "Python Programming & Data Structures",
    "start_time_utc": "2026-10-03T08:30:00Z",
    "scheduled_end_time_utc": "2026-10-03T09:15:00Z",
    "server_time_utc": "2026-10-03T08:30:00Z",
    "remaining_seconds": 2700,
    "proctoring_config": {
      "camera_required": true,
      "fullscreen_required": true,
      "max_tab_switches": 3,
      "max_violations_threshold": 100
    }
  }
  ```

### `GET /attempts/{id}/time-sync`
Returns authoritative countdown remaining seconds.
- **Response (200 OK):**
  ```json
  {
    "attempt_id": 1024,
    "server_time_utc": "2026-10-03T08:45:00Z",
    "remaining_seconds": 1800,
    "is_expired": false
  }
  ```

### `GET /attempts/{id}/questions`
Fetches questions with sanitized payloads (hidden test cases and correct answers are excluded).

### `POST /attempts/{id}/answer`
Saves an incremental answer for a question.
- **Request Body:**
  ```json
  {
    "question_id": 45,
    "submitted_answer": "def reverse_words(s):\n    return ' '.join(s.split()[::-1])",
    "execution_output": "All 2 public test cases passed."
  }
  ```

### `POST /attempts/{id}/viva-explanation`
Submits student explanations to post-code follow-up prompts.
- **Request Body:**
  ```json
  {
    "question_id": 45,
    "prompt_index": 0,
    "explanation_text": "I used split() which takes O(N) time and then sliced with [::-1] in O(N) time."
  }
  ```

### `POST /attempts/{id}/submit`
Formally submits the exam attempt, triggers grading, and marks status as `SUBMITTED`.

---

## 4. Proctoring & Telemetry Endpoints

### `POST /proctor/analyze-frame`
Sends a compressed JPEG webcam frame for server-side CV inference.
- **Request:** `multipart/form-data`
  - `attempt_id`: `1024`
  - `frame`: `[binary image/jpeg]`
- **Response (200 OK):**
  ```json
  {
    "attempt_id": 1024,
    "faces_detected": 1,
    "head_pose": { "pitch": 2.1, "yaw": -4.3, "direction": "STRAIGHT" },
    "eye_gaze": "FOCUSED",
    "phone_detected": false,
    "violation_detected": null,
    "current_suspicious_score": 0,
    "terminate_exam": false
  }
  ```

### `POST /proctor/violation`
Dispatches client-side telemetry events (tab switch, fullscreen drop, paste burst).
- **Request Body:**
  ```json
  {
    "attempt_id": 1024,
    "violation_type": "TAB_SWITCH", // "FULLSCREEN_EXIT", "PASTE_BURST"
    "metadata": { "duration_ms": 1420, "characters_pasted": 0 }
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "attempt_id": 1024,
    "violation_type": "TAB_SWITCH",
    "points_added": 5,
    "total_suspicious_score": 15,
    "tab_switch_count": 2,
    "terminate_exam": false,
    "warning_message": "Warning 2 of 3: Tab switching is strictly prohibited."
  }
  ```

---

## 5. Examiner Review & Reporting

### `GET /admin/attempts/{id}/timeline`
Returns the chronological audit log of all answers and proctoring violations for session replay.

### `GET /admin/attempts/{id}/pdf-report`
Streams a dynamically compiled PDF integrity report with student metrics, score breakdown, and violation telemetry.

---

## 6. Real-Time WebSockets

### Client Proctor Channel: `WS /ws/attempts/{attempt_id}`
Pushes real-time warnings and termination notices directly to the student UI.

### Teacher Proctor Console: `WS /ws/teacher/{exam_id}`
Broadcasts live violation events across all active students taking a given exam in real time.
- **Message Payload:**
  ```json
  {
    "event": "PROCTOR_VIOLATION",
    "attempt_id": 1024,
    "student_name": "Jane Doe",
    "event_type": "PHONE_DETECTED",
    "points": 10,
    "total_score": 25,
    "risk_level": "WARNING",
    "timestamp": "2026-10-03T08:52:14Z"
  }
  ```
