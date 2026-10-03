# TestTrace — AI-Assisted Secure Assessment & Proctoring Platform

> **Test knowledge. Trace integrity.**

---

## 1. Executive Summary

**TestTrace** is a next-generation web-based assessment and automated proctoring platform designed to evaluate a student's actual problem-solving and conceptual understanding while preserving examination integrity.

Unlike standard quiz platforms that only record MCQ choices, and unlike legacy proctoring tools that behave as black-box lockouts, TestTrace combines:
1. **Server-Authoritative Examination Engine:** Strict server-side countdown timers, question randomization, and tamper-resistant state validation.
2. **Multi-Domain Assessment Types:** Multiple Choice, True/False, Short Answer, Coding (with in-browser / sandboxed execution), and Debugging challenges across multiple subjects (Python, Java, C/C++, Data Structures, Mathematics, and custom curricula).
3. **Dual-Layer Integrity Monitoring:**
   - **Browser-Level Signals:** Tab switching (`visibilitychange`), window blur/focus loss, fullscreen departures, and clipboard monitoring (paste burst analysis).
   - **Webcam-Based Computer Vision:** Real-time face presence tracking, multiple-person detection, gaze / head orientation estimation (via MediaPipe), and mobile phone detection (via YOLOv8).
4. **AI-Resistant Assessment Mechanics:** Defeats blind copying and LLM shortcut usage through parameterized problems, output prediction, and **post-submission explanation / mini-viva verification steps**.
5. **Examiner Intelligence & Audit Trails:** Second-by-second violation timeline replay, tiered risk assessment scores (Low, Medium, High, Critical), performance analytics, and exportable PDF audit certificates.

---

## 2. Core Architectural Principles

- **Integrity Signals, Not Automated Punishments:** AI detections (e.g., face missing, looking away, phone detected) are aggregated as probabilistic integrity signals and risk indicators for examiner review, preventing automated unfair failures due to lighting, glasses, or camera jitters.
- **Server Authority:** Timers, question banks, answers, and test-case evaluations are anchored on the backend. Client clocks cannot manipulate test durations.
- **Graceful Resource Degradation:** Lightweight MediaPipe client/server pipelines remain operational even in memory-constrained cloud environments (e.g. 512MB RAM free instances), while heavy neural networks (YOLOv8) can be toggled via environment settings.
- **Privacy by Design:** Explicit camera consent banners, encrypted network transit (HTTPS/WSS), role-based data isolation, and clear retention policies.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend UI** | React 18, Vite, Material-UI (MUI) / Tailwind CSS, Lucide Icons |
| **Code Editor** | Monaco Editor / CodeMirror |
| **Code Runner** | Pyodide (WASM in-browser Python sandbox) & Backend Docker sandbox |
| **Backend API** | FastAPI (Python 3.11+), Uvicorn, WebSockets, Pydantic v2 |
| **Database & ORM** | PostgreSQL (Neon Serverless) / SQLite (Development), SQLAlchemy 2.0 |
| **Computer Vision** | OpenCV, MediaPipe (FaceMesh / Landmark tracking), Ultralytics YOLOv8 |
| **Reporting & Export** | ReportLab (PDF Generation), CSV streaming |
| **Deployment Target** | Vercel (Frontend), Render / VPS (Backend), Neon (Database) |

---

## 4. Repository Structure

```text
TestTrace/
├── docs/
│   ├── ARCHITECTURE.md          # Detailed system architecture & data flow
│   ├── API_SPECIFICATION.md     # REST & WebSocket endpoint contracts
│   └── AI_RESISTANT_ASSESSMENT.md # Parameterization & Viva Explanation mechanics
├── schema/
│   └── schema.sql               # Pure SQL DDL schema for PostgreSQL / SQLite
├── backend/
│   ├── app/
│   │   ├── ai/                  # CV proctoring engines (MediaPipe, YOLO, scoring)
│   │   ├── auth/                # JWT auth, hashing, role guards (STUDENT, TEACHER, ADMIN)
│   │   ├── database/            # Database session & engine configurations
│   │   ├── models/              # SQLAlchemy relational models
│   │   ├── routers/             # API routes (auth, exams, attempts, proctor, reports)
│   │   └── schemas/             # Pydantic validation schemas
│   ├── requirements.txt         # Backend Python dependencies
│   └── scripts/
│       └── init_db.py           # Database migration & seeder script
└── frontend/                    # React + Vite application (to be implemented)
```

---

## 5. Getting Started

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm
- PostgreSQL (or SQLite for local zero-dependency testing)

### Quickstart (Backend)
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --reload --port 8000
```
Swagger API docs will be available at: `http://localhost:8000/docs`.

### Quickstart (Frontend)
```bash
cd frontend
npm install
npm run dev
```
The React interface will be running at: `http://localhost:5173`.

### Pre-Seeded Demo Credentials
- Student: `username: student` | `password: Student@12345`
- Teacher: `username: teacher` | `password: Teacher@12345`
- Admin:   `username: admin`   | `password: Admin@12345`

---

## 6. License & Attribution

TestTrace is an open-source educational assessment and integrity engineering project. Computer-vision proctoring patterns are inspired by the open-source research and community architectures in the online proctoring domain.
