from datetime import datetime, timezone, timedelta
import json
import base64
import cv2
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session
from app.models.proctoring_event import ProctoringEvent
from app.ai.proctor_service import (
    decode_image_bytes,
    get_face_cascade,
    get_face_models,
    extract_deep_face_embedding,
    _enrolled_face_signatures,
)

from app.database.database import get_db
from app.models.exam import Exam
from app.models.question import Question
from app.models.exam_attempt import ExamAttempt
from app.models.student_answer import StudentAnswer
from app.models.explanation_response import ExplanationResponse
from app.models.user import User
from app.schemas.attempt import (
    AttemptStartResponse,
    AttemptResultResponse,
    TimeSyncResponse,
    AnswerSubmitRequest,
    AnswerResponse,
    VivaSubmitRequest,
    VivaResponse,
    ProctoringConfig,
)
from app.schemas.exam import QuestionSanitizedResponse
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/attempts", tags=["Exam Attempts"])


def to_utc(dt: datetime | None) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post("/exams/{exam_id}/start", response_model=AttemptStartResponse)
def start_exam_attempt(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initializes an exam attempt with a strict server-anchored UTC countdown."""
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.is_published == True).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found or not published")

    # Check for active existing in-progress attempt
    existing = db.query(ExamAttempt).filter(
        ExamAttempt.student_id == current_user.id,
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.status == "IN_PROGRESS",
    ).first()

    now_utc = datetime.now(timezone.utc)

    if existing:
        scheduled_utc = to_utc(existing.scheduled_end_time)
        if now_utc > scheduled_utc:
            existing.status = "TIME_EXPIRED"
            db.commit()
        else:
            remaining = max(0, int((scheduled_utc - now_utc).total_seconds()))
            return AttemptStartResponse(
                attempt_id=existing.id,
                exam_id=exam.id,
                title=exam.title,
                subject=exam.subject,
                duration_minutes=exam.duration_minutes,
                total_marks=exam.total_marks,
                start_time_utc=to_utc(existing.start_time),
                scheduled_end_time_utc=scheduled_utc,
                server_time_utc=now_utc,
                remaining_seconds=remaining,
                proctoring_config=ProctoringConfig(
                    proctoring_enabled=exam.proctoring_enabled,
                    auto_submit_on_violations=exam.auto_submit_on_violations,
                    max_violations_threshold=exam.max_violations_threshold,
                    max_tab_switches_threshold=exam.max_tab_switches_threshold,
                ),
            )

    # Create new attempt
    scheduled_end = now_utc + timedelta(minutes=exam.duration_minutes)
    attempt = ExamAttempt(
        student_id=current_user.id,
        exam_id=exam.id,
        start_time=now_utc,
        scheduled_end_time=scheduled_end,
        status="IN_PROGRESS",
        suspicious_score=0,
        integrity_status="LOW",
        tab_switch_count=0,
        fullscreen_exit_count=0,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    remaining = exam.duration_minutes * 60

    return AttemptStartResponse(
        attempt_id=attempt.id,
        exam_id=exam.id,
        title=exam.title,
        subject=exam.subject,
        duration_minutes=exam.duration_minutes,
        total_marks=exam.total_marks,
        start_time_utc=now_utc,
        scheduled_end_time_utc=scheduled_end,
        server_time_utc=now_utc,
        remaining_seconds=remaining,
        proctoring_config=ProctoringConfig(
            proctoring_enabled=exam.proctoring_enabled,
            auto_submit_on_violations=exam.auto_submit_on_violations,
            max_violations_threshold=exam.max_violations_threshold,
            max_tab_switches_threshold=exam.max_tab_switches_threshold,
        ),
    )


@router.post("/{attempt_id}/enroll-identity")
async def enroll_candidate_identity(
    attempt_id: int,
    photo: UploadFile | None = File(None),
    photo_base64: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enroll candidate's official reference photo prior to starting the timed examination."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt or attempt.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden or attempt not found")

    image_bytes = None
    data_uri = None

    if photo:
        image_bytes = await photo.read()
        b64 = base64.b64encode(image_bytes).decode('utf-8')
        mime = photo.content_type or 'image/jpeg'
        data_uri = f"data:{mime};base64,{b64}"
    elif photo_base64:
        try:
            if "," in photo_base64:
                header, encoded = photo_base64.split(",", 1)
                image_bytes = base64.b64decode(encoded)
                data_uri = photo_base64
            else:
                image_bytes = base64.b64decode(photo_base64)
                data_uri = f"data:image/jpeg;base64,{photo_base64}"
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
    else:
        raise HTTPException(status_code=400, detail="Missing candidate photo payload")

    frame = decode_image_bytes(image_bytes)
    if frame is None:
        raise HTTPException(status_code=400, detail="Failed to decode reference photo image.")

    h, w = frame.shape[:2]
    detector, recognizer = get_face_models((w, h))
    faces = []
    face_info = None

    if detector is not None:
        try:
            _, raw_faces = detector.detect(frame)
            if raw_faces is not None and len(raw_faces) > 0:
                for f_info in raw_faces:
                    fx, fy, fw, fh = int(f_info[0]), int(f_info[1]), int(f_info[2]), int(f_info[3])
                    faces.append((fx, fy, fw, fh))
                face_info = raw_faces[0]
        except Exception as e:
            print(f"[Enrollment] YuNet detection error: {e}")

    # Fallback to Haar cascade if YuNet is unavailable
    if len(faces) == 0 and detector is None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        cascade = get_face_cascade()
        if cascade and not cascade.empty():
            raw_faces = cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )
            for (fx, fy, fw, fh) in raw_faces:
                aspect = fh / float(fw)
                if 0.70 <= aspect <= 1.40:
                    faces.append((fx, fy, fw, fh))

    if len(faces) == 0:
        raise HTTPException(
            status_code=400,
            detail="No face detected. Please ensure your face is clearly visible, well-lit, and centered."
        )
    if len(faces) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple faces detected in frame. Only the registered student must be in front of the camera."
        )

    (x, y, fw, fh) = faces[0]

    # Extract 128-d deep facial feature vector via SFace
    deep_sig = extract_deep_face_embedding(frame, face_info)

    # Store in memory for instant biometric verification during the exam
    if deep_sig is not None:
        _enrolled_face_signatures[attempt.id] = deep_sig

    # Persist reference photo data URI on attempt record
    attempt.reference_photo = data_uri

    # Add audit log event
    event = ProctoringEvent(
        attempt_id=attempt.id,
        event_type="IDENTITY_ENROLLED",
        severity="INFO",
        points=0,
        timestamp=datetime.now(timezone.utc),
        metadata_json=json.dumps({"face_box": [int(x), int(y), int(fw), int(fh)]}),
    )
    db.add(event)
    db.commit()

    return {
        "success": True,
        "message": "Candidate biometric identity successfully verified and enrolled.",
        "attempt_id": attempt.id,
        "face_box": [int(x), int(y), int(fw), int(fh)],
        "reference_photo": data_uri,
    }


@router.get("/{attempt_id}/time-sync", response_model=TimeSyncResponse)
def time_sync(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Authoritative server countdown check. Enforces hard expiration."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id and current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    now_utc = datetime.now(timezone.utc)
    scheduled_utc = to_utc(attempt.scheduled_end_time)
    remaining = int((scheduled_utc - now_utc).total_seconds())
    is_expired = remaining <= 0

    if is_expired and attempt.status == "IN_PROGRESS":
        attempt.status = "TIME_EXPIRED"
        db.commit()

    return TimeSyncResponse(
        attempt_id=attempt.id,
        server_time_utc=now_utc,
        scheduled_end_time_utc=scheduled_utc,
        remaining_seconds=max(0, remaining),
        is_expired=is_expired,
    )


@router.get("/{attempt_id}/questions", response_model=list[QuestionSanitizedResponse])
def get_attempt_questions(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns sanitized question set for the active attempt."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id and current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    questions = db.query(Question).filter(Question.exam_id == attempt.exam_id).order_by(Question.order_num).all()

    sanitized = []
    for q in questions:
        public_tests = []
        if q.test_cases_json:
            try:
                all_tests = json.loads(q.test_cases_json)
                public_tests = [t for t in all_tests if not t.get("is_hidden", False)]
            except Exception:
                public_tests = []

        prompts = []
        if q.explanation_prompts_json:
            try:
                prompts = json.loads(q.explanation_prompts_json)
            except Exception:
                prompts = []

        sanitized.append(
            QuestionSanitizedResponse(
                id=q.id,
                exam_id=q.exam_id,
                question_text=q.question_text,
                question_type=q.question_type,
                options_json=q.options_json,
                starter_code=q.starter_code,
                coding_language=q.coding_language or "python",
                marks=q.marks,
                order_num=q.order_num,
                public_test_cases=public_tests,
                explanation_prompts=prompts,
            )
        )
    return sanitized


@router.post("/{attempt_id}/answer", response_model=AnswerResponse)
def submit_answer(
    attempt_id: int,
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Saves an incremental answer. Validates attempt time and status."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if attempt.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail=f"Cannot answer; attempt is {attempt.status}")

    now_utc = datetime.now(timezone.utc)
    if now_utc > to_utc(attempt.scheduled_end_time):
        attempt.status = "TIME_EXPIRED"
        db.commit()
        raise HTTPException(status_code=403, detail="Examination time has expired")

    question = db.query(Question).filter(Question.id == payload.question_id, Question.exam_id == attempt.exam_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this exam")

    # Check if answer row exists
    answer = db.query(StudentAnswer).filter(
        StudentAnswer.attempt_id == attempt_id,
        StudentAnswer.question_id == payload.question_id,
    ).first()

    # Pre-score for simple MCQ and TRUE_FALSE
    is_correct = None
    marks = 0.0
    clean_sub = payload.submitted_answer.strip()
    if question.question_type in ["MCQ", "TRUE_FALSE"] and question.correct_answer:
        if clean_sub.upper() == question.correct_answer.strip().upper():
            is_correct = True
            marks = float(question.marks)
        else:
            is_correct = False
            marks = 0.0
    elif question.question_type == "SHORT_ANSWER" and question.correct_answer:
        from app.ai.groq_judge import judge_student_answer_with_groq
        exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
        subj = exam.subject if exam else "General"
        judge_res = judge_student_answer_with_groq(
            question_text=question.question_text,
            expected_answer=question.correct_answer,
            student_response=payload.submitted_answer,
            subject=subj,
            max_marks=float(question.marks),
        )
        is_correct = judge_res.get("is_correct", False)
        marks = float(judge_res.get("marks_awarded", 0.0))

    if answer:
        answer.submitted_answer = payload.submitted_answer
        answer.execution_output = payload.execution_output
        answer.is_correct = is_correct
        answer.marks_awarded = marks
        answer.answered_at = now_utc
    else:
        answer = StudentAnswer(
            attempt_id=attempt_id,
            question_id=payload.question_id,
            submitted_answer=payload.submitted_answer,
            execution_output=payload.execution_output,
            is_correct=is_correct,
            marks_awarded=marks,
            answered_at=now_utc,
        )
        db.add(answer)

    db.commit()
    db.refresh(answer)

    return AnswerResponse(
        id=answer.id,
        question_id=answer.question_id,
        is_correct=answer.is_correct,
        marks_awarded=float(answer.marks_awarded),
        answered_at=answer.answered_at,
    )


@router.post("/{attempt_id}/viva-explanation", response_model=VivaResponse)
def submit_viva_explanation(
    attempt_id: int,
    payload: VivaSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submits student explanation to a mini-viva verification prompt."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt or attempt.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden or attempt not found")

    resp = ExplanationResponse(
        attempt_id=attempt_id,
        question_id=payload.question_id,
        prompt_index=payload.prompt_index,
        prompt_text=payload.prompt_text,
        student_explanation=payload.student_explanation,
        response_time_seconds=payload.response_time_seconds,
        is_timed_out=False,
    )
    db.add(resp)
    db.commit()
    db.refresh(resp)

    return VivaResponse(
        id=resp.id,
        question_id=resp.question_id,
        prompt_index=resp.prompt_index,
        student_explanation=resp.student_explanation,
        submitted_at=resp.submitted_at,
    )


@router.post("/{attempt_id}/submit", response_model=AttemptResultResponse)
def submit_exam_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Finalizes and scores the examination attempt."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id and current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
    student = db.query(User).filter(User.id == attempt.student_id).first()

    now_utc = datetime.now(timezone.utc)
    if attempt.status == "IN_PROGRESS":
        attempt.status = "SUBMITTED"
        attempt.submitted_at = now_utc

    # Calculate final score
    answers = db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt_id).all()
    total_score = sum(float(a.marks_awarded or 0.0) for a in answers)
    attempt.final_score = total_score
    db.commit()

    total_questions = db.query(Question).filter(Question.exam_id == attempt.exam_id).count()
    answered_count = len(answers)
    passed = total_score >= exam.passing_marks

    return AttemptResultResponse(
        attempt_id=attempt.id,
        student_id=student.id,
        student_name=student.name,
        exam_id=exam.id,
        exam_title=exam.title,
        status=attempt.status,
        final_score=float(attempt.final_score),
        total_marks=exam.total_marks,
        passing_marks=exam.passing_marks,
        passed=passed,
        start_time=attempt.start_time,
        submitted_at=attempt.submitted_at,
        suspicious_score=attempt.suspicious_score,
        integrity_status=attempt.integrity_status,
        tab_switch_count=attempt.tab_switch_count,
        fullscreen_exit_count=attempt.fullscreen_exit_count,
        termination_reason=attempt.termination_reason,
        total_questions=total_questions,
        answered_count=answered_count,
    )


@router.get("/{attempt_id}/result", response_model=AttemptResultResponse)
def get_attempt_result(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves finalized score and integrity evaluation for an attempt."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id and current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
    student = db.query(User).filter(User.id == attempt.student_id).first()
    total_questions = db.query(Question).filter(Question.exam_id == attempt.exam_id).count()
    answered_count = db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt_id).count()
    passed = float(attempt.final_score or 0.0) >= exam.passing_marks

    return AttemptResultResponse(
        attempt_id=attempt.id,
        student_id=student.id,
        student_name=student.name,
        exam_id=exam.id,
        exam_title=exam.title,
        status=attempt.status,
        final_score=float(attempt.final_score or 0.0),
        total_marks=exam.total_marks,
        passing_marks=exam.passing_marks,
        passed=passed,
        start_time=attempt.start_time,
        submitted_at=attempt.submitted_at,
        suspicious_score=attempt.suspicious_score,
        integrity_status=attempt.integrity_status,
        tab_switch_count=attempt.tab_switch_count,
        fullscreen_exit_count=attempt.fullscreen_exit_count,
        termination_reason=attempt.termination_reason,
        total_questions=total_questions,
        answered_count=answered_count,
    )


@router.get("/{attempt_id}/pdf-report")
def download_attempt_pdf_report(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates and streams a formal PDF report card and integrity certificate."""
    from fastapi.responses import Response
    from app.ai.report_generator import generate_report_card_pdf

    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.student_id != current_user.id and current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
    student = db.query(User).filter(User.id == attempt.student_id).first()
    total_q = db.query(Question).filter(Question.exam_id == attempt.exam_id).count()
    answered = db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt_id).count()
    passed = float(attempt.final_score or 0.0) >= (exam.passing_marks if exam else 0)

    # Detailed questions for report
    questions = db.query(Question).filter(Question.exam_id == attempt.exam_id).order_by(Question.order_num).all()
    answers = {a.question_id: a for a in db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt_id).all()}

    q_data = []
    for q in questions:
        ans = answers.get(q.id)
        q_data.append({
            "order_num": q.order_num,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "max_marks": q.marks,
            "marks_awarded": float(ans.marks_awarded) if (ans and ans.marks_awarded is not None) else 0.0,
        })

    pdf_bytes = generate_report_card_pdf(
        student_name=student.name if student else "Candidate",
        student_email=student.email if student else "student@testtrace.org",
        exam_title=exam.title if exam else "Assessment",
        subject=exam.subject if exam else "General",
        attempt_id=attempt.id,
        start_time=attempt.start_time,
        submitted_at=attempt.submitted_at,
        final_score=float(attempt.final_score or 0.0),
        total_marks=exam.total_marks if exam else 0,
        passing_marks=exam.passing_marks if exam else 0,
        passed=passed,
        integrity_status=attempt.integrity_status,
        suspicious_score=attempt.suspicious_score,
        tab_switch_count=attempt.tab_switch_count,
        total_questions=total_q,
        answered_count=answered,
        questions_data=q_data,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=TestTrace_Report_Attempt_{attempt.id}.pdf"
        },
    )


