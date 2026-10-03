"""Seed rich school assessments across Math, Science, English, Grammar, and Computer Studies."""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import SessionLocal
from app.models.user import User
from app.models.exam import Exam
from app.models.question import Question


def seed_school_exams():
    db = SessionLocal()
    try:
        teacher = db.query(User).filter_by(username="teacher").first()
        if not teacher:
            print("Teacher user not found.")
            return

        # 1. Mathematics Exam
        math_exam = db.query(Exam).filter_by(title="Grade 8 Mathematics Assessment").first()
        if not math_exam:
            math_exam = Exam(
                title="Grade 8 Mathematics Assessment",
                subject="Mathematics",
                description="Algebraic equations, linear expressions, exponents, and geometric principles.",
                duration_minutes=25,
                total_marks=25,
                passing_marks=12,
                is_published=True,
                proctoring_enabled=True,
                auto_submit_on_violations=True,
                max_tab_switches_threshold=3,
                created_by=teacher.id,
            )
            db.add(math_exam)
            db.commit()
            db.refresh(math_exam)

            q_math1 = Question(
                exam_id=math_exam.id,
                question_text="Solve for x: 3x + 7 = 22",
                question_type="MCQ",
                options_json=json.dumps([
                    {"id": "A", "text": "x = 3"},
                    {"id": "B", "text": "x = 5"},
                    {"id": "C", "text": "x = 7"},
                    {"id": "D", "text": "x = 9"},
                ]),
                correct_answer="B",
                marks=5,
                order_num=1,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Show each arithmetic step you took to isolate x."}
                ]),
            )

            q_math2 = Question(
                exam_id=math_exam.id,
                question_text="The sum of the interior angles of a quadrilateral is always 360 degrees.",
                question_type="TRUE_FALSE",
                options_json=json.dumps([
                    {"id": "TRUE", "text": "True"},
                    {"id": "FALSE", "text": "False"},
                ]),
                correct_answer="TRUE",
                marks=5,
                order_num=2,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Why does dividing a quadrilateral into two triangles confirm this sum?"}
                ]),
            )

            q_math3 = Question(
                exam_id=math_exam.id,
                question_text="A rectangle has a length of 12 cm and a perimeter of 38 cm. What is its breadth in cm?",
                question_type="SHORT_ANSWER",
                correct_answer="7",
                marks=5,
                order_num=3,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "State the perimeter formula you used to find the breadth."}
                ]),
            )

            q_math4 = Question(
                exam_id=math_exam.id,
                question_text="Simplify the expression: (2^3) * (2^4)",
                question_type="MCQ",
                options_json=json.dumps([
                    {"id": "A", "text": "2^7 = 128"},
                    {"id": "B", "text": "2^12 = 4096"},
                    {"id": "C", "text": "4^7"},
                    {"id": "D", "text": "16"},
                ]),
                correct_answer="A",
                marks=10,
                order_num=4,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Which law of exponents applies when multiplying powers with the same base?"}
                ]),
            )
            db.add_all([q_math1, q_math2, q_math3, q_math4])
            db.commit()
            print("Seeded Grade 8 Mathematics Assessment.")

        # 2. General Science Exam
        science_exam = db.query(Exam).filter_by(title="General Science & Physics Fundamentals").first()
        if not science_exam:
            science_exam = Exam(
                title="General Science & Physics Fundamentals",
                subject="Science",
                description="Cell biology, states of matter, basic chemistry, and Newton's laws of motion.",
                duration_minutes=25,
                total_marks=20,
                passing_marks=10,
                is_published=True,
                proctoring_enabled=True,
                auto_submit_on_violations=True,
                max_tab_switches_threshold=3,
                created_by=teacher.id,
            )
            db.add(science_exam)
            db.commit()
            db.refresh(science_exam)

            q_sci1 = Question(
                exam_id=science_exam.id,
                question_text="Which organelle is known as the powerhouse of the cell?",
                question_type="MCQ",
                options_json=json.dumps([
                    {"id": "A", "text": "Ribosome"},
                    {"id": "B", "text": "Nucleus"},
                    {"id": "C", "text": "Mitochondria"},
                    {"id": "D", "text": "Endoplasmic Reticulum"},
                ]),
                correct_answer="C",
                marks=5,
                order_num=1,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "What chemical energy molecule does the mitochondria produce during cellular respiration?"}
                ]),
            )

            q_sci2 = Question(
                exam_id=science_exam.id,
                question_text="Sound waves can travel through a complete vacuum.",
                question_type="TRUE_FALSE",
                options_json=json.dumps([
                    {"id": "TRUE", "text": "True"},
                    {"id": "FALSE", "text": "False"},
                ]),
                correct_answer="FALSE",
                marks=5,
                order_num=2,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Explain why mechanical sound waves require a physical medium to propagate."}
                ]),
            )

            q_sci3 = Question(
                exam_id=science_exam.id,
                question_text="What is the chemical formula for water?",
                question_type="SHORT_ANSWER",
                correct_answer="H2O",
                marks=5,
                order_num=3,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Name the two elements and their ratio of atoms that make up a water molecule."}
                ]),
            )

            q_sci4 = Question(
                exam_id=science_exam.id,
                question_text="Which of Newton's laws states that for every action, there is an equal and opposite reaction?",
                question_type="MCQ",
                options_json=json.dumps([
                    {"id": "A", "text": "First Law (Inertia)"},
                    {"id": "B", "text": "Second Law (F=ma)"},
                    {"id": "C", "text": "Third Law"},
                    {"id": "D", "text": "Law of Gravitation"},
                ]),
                correct_answer="C",
                marks=5,
                order_num=4,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Give one everyday real-world example of action-reaction force pairs."}
                ]),
            )
            db.add_all([q_sci1, q_sci2, q_sci3, q_sci4])
            db.commit()
            print("Seeded General Science Assessment.")

        # 3. English & Grammar Exam
        eng_exam = db.query(Exam).filter_by(title="English Language & Grammar Mastery").first()
        if not eng_exam:
            eng_exam = Exam(
                title="English Language & Grammar Mastery",
                subject="English & Grammar",
                description="Parts of speech, sentence correction, active/passive voice, and vocabulary precision.",
                duration_minutes=20,
                total_marks=20,
                passing_marks=10,
                is_published=True,
                proctoring_enabled=True,
                auto_submit_on_violations=True,
                max_tab_switches_threshold=3,
                created_by=teacher.id,
            )
            db.add(eng_exam)
            db.commit()
            db.refresh(eng_exam)

            q_eng1 = Question(
                exam_id=eng_exam.id,
                question_text="Identify the part of speech of the underlined word: 'The dog ran *swiftly* across the field.'",
                question_type="MCQ",
                options_json=json.dumps([
                    {"id": "A", "text": "Adjective"},
                    {"id": "B", "text": "Adverb"},
                    {"id": "C", "text": "Conjunction"},
                    {"id": "D", "text": "Preposition"},
                ]),
                correct_answer="B",
                marks=5,
                order_num=1,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Which verb does 'swiftly' modify in the sentence, and how do you know it is an adverb?"}
                ]),
            )

            q_eng2 = Question(
                exam_id=eng_exam.id,
                question_text="Choose the correct sentence with proper subject-verb agreement:",
                question_type="MCQ",
                options_json=json.dumps([
                    {"id": "A", "text": "Either the teacher or the students was present in the hall."},
                    {"id": "B", "text": "Either the teacher or the students were present in the hall."},
                    {"id": "C", "text": "Either the teacher or the students is present in the hall."},
                    {"id": "D", "text": "Either the teacher or the students be present in the hall."},
                ]),
                correct_answer="B",
                marks=5,
                order_num=2,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Explain the proximity rule when two subjects are joined by 'either... or'."}
                ]),
            )

            q_eng3 = Question(
                exam_id=eng_exam.id,
                question_text="What is the antonym of the word 'Abundant'?",
                question_type="SHORT_ANSWER",
                correct_answer="Scarce",
                marks=5,
                order_num=3,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Use the word 'scarce' in a grammatically correct sentence."}
                ]),
            )

            q_eng4 = Question(
                exam_id=eng_exam.id,
                question_text="Convert the active sentence into passive voice: 'William Shakespeare wrote Hamlet.'",
                question_type="SHORT_ANSWER",
                correct_answer="Hamlet was written by William Shakespeare.",
                marks=5,
                order_num=4,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Identify how the grammatical subject and object swapped positions in passive voice."}
                ]),
            )
            db.add_all([q_eng1, q_eng2, q_eng3, q_eng4])
            db.commit()
            print("Seeded English & Grammar Assessment.")

        # 4. Computer & Programming Exam
        comp_exam = db.query(Exam).filter_by(title="Computer Applications & Basic Python").first()
        if not comp_exam:
            comp_exam = Exam(
                title="Computer Applications & Basic Python",
                subject="Computer & Programming",
                description="Computer memory hierarchy, basic input/output, and introductory Python programming.",
                duration_minutes=30,
                total_marks=25,
                passing_marks=12,
                is_published=True,
                proctoring_enabled=True,
                auto_submit_on_violations=True,
                max_tab_switches_threshold=3,
                created_by=teacher.id,
            )
            db.add(comp_exam)
            db.commit()
            db.refresh(comp_exam)

            q_comp1 = Question(
                exam_id=comp_exam.id,
                question_text="Which of the following is non-volatile computer memory?",
                question_type="MCQ",
                options_json=json.dumps([
                    {"id": "A", "text": "RAM"},
                    {"id": "B", "text": "Cache"},
                    {"id": "C", "text": "ROM"},
                    {"id": "D", "text": "Registers"},
                ]),
                correct_answer="C",
                marks=5,
                order_num=1,
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "What does non-volatile mean when computer power is turned off?"}
                ]),
            )

            q_comp2 = Question(
                exam_id=comp_exam.id,
                question_text="Write a Python program to calculate the area of a rectangle with length 15 and width 8.",
                question_type="CODING",
                starter_code="def calculate_area(length, width):\n    # Return the area of the rectangle\n    return length * width",
                coding_language="python",
                test_cases_json=json.dumps([
                    {"input": "15, 8", "expected_output": "120", "is_hidden": False},
                    {"input": "10, 5", "expected_output": "50", "is_hidden": True},
                ]),
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "Explain the arithmetic operator used to compute rectangular area in Python."}
                ]),
                marks=10,
                order_num=2,
            )

            q_comp3 = Question(
                exam_id=comp_exam.id,
                question_text="Fix the syntax error in this Python print statement:\n\n```python\nprint(\"Welcome to Computer Science!\n```",
                question_type="DEBUGGING",
                starter_code="print(\"Welcome to Computer Science!\")",
                coding_language="python",
                test_cases_json=json.dumps([
                    {"input": "", "expected_output": "Welcome to Computer Science!", "is_hidden": False}
                ]),
                explanation_prompts_json=json.dumps([
                    {"id": "p1", "prompt": "What punctuation character was missing in the original statement?"}
                ]),
                marks=10,
                order_num=3,
            )
            db.add_all([q_comp1, q_comp2, q_comp3])
            db.commit()
            print("Seeded Computer & Programming Assessment.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_school_exams()
