-- ============================================================================
-- TestTrace Relational Database Schema
-- Compatible with PostgreSQL 13+ and SQLite 3.35+
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: users
-- Core user accounts with role-based access control.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(60) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'STUDENT', -- 'STUDENT', 'TEACHER', 'ADMIN'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ----------------------------------------------------------------------------
-- Table: exams
-- Assessment definitions, duration limits, and proctoring policy flags.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    total_marks INTEGER NOT NULL DEFAULT 100,
    passing_marks INTEGER NOT NULL DEFAULT 40,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    proctoring_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    auto_submit_on_violations BOOLEAN NOT NULL DEFAULT TRUE,
    max_violations_threshold INTEGER NOT NULL DEFAULT 100,
    max_tab_switches_threshold INTEGER NOT NULL DEFAULT 3,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exams_subject ON exams(subject);
CREATE INDEX IF NOT EXISTS idx_exams_created_by ON exams(created_by);

-- ----------------------------------------------------------------------------
-- Table: questions
-- Question bank supporting MCQ, Coding, Debugging, and Viva follow-up prompts.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(30) NOT NULL, -- 'MCQ', 'TRUE_FALSE', 'SHORT_ANSWER', 'CODING', 'DEBUGGING'
    options_json TEXT, -- JSON array of choices for MCQ/TF: [{"id": "A", "text": "..."}]
    correct_answer TEXT, -- For MCQ/TF or reference answer for short answer
    starter_code TEXT, -- Boilerplate code for CODING/DEBUGGING
    coding_language VARCHAR(30) DEFAULT 'python', -- 'python', 'java', 'cpp', 'c'
    test_cases_json TEXT, -- JSON array: [{"input": "...", "expected_output": "...", "is_hidden": false}]
    explanation_prompts_json TEXT, -- JSON array of mini-viva follow-ups: [{"prompt": "...", "timer_seconds": 45}]
    marks INTEGER NOT NULL DEFAULT 5,
    order_num INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_exam_id ON questions(exam_id);

-- ----------------------------------------------------------------------------
-- Table: exam_attempts
-- Specific examination sessions, countdown anchors, and cumulative scores.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exam_attempts (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    scheduled_end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(30) NOT NULL DEFAULT 'IN_PROGRESS', -- 'IN_PROGRESS', 'SUBMITTED', 'TIME_EXPIRED', 'TERMINATED_VIOLATION'
    final_score NUMERIC(6, 2) DEFAULT 0.0,
    suspicious_score INTEGER NOT NULL DEFAULT 0,
    integrity_status VARCHAR(20) NOT NULL DEFAULT 'LOW', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    tab_switch_count INTEGER NOT NULL DEFAULT 0,
    fullscreen_exit_count INTEGER NOT NULL DEFAULT 0,
    termination_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_attempts_student_exam ON exam_attempts(student_id, exam_id);
CREATE INDEX IF NOT EXISTS idx_attempts_status ON exam_attempts(status);

-- ----------------------------------------------------------------------------
-- Table: student_answers
-- Incremental question answers and sandbox execution evaluation traces.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS student_answers (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER NOT NULL REFERENCES exam_attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    submitted_answer TEXT,
    execution_output TEXT,
    is_correct BOOLEAN,
    marks_awarded NUMERIC(5, 2) DEFAULT 0.0,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(attempt_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_answers_attempt_id ON student_answers(attempt_id);

-- ----------------------------------------------------------------------------
-- Table: explanation_responses
-- Post-submission rapid-fire viva explanations for coding understanding.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS explanation_responses (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER NOT NULL REFERENCES exam_attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    prompt_index INTEGER NOT NULL DEFAULT 0,
    prompt_text TEXT NOT NULL,
    student_explanation TEXT NOT NULL,
    response_time_seconds NUMERIC(5, 2),
    is_timed_out BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_explanations_attempt ON explanation_responses(attempt_id);

-- ----------------------------------------------------------------------------
-- Table: proctoring_events
-- Discrete timestamped integrity anomalies and point penalties.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proctoring_events (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER NOT NULL REFERENCES exam_attempts(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'TAB_SWITCH', 'FULLSCREEN_EXIT', 'PASTE_BURST', 'FACE_MISSING', 'LOOKING_LEFT', etc.
    severity VARCHAR(20) NOT NULL DEFAULT 'WARNING', -- 'INFO', 'WARNING', 'CRITICAL'
    points INTEGER NOT NULL DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT -- Arbitrary context: {"pitch": 25.4, "yaw": -30.1, "paste_length": 180}
);

CREATE INDEX IF NOT EXISTS idx_proctor_events_attempt ON proctoring_events(attempt_id);
CREATE INDEX IF NOT EXISTS idx_proctor_events_type ON proctoring_events(event_type);

-- ----------------------------------------------------------------------------
-- Table: audit_logs
-- Immutable security audit log for authentication and administrative actions.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
