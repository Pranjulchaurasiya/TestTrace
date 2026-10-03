"""PDF Report Card and Integrity Certificate Generator for TestTrace."""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_report_card_pdf(
    student_name: str,
    student_email: str,
    exam_title: str,
    subject: str,
    attempt_id: int,
    start_time: datetime,
    submitted_at: datetime | None,
    final_score: float,
    total_marks: int,
    passing_marks: int,
    passed: bool,
    integrity_status: str,
    suspicious_score: int,
    tab_switch_count: int,
    total_questions: int,
    answered_count: int,
    questions_data: list[dict] = None,
) -> bytes:
    """Generates an institutional, formal PDF assessment report card and integrity certificate."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    brand_style = ParagraphStyle(
        "BrandHeader",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
    )

    sub_style = ParagraphStyle(
        "SubHeader",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748b"),
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("TestTrace Examination Report & Integrity Certificate", brand_style))
    elements.append(Paragraph("Test knowledge. Trace integrity. Institutional Assessment System", sub_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=15))

    # 2. Candidate & Exam Meta Table
    submitted_str = submitted_at.strftime("%Y-%m-%d %H:%M UTC") if submitted_at else "Not Recorded"
    started_str = start_time.strftime("%Y-%m-%d %H:%M UTC") if start_time else "Not Recorded"

    meta_table_data = [
        [
            Paragraph("<b>Candidate Name:</b>", body_style),
            Paragraph(student_name, body_style),
            Paragraph("<b>Attempt ID:</b>", body_style),
            Paragraph(f"#{attempt_id}", body_style),
        ],
        [
            Paragraph("<b>Account / Email:</b>", body_style),
            Paragraph(student_email or "student@testtrace.org", body_style),
            Paragraph("<b>Examination:</b>", body_style),
            Paragraph(exam_title, body_style),
        ],
        [
            Paragraph("<b>Curriculum / Subject:</b>", body_style),
            Paragraph(subject or "General", body_style),
            Paragraph("<b>Date & Time:</b>", body_style),
            Paragraph(submitted_str, body_style),
        ],
    ]

    meta_table = Table(meta_table_data, colWidths=[110, 160, 110, 150])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # 3. Assessment Performance Summary
    elements.append(Paragraph("Academic Assessment Summary", section_style))

    score_color = colors.HexColor("#16a34a") if passed else colors.HexColor("#dc2626")
    status_text = "PASSED" if passed else "DID NOT PASS"

    pct = round((final_score / max(1, total_marks)) * 100, 1)

    summary_data = [
        [
            Paragraph("<b>Total Score:</b>", body_style),
            Paragraph(f"<b>{final_score} / {total_marks} ({pct}%)</b>", body_style),
            Paragraph("<b>Assessment Status:</b>", body_style),
            Paragraph(f"<font color='{score_color.hexval()}'><b>{status_text}</b></font>", body_style),
        ],
        [
            Paragraph("<b>Passing Requirement:</b>", body_style),
            Paragraph(f"{passing_marks} marks", body_style),
            Paragraph("<b>Questions Answered:</b>", body_style),
            Paragraph(f"{answered_count} of {total_questions}", body_style),
        ],
    ]

    summary_table = Table(summary_data, colWidths=[120, 150, 120, 140])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 15))

    # 4. Proctoring & Biometric Integrity Verification
    elements.append(Paragraph("AI Proctoring & Biometric Integrity Trace", section_style))

    risk_hex = "#16a34a" if integrity_status == "LOW" else "#ea580c" if integrity_status == "MEDIUM" else "#dc2626"

    integrity_data = [
        [
            Paragraph("<b>Integrity Risk Rating:</b>", body_style),
            Paragraph(f"<font color='{risk_hex}'><b>{integrity_status} RISK</b></font>", body_style),
            Paragraph("<b>Cumulative Telemetry:</b>", body_style),
            Paragraph(f"{suspicious_score} penalty points", body_style),
        ],
        [
            Paragraph("<b>Tab Switches Recorded:</b>", body_style),
            Paragraph(f"{tab_switch_count} occurrence(s)", body_style),
            Paragraph("<b>Verification Mechanism:</b>", body_style),
            Paragraph("Face & Gaze Telemetry + YOLO Detection", body_style),
        ],
    ]

    integrity_table = Table(integrity_data, colWidths=[130, 140, 130, 130])
    integrity_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    elements.append(integrity_table)
    elements.append(Spacer(1, 15))

    # 5. Question Breakdown Table
    if questions_data:
        elements.append(Paragraph("Detailed Question Assessment", section_style))
        q_rows = [[
            Paragraph("<b>Q#</b>", body_style),
            Paragraph("<b>Question</b>", body_style),
            Paragraph("<b>Type</b>", body_style),
            Paragraph("<b>Marks</b>", body_style),
        ]]

        for q in questions_data[:10]:
            q_rows.append([
                Paragraph(str(q.get("order_num", 1)), body_style),
                Paragraph(q.get("question_text", "")[:80] + "...", body_style),
                Paragraph(str(q.get("question_type", "MCQ")), body_style),
                Paragraph(f"{q.get('marks_awarded', 0)} / {q.get('max_marks', 5)}", body_style),
            ])

        q_table = Table(q_rows, colWidths=[30, 340, 80, 80])
        q_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(q_table)
        elements.append(Spacer(1, 20))

    # 6. Official Institutional Footer
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    footer_text = Paragraph(
        "<i>This official assessment document was generated automatically by TestTrace. "
        "Integrity telemetry records browser activity, facial presence, and unauthorized device detection.</i>",
        sub_style,
    )
    elements.append(footer_text)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