@router.get("/overview", response_model=list[AttemptResultResponse])
def get_all_attempts_overview(
    exam_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves all attempts for Teacher or Admin dashboard review."""
    if current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    query = db.query(ExamAttempt)
    if exam_id:
        query = query.filter(ExamAttempt.exam_id == exam_id)
    elif current_user.role == "TEACHER":
        # Only attempts for exams created by this teacher
        teacher_exam_ids = [e.id for e in db.query(Exam.id).filter(Exam.created_by == current_user.id).all()]
        query = query.filter(ExamAttempt.exam_id.in_(teacher_exam_ids))

    attempts = query.order_by(ExamAttempt.id.desc()).all()

    results = []
    for att in attempts:
        exam = db.query(Exam).filter(Exam.id == att.exam_id).first()
        student = db.query(User).filter(User.id == att.student_id).first()
        total_q = db.query(Question).filter(Question.exam_id == att.exam_id).count()
        answered = db.query(StudentAnswer).filter(StudentAnswer.attempt_id == att.id).count()
        passed = float(att.final_score or 0.0) >= (exam.passing_marks if exam else 0)

        results.append(
            AttemptResultResponse(
                attempt_id=att.id,
                student_id=student.id if student else 0,
                student_name=student.name if student else "Unknown Student",
                exam_id=exam.id if exam else 0,
                exam_title=exam.title if exam else "Unknown Exam",
                status=att.status,
                final_score=float(att.final_score or 0.0),
                total_marks=exam.total_marks if exam else 0,
                passing_marks=exam.passing_marks if exam else 0,
                passed=passed,
                start_time=att.start_time,
                submitted_at=att.submitted_at,
                suspicious_score=att.suspicious_score,
                integrity_status=att.integrity_status,
                tab_switch_count=att.tab_switch_count,
                fullscreen_exit_count=att.fullscreen_exit_count,
                termination_reason=att.termination_reason,
                total_questions=total_q,
                answered_count=answered,
            )
        )

    return results


@router.get("/{attempt_id}/answers")
def get_attempt_answers_for_teacher(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves full student answers and questions for manual teacher inspection and grading."""
    if current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    questions = db.query(Question).filter(Question.exam_id == attempt.exam_id).order_by(Question.order_num).all()
    answers = {a.question_id: a for a in db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt_id).all()}

    items = []
    for q in questions:
        ans = answers.get(q.id)
        items.append({
            "question_id": q.id,
            "order_num": q.order_num,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "max_marks": q.marks,
            "correct_answer": q.correct_answer,
            "submitted_answer": ans.submitted_answer if ans else None,
            "marks_awarded": float(ans.marks_awarded) if (ans and ans.marks_awarded is not None) else 0.0,
            "is_correct": ans.is_correct if ans else False,
            "answered_at": ans.answered_at.isoformat() if (ans and ans.answered_at) else None,
        })

    return {
        "attempt_id": attempt.id,
        "student_id": attempt.student_id,
        "final_score": float(attempt.final_score or 0.0),
        "reference_photo": attempt.reference_photo,
        "items": items,
    }


