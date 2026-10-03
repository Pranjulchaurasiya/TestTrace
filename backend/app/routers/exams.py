import json
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.exam import Exam
from app.models.question import Question
from app.models.user import User
from app.schemas.exam import (
    ExamCreate,
    ExamResponse,
    QuestionCreate,
    QuestionDetailResponse,
    QuestionSanitizedResponse,
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.get("", response_model=list[ExamResponse])
def list_exams(
    subject: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists accessible exams. Students receive only published exams."""
    query = db.query(Exam)

    if current_user.role == "STUDENT":
        query = query.filter(Exam.is_published == True)
    elif current_user.role == "TEACHER":
        query = query.filter((Exam.created_by == current_user.id) | (Exam.is_published == True))

    if subject:
        query = query.filter(Exam.subject.ilike(f"%{subject}%"))

    exams = query.order_by(Exam.id.desc()).all()

    result = []
    for exam in exams:
        count = db.query(Question).filter(Question.exam_id == exam.id).count()
        item = ExamResponse.model_validate(exam)
        item.question_count = count
        result.append(item)

    return result


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves single exam overview."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    count = db.query(Question).filter(Question.exam_id == exam.id).count()
    resp = ExamResponse.model_validate(exam)
    resp.question_count = count
    return resp


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["TEACHER", "ADMIN"])),
):
    """Creates a new exam (Teachers and Admins only)."""
    exam = Exam(
        title=payload.title.strip(),
        subject=payload.subject.strip(),
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        total_marks=payload.total_marks,
        passing_marks=payload.passing_marks,
        proctoring_enabled=payload.proctoring_enabled,
        auto_submit_on_violations=payload.auto_submit_on_violations,
        max_violations_threshold=payload.max_violations_threshold,
        max_tab_switches_threshold=payload.max_tab_switches_threshold,
        is_published=True,
        created_by=current_user.id,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    resp = ExamResponse.model_validate(exam)
    resp.question_count = 0
    return resp


@router.get("/{exam_id}/questions")
def get_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns questions for an exam. Students receive sanitized questions."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    questions = db.query(Question).filter(Question.exam_id == exam_id).order_by(Question.order_num).all()

    if current_user.role in ["TEACHER", "ADMIN"]:
        return [QuestionDetailResponse.model_validate(q) for q in questions]

    # Sanitize for students: omit correct answers and hidden test cases
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

        item = QuestionSanitizedResponse(
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
        sanitized.append(item)

    return sanitized


@router.post("/{exam_id}/questions", response_model=QuestionDetailResponse, status_code=status.HTTP_201_CREATED)
def add_question(
    exam_id: int,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["TEACHER", "ADMIN"])),
):
    """Adds a question to an exam."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    question = Question(
        exam_id=exam_id,
        question_text=payload.question_text,
        question_type=payload.question_type,
        options_json=payload.options_json,
        correct_answer=payload.correct_answer,
        starter_code=payload.starter_code,
        coding_language=payload.coding_language,
        test_cases_json=payload.test_cases_json,
        explanation_prompts_json=payload.explanation_prompts_json,
        marks=payload.marks,
        order_num=payload.order_num,
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    return QuestionDetailResponse.model_validate(question)


@router.post("/{exam_id}/upload-questions")
async def upload_and_parse_questions(
    exam_id: int,
    file: UploadFile = File(...),
    groq_api_key: str | None = Form(None),
    auto_save: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["TEACHER", "ADMIN"])),
):
    """Parses questions directly from PDF, Word (.docx), Excel (.xlsx), or CSV files using lightweight parsing & Groq."""
    from app.ai.document_parser import extract_raw_text_from_file, parse_questions_with_groq

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        raw_text = extract_raw_text_from_file(file.filename, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read document: {str(e)}")

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in document")

    parsed_questions = parse_questions_with_groq(
        raw_text=raw_text,
        subject=exam.subject,
        groq_api_key=groq_api_key,
    )

    if not parsed_questions:
        raise HTTPException(status_code=400, detail="Could not detect or parse any questions from document.")

    saved_count = 0
    if auto_save:
        # Determine current max order
        current_max = (
            db.query(Question.order_num)
            .filter(Question.exam_id == exam_id)
            .order_by(Question.order_num.desc())
            .first()
        )
        base_order = current_max[0] if current_max else 0

        for q_data in parsed_questions:
            base_order += 1
            q = Question(
                exam_id=exam_id,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                options_json=q_data["options_json"],
                correct_answer=q_data["correct_answer"],
                starter_code=q_data["starter_code"],
                coding_language=q_data["coding_language"] or "python",
                test_cases_json=q_data["test_cases_json"],
                explanation_prompts_json=q_data["explanation_prompts_json"],
                marks=q_data["marks"],
                order_num=base_order,
            )
            db.add(q)
            saved_count += 1
        db.commit()

    return {
        "status": "success",
        "exam_id": exam_id,
        "questions_parsed": len(parsed_questions),
        "questions_saved": saved_count,
        "questions": parsed_questions,
    }
