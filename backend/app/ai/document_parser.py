"""Document Parsing and Groq LLM Question Extraction Service for School Subjects.

Extracts text from PDF, DOCX, XLSX, and CSV documents with zero external weight,
and parses or formats questions for school assessments (Math, Science, English, etc.)
using structured Groq LLM intelligence or deterministic regex rules.
"""

import os
import re
import json
from typing import List, Dict, Any
from io import BytesIO

# Light document parsers
import pypdf
import docx
import openpyxl

try:
    from groq import Groq
except ImportError:
    Groq = None


def extract_raw_text_from_file(filename: str, content: bytes) -> str:
    """Extracts raw text content from uploaded PDF, Word, or Excel file."""
    ext = filename.lower().split(".")[-1]

    if ext == "pdf":
        reader = pypdf.PdfReader(BytesIO(content))
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
        return "\n\n".join(text_parts)

    elif ext in ["docx", "doc"]:
        doc = docx.Document(BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # Also parse tables if present
        table_lines = []
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_lines.append(" | ".join(row_cells))
        return "\n".join(paragraphs + table_lines)

    elif ext in ["xlsx", "xls"]:
        wb = openpyxl.load_workbook(filename=BytesIO(content), data_only=True)
        sheets_data = []
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            rows = []
            for row in sheet.iter_rows(values_only=True):
                non_empty = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                if non_empty:
                    rows.append(" | ".join(non_empty))
            if rows:
                sheets_data.append(f"Sheet: {sheet_name}\n" + "\n".join(rows))
        return "\n\n".join(sheets_data)

    elif ext in ["txt", "csv", "md"]:
        return content.decode("utf-8", errors="ignore")

    else:
        raise ValueError(f"Unsupported file format: .{ext}. Allowed: PDF, DOCX, XLSX, CSV, TXT")


def parse_questions_with_groq(
    raw_text: str,
    subject: str = "General",
    groq_api_key: str | None = None,
) -> List[Dict[str, Any]]:
    """Uses Groq LLaMA 3.3 / 3.1 70B Versatile to parse and judge test questions from document text."""
    api_key = groq_api_key or os.environ.get("GROQ_API_KEY")

    if not api_key:
        # Fallback to local rule-based parsing if no API key is provided
        return parse_questions_rule_based(raw_text, subject)

    client = Groq(api_key=api_key)

    system_prompt = (
        "You are an expert school assessment parser. "
        "Your task is to analyze document text containing an exam, worksheet, or question bank "
        "for school students (subjects such as Math, Science, English, Grammar, Social Studies, Computer Science, etc.). "
        "Extract every distinct question into a strict JSON array. "
        "Each element of the array must have the following schema:\n"
        "{\n"
        '  "question_text": "Clear question string (include math symbols, reading passage snippets, or sentences)",\n'
        '  "question_type": "MCQ" | "TRUE_FALSE" | "SHORT_ANSWER" | "CODING",\n'
        '  "options": [{"id": "A", "text": "Option A"}, {"id": "B", "text": "Option B"}, ...],\n'
        '  "correct_answer": "A" or "True" or expected keywords/answer,\n'
        '  "marks": integer (e.g. 2, 5),\n'
        '  "starter_code": null or template string if Computer/Coding,\n'
        '  "coding_language": "python" or null,\n'
        '  "explanation_prompts": [{"id": "p1", "prompt": "Prompt asking student to explain why this answer is correct"}]\n'
        "}\n\n"
        "Rules:\n"
        "1. For MCQ questions, populate 'options' with id and text for each choice.\n"
        "2. For True/False, set 'options' to [{'id': 'True', 'text': 'True'}, {'id': 'False', 'text': 'False'}].\n"
        "3. For Short Answer or Math/Grammar questions with no options, set 'options' to null.\n"
        "4. Respond ONLY with the valid raw JSON array. Do not wrap in conversational markdown, greetings, or explanations."
    )

    prompt = (
        f"Subject: {subject}\n\n"
        f"Document Content:\n```\n{raw_text[:12000]}\n```\n\n"
        f"Extract all valid questions as a JSON array now:"
    )

    candidate_models = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
    ]

    chat_completion = None
    last_error = None
    for model_name in candidate_models:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                model=model_name,
                temperature=0.1,
                max_tokens=4096,
            )
            break
        except Exception as e:
            last_error = e
            continue

    if not chat_completion:
        print(f"[DocumentParser] All Groq models failed ({last_error}). Falling back to rule-based parser.")
        return parse_questions_rule_based(raw_text, subject)

    try:
        response_content = chat_completion.choices[0].message.content.strip()
        # Clean potential markdown fences
        if response_content.startswith("```json"):
            response_content = response_content[7:]
        if response_content.startswith("```"):
            response_content = response_content[3:]
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        response_content = response_content.strip()

        questions = json.loads(response_content)
        if isinstance(questions, list):
            return format_parsed_questions(questions)
        elif isinstance(questions, dict) and "questions" in questions:
            return format_parsed_questions(questions["questions"])
        else:
            return parse_questions_rule_based(raw_text, subject)

    except Exception as e:
        print(f"[DocumentParser] Groq extraction error ({e}). Falling back to rule-based parser.")
        return parse_questions_rule_based(raw_text, subject)


