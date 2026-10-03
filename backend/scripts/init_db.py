"""Database initialization and seeding script for TestTrace."""

import json
import os
import sys

# Add parent directory to sys.path so app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import Base, SessionLocal, engine
from app.models import (
    AuditLog,
    Exam,
    ExamAttempt,
    ExplanationResponse,
    ProctoringEvent,
    Question,
    StudentAnswer,
    User,
)


from app.auth.security import get_password_hash


def init_db():
    print("[TestTrace] Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("[TestTrace] Tables created successfully.")

    db = SessionLocal()
    try:
        # Check if users already exist
        # Ensure requested accounts exist with updated passwords
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                name="Pranjul Chaurasiya",
                email="admin@testtrace.org",
                password_hash=get_password_hash("Pranjul27"),
                role="ADMIN",
            )
            db.add(admin)
        else:
            admin.password_hash = get_password_hash("Pranjul27")

        teacher = db.query(User).filter((User.username == "Teacher@2026") | (User.username == "teacher")).first()
        if not teacher:
            teacher = User(
                username="Teacher@2026",
                name="Instructor",
                email="teacher@testtrace.org",
                password_hash=get_password_hash("Password@2026"),
                role="TEACHER",
            )
            db.add(teacher)
        else:
            teacher.username = "Teacher@2026"
            teacher.password_hash = get_password_hash("Password@2026")

        student = db.query(User).filter((User.username == "Prashant@pc") | (User.username == "student")).first()
        if not student:
            student = User(
                username="Prashant@pc",
                name="Prashant",
                email="prashant@pc.testtrace.org",
                password_hash=get_password_hash("Prashant@2011"),
                role="STUDENT",
            )
            db.add(student)
        else:
            student.username = "Prashant@pc"
            student.password_hash = get_password_hash("Prashant@2011")

        db.commit()
        db.refresh(teacher)

        print("[TestTrace] Seeding sample multi-type exam...")
        # 2. Sample Exam
        exam = Exam(
            title="Python Fundamentals & Algorithmic Logic",
            subject="Python",
            description="Comprehensive assessment covering core Python syntax, debugging logic, and algorithmic coding with viva verification.",
            duration_minutes=30,
            total_marks=35,
            passing_marks=15,
            is_published=True,
            proctoring_enabled=True,
            auto_submit_on_violations=True,
            max_violations_threshold=100,
            max_tab_switches_threshold=3,
            created_by=teacher.id,
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        # 3. Questions
        q1 = Question(
            exam_id=exam.id,
            question_text="What is the output of the following Python snippet?\n\n```python\nx = [1, 2, 3]\ny = x\ny.append(4)\nprint(len(x))\n```",
            question_type="MCQ",
            options_json=json.dumps([
                {"id": "A", "text": "3"},
                {"id": "B", "text": "4"},
                {"id": "C", "text": "Error"},
                {"id": "D", "text": "None"},
            ]),
            correct_answer="B",
            marks=5,
            order_num=1,
        )

        q2 = Question(
            exam_id=exam.id,
            question_text="In Python, tuples are mutable while lists are immutable.",
            question_type="TRUE_FALSE",
            options_json=json.dumps([
                {"id": "TRUE", "text": "True"},
                {"id": "FALSE", "text": "False"},
            ]),
            correct_answer="FALSE",
            marks=5,
            order_num=2,
        )

        q3 = Question(
            exam_id=exam.id,
            question_text="Identify and rectify the bug in the following function designed to return the average of non-empty numbers list.\n\n```python\ndef compute_average(nums):\n    total = 0\n    for i in range(len(nums) + 1):  # Bug here\n        total += nums[i]\n    return total / len(nums)\n```",
            question_type="DEBUGGING",
            starter_code="def compute_average(nums):\n    total = 0\n    for i in range(len(nums)): # Fixed\n        total += nums[i]\n    return total / len(nums)",
            coding_language="python",
            test_cases_json=json.dumps([
                {"input": "[10, 20, 30]", "expected_output": "20.0", "is_hidden": False},
                {"input": "[5, 15]", "expected_output": "10.0", "is_hidden": True},
            ]),
            marks=10,
            order_num=3,
        )

        q4 = Question(
            exam_id=exam.id,
            question_text="Write a function `reverse_words(sentence: str) -> str` that reverses the order of words in a sentence while preserving single spacing between words.",
            question_type="CODING",
            starter_code="def reverse_words(sentence: str) -> str:\n    # Implement your logic here\n    pass",
            coding_language="python",
            test_cases_json=json.dumps([
                {"input": "\"hello world\"", "expected_output": "\"world hello\"", "is_hidden": False},
                {"input": "\"Python makes coding fun\"", "expected_output": "\"fun coding makes Python\"", "is_hidden": True},
            ]),
            explanation_prompts_json=json.dumps([
                {
                    "prompt": "What is the asymptotic time and space complexity of your word reversal implementation?",
                    "timer_seconds": 45,
                },
                {
                    "prompt": "How does your code handle leading or trailing whitespace?",
                    "timer_seconds": 45,
                },
            ]),
            marks=15,
            order_num=4,
        )

        db.add_all([q1, q2, q3, q4])
        db.commit()

        print("[TestTrace] Database seeding completed successfully!")
        print("  - Admin:   admin@testtrace.org / Admin@12345")
        print("  - Teacher: teacher@testtrace.org / Teacher@12345")
        print("  - Student: student@testtrace.org / Student@12345")
        print(f"  - Exam:    '{exam.title}' with 4 questions (35 marks total).")

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