@router.post("/{attempt_id}/override-grade")
def override_question_grade(
    attempt_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allows teacher to manually adjust marks and status for any student question."""
    if current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    question_id = payload.get("question_id")
    new_marks = float(payload.get("marks_awarded", 0.0))
    is_correct = bool(payload.get("is_correct", new_marks > 0))

    ans = db.query(StudentAnswer).filter(
        StudentAnswer.attempt_id == attempt_id,
        StudentAnswer.question_id == question_id,
    ).first()

    if not ans:
        ans = StudentAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            submitted_answer="[Manual Grade Assignment]",
            is_correct=is_correct,
            marks_awarded=new_marks,
            answered_at=datetime.now(timezone.utc),
        )
        db.add(ans)
    else:
        ans.marks_awarded = new_marks
        ans.is_correct = is_correct

    db.commit()

    # Recalculate attempt final score
    all_answers = db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt_id).all()
    total = sum(float(a.marks_awarded or 0.0) for a in all_answers)
    attempt.final_score = total
    db.commit()

    return {
        "status": "success",
        "attempt_id": attempt_id,
        "question_id": question_id,
        "updated_marks": new_marks,
        "new_final_score": total,
    }


@router.get("/my-history", response_model=list[AttemptResultResponse])
def get_student_attempt_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns past completed examinations and scores for the logged-in student."""
    attempts = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.student_id == current_user.id)
        .order_by(ExamAttempt.id.desc())
        .all()
    )

    results = []
    for att in attempts:
        exam = db.query(Exam).filter(Exam.id == att.exam_id).first()
        total_q = db.query(Question).filter(Question.exam_id == att.exam_id).count()
        answered = db.query(StudentAnswer).filter(StudentAnswer.attempt_id == att.id).count()
        passed = float(att.final_score or 0.0) >= (exam.passing_marks if exam else 0)

        results.append(
            AttemptResultResponse(
                attempt_id=att.id,
                student_id=current_user.id,
                student_name=current_user.name,
                exam_id=exam.id if exam else 0,
                exam_title=exam.title if exam else "Unknown Exam",
                status=att.status,
                final_score=float(att.final_score or 0.0),
                total_marks=exam.total_marks if exam else 0,
                passing_marks=exam.passing_marks if exam else 0,
                passed=passed,
                start_time=att.start_time,
                submitted_at=att.submitted_at,
                suspicious_score=att.suspicious_score,
                integrity_status=att.integrity_status,
                tab_switch_count=att.tab_switch_count,
                fullscreen_exit_count=att.fullscreen_exit_count,
                termination_reason=att.termination_reason,
                total_questions=total_q,
                answered_count=answered,
            )
        )

    return results