def parse_questions_rule_based(raw_text: str, subject: str = "General") -> List[Dict[str, Any]]:
    """Lightweight regex and line-based question extractor when Groq API key is not supplied."""
    lines = raw_text.splitlines()
    questions = []
    current_q = None

    q_pattern = re.compile(r"^(?:Q(?:uestion)?\s*[\d]+[\.\:]|[\d]+[\.\)])\s*(.*)", re.IGNORECASE)
    opt_pattern = re.compile(r"^([A-D])[\.\)]\s*(.*)", re.IGNORECASE)
    ans_pattern = re.compile(r"^(?:Ans(?:wer)?|Correct)\s*[\:\-]\s*([A-D]|True|False|.*)", re.IGNORECASE)

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        q_match = q_pattern.match(line_clean)
        if q_match:
            if current_q:
                questions.append(current_q)
            current_q = {
                "question_text": q_match.group(1).strip(),
                "question_type": "MCQ",
                "options": [],
                "correct_answer": None,
                "marks": 5,
                "starter_code": None,
                "coding_language": "python" if "computer" in subject.lower() or "programming" in subject.lower() else None,
                "explanation_prompts": [
                    {"id": "p1", "prompt": "Briefly explain the concept or working behind your answer."}
                ],
            }
            continue

        opt_match = opt_pattern.match(line_clean)
        if opt_match and current_q:
            opt_id = opt_match.group(1).upper()
            opt_text = opt_match.group(2).strip()
            current_q["options"].append({"id": opt_id, "text": opt_text})
            continue

        ans_match = ans_pattern.match(line_clean)
        if ans_match and current_q:
            current_q["correct_answer"] = ans_match.group(1).strip()
            continue

        if current_q:
            if not current_q["options"]:
                current_q["question_text"] += " " + line_clean

    if current_q:
        questions.append(current_q)

    # Post-process question types
    for q in questions:
        if not q["options"]:
            q["question_type"] = "SHORT_ANSWER"
        elif len(q["options"]) == 2 and any("true" in o["text"].lower() for o in q["options"]):
            q["question_type"] = "TRUE_FALSE"

    return format_parsed_questions(questions)


def format_parsed_questions(raw_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalizes parsed questions into the exact TestTrace DB schema format."""
    formatted = []
    for i, item in enumerate(raw_list, start=1):
        q_text = item.get("question_text", "").strip()
        if not q_text:
            continue

        q_type = item.get("question_type", "MCQ").upper()
        if q_type not in ["MCQ", "TRUE_FALSE", "SHORT_ANSWER", "CODING", "DEBUGGING"]:
            q_type = "MCQ" if item.get("options") else "SHORT_ANSWER"

        options = item.get("options")
        options_json = json.dumps(options) if options and isinstance(options, list) else None

        explanation_prompts = item.get("explanation_prompts", [
            {"id": "p1", "prompt": "Explain the reasoning behind your answer in 1-2 sentences."}
        ])

        formatted.append({
            "order_num": i,
            "question_text": q_text,
            "question_type": q_type,
            "options_json": options_json,
            "correct_answer": str(item.get("correct_answer", "")) if item.get("correct_answer") is not None else None,
            "marks": int(item.get("marks", 5)),
            "starter_code": item.get("starter_code"),
            "coding_language": item.get("coding_language") or "python",
            "test_cases_json": json.dumps(item.get("test_cases", [])) if item.get("test_cases") else None,
            "explanation_prompts_json": json.dumps(explanation_prompts),
        })

    return formatted
