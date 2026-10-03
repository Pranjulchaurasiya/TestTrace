"""Groq LLM Evaluation Engine for School Assessments.

Judges student short answers, explanations, and math steps using Groq LLaMA models.
Fast, structured, deterministic JSON evaluation with zero heavy dependencies.
"""

import os
import json
from typing import Dict, Any

try:
    from groq import Groq
except ImportError:
    Groq = None


def judge_student_answer_with_groq(
    question_text: str,
    expected_answer: str,
    student_response: str,
    subject: str = "General",
    max_marks: float = 5.0,
    groq_api_key: str | None = None,
) -> Dict[str, Any]:
    """Judges a student's answer or step-by-step reasoning against the reference answer."""
    api_key = groq_api_key or os.environ.get("GROQ_API_KEY")

    if not api_key:
        # Fallback to normalized keyword similarity
        return fallback_rule_judge(student_response, expected_answer, max_marks)

    client = Groq(api_key=api_key)

    system_prompt = (
        "You are an encouraging, objective school teacher and examiner grading student answers. "
        "Evaluate the student's answer against the question and the reference answer. "
        "For Math and Science, credit valid working, step logic, or equivalent mathematical forms. "
        "For English and Grammar, check grammatical correctness, phrasing, and requested syntax. "
        "Respond ONLY with a strict JSON object:\n"
        "{\n"
        '  "is_correct": true | false,\n'
        '  "marks_awarded": float (between 0.0 and max_marks),\n'
        '  "feedback": "Short constructive sentence for the student",\n'
        '  "reasoning_summary": "1 sentence explanation of grade awarded"\n'
        "}\n"
        "Do NOT include markdown fences, greetings, or extra text."
    )

    user_prompt = (
        f"Subject: {subject}\n"
        f"Max Marks: {max_marks}\n"
        f"Question: {question_text}\n"
        f"Expected/Reference Answer: {expected_answer}\n"
        f"Student's Answer: {student_response}\n\n"
        f"Grade this submission now:"
    )

    candidate_models = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
    ]

    completion = None
    for model_name in candidate_models:
        try:
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=model_name,
                temperature=0.0,
                max_tokens=500,
            )
            break
        except Exception:
            continue

    if not completion:
        return fallback_rule_judge(student_response, expected_answer, max_marks)

    try:
        content = completion.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        data = json.loads(content)
        awarded = float(data.get("marks_awarded", 0.0))
        awarded = max(0.0, min(float(max_marks), awarded))

        return {
            "is_correct": bool(data.get("is_correct", awarded >= (max_marks * 0.5))),
            "marks_awarded": awarded,
            "feedback": data.get("feedback", "Good effort."),
            "reasoning_summary": data.get("reasoning_summary", ""),
        }
    except Exception as e:
        print(f"[GroqJudge] JSON parse error: {e}. Using deterministic fallback.")
        return fallback_rule_judge(student_response, expected_answer, max_marks)


def fallback_rule_judge(student_response: str, expected_answer: str, max_marks: float) -> Dict[str, Any]:
    """Lightweight rule-based grader when Groq is unreachable or key is not provided."""
    sub_clean = (student_response or "").strip().lower()
    exp_clean = (expected_answer or "").strip().lower()

    if not sub_clean:
        return {"is_correct": False, "marks_awarded": 0.0, "feedback": "No answer provided."}

    if sub_clean == exp_clean or exp_clean in sub_clean:
        return {
            "is_correct": True,
            "marks_awarded": float(max_marks),
            "feedback": "Correct answer.",
        }

    # Partial match for multi-word answers
    exp_words = set(exp_clean.split())
    sub_words = set(sub_clean.split())
    common = exp_words.intersection(sub_words)

    if common and len(exp_words) > 0:
        ratio = len(common) / len(exp_words)
        if ratio >= 0.6:
            score = round(float(max_marks) * ratio, 1)
            return {
                "is_correct": True,
                "marks_awarded": score,
                "feedback": "Partially correct answer.",
            }

    return {
        "is_correct": False,
        "marks_awarded": 0.0,
        "feedback": "Answer does not match expected solution.",
    }
