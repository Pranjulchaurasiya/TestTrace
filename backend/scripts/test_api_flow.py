"""End-to-end API integration test script for TestTrace."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def run_e2e_test():
    print("[TestTrace] Running End-to-End API Integration Suite...")

    # 1. Root healthcheck
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.text}"
    print("  [PASS] Root healthcheck OK")

    # 2. Login as student
    login_res = client.post(
        "/auth/login",
        json={"username": "student", "password": "Student@12345"},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  [PASS] Student authenticated, token received")

    # 3. List exams
    exams_res = client.get("/exams", headers=headers)
    assert exams_res.status_code == 200, f"List exams failed: {exams_res.text}"
    exams = exams_res.json()
    assert len(exams) > 0, "No exams returned"
    exam_id = exams[0]["id"]
    print(f"  [PASS] Fetched {len(exams)} exam(s). Selected Exam ID {exam_id} ('{exams[0]['title']}')")

    # 4. Start exam attempt
    start_res = client.post(f"/attempts/exams/{exam_id}/start", headers=headers)
    assert start_res.status_code == 200, f"Start attempt failed: {start_res.text}"
    attempt_data = start_res.json()
    attempt_id = attempt_data["attempt_id"]
    print(f"  [PASS] Attempt #{attempt_id} created with {attempt_data['remaining_seconds']}s remaining")

    # 5. Authoritative time sync check
    sync_res = client.get(f"/attempts/{attempt_id}/time-sync", headers=headers)
    assert sync_res.status_code == 200, f"Time sync failed: {sync_res.text}"
    sync_data = sync_res.json()
    assert sync_data["remaining_seconds"] > 0, "Timer should have time remaining"
    print(f"  [PASS] Server time synced: {sync_data['remaining_seconds']}s remaining")

    # 6. Fetch sanitized questions
    q_res = client.get(f"/attempts/{attempt_id}/questions", headers=headers)
    assert q_res.status_code == 200, f"Fetch questions failed: {q_res.text}"
    questions = q_res.json()
    assert len(questions) > 0, "No questions returned"
    print(f"  [PASS] Fetched {len(questions)} sanitized questions")

    # 7. Submit MCQ answer
    q1 = questions[0]
    ans_res = client.post(
        f"/attempts/{attempt_id}/answer",
        headers=headers,
        json={"question_id": q1["id"], "submitted_answer": "B"},
    )
    assert ans_res.status_code == 200, f"Submit answer failed: {ans_res.text}"
    ans_data = ans_res.json()
    assert ans_data["is_correct"] is True, "Answer 'B' should be correct for Q1"
    print(f"  [PASS] Submitted answer for Q1. Correct: {ans_data['is_correct']}, Marks: {ans_data['marks_awarded']}")

    # 8. Submit Mini-Viva explanation
    viva_res = client.post(
        f"/attempts/{attempt_id}/viva-explanation",
        headers=headers,
        json={
            "question_id": questions[-1]["id"],
            "prompt_index": 0,
            "prompt_text": "Explain why you chose split() and join() and what is the space complexity?",
            "student_explanation": "I used split() to tokenize by spaces in O(N) time and O(N) auxiliary space, followed by join.",
            "response_time_seconds": 18.5,
        },
    )
    assert viva_res.status_code == 200, f"Viva submit failed: {viva_res.text}"
    print("  [PASS] Submitted rapid mini-viva explanation")

    # 9. Test browser violation reporting
    v1_res = client.post(
        "/proctor/violation",
        headers=headers,
        json={"attempt_id": attempt_id, "violation_type": "TAB_SWITCH"},
    )
    assert v1_res.status_code == 200, f"Violation 1 failed: {v1_res.text}"
    v1_data = v1_res.json()
    assert v1_data["tab_switch_count"] == 1, "Tab switch count should be 1"
    print(f"  [PASS] Recorded Tab Switch 1/3 (Total suspicious score: {v1_data['total_suspicious_score']})")

    v2_res = client.post(
        "/proctor/violation",
        headers=headers,
        json={"attempt_id": attempt_id, "violation_type": "FULLSCREEN_EXIT"},
    )
    assert v2_res.status_code == 200, f"Violation 2 failed: {v2_res.text}"
    v2_data = v2_res.json()
    assert v2_data["fullscreen_exit_count"] == 1, "Fullscreen exit count should be 1"
    print(f"  [PASS] Recorded Fullscreen Exit (Total suspicious score: {v2_data['total_suspicious_score']})")

    # 10. Submit exam and verify results
    sub_res = client.post(f"/attempts/{attempt_id}/submit", headers=headers)
    assert sub_res.status_code == 200, f"Submit exam failed: {sub_res.text}"
    result = sub_res.json()
    assert result["status"] == "SUBMITTED", "Status should be SUBMITTED"
    assert result["final_score"] >= 5.0, "Score should include Q1 marks"
    print(f"  [PASS] Final Exam Result: Score={result['final_score']}/{result['total_marks']}, Status={result['status']}, Suspicious Score={result['suspicious_score']}")

    # 11. Fetch chronological proctoring timeline
    events_res = client.get(f"/proctor/attempts/{attempt_id}/events", headers=headers)
    assert events_res.status_code == 200, f"Fetch events failed: {events_res.text}"
    events = events_res.json()
    assert len(events) >= 2, "Expected at least 2 proctoring events"
    print(f"  [PASS] Chronological event audit log verified: {len(events)} events recorded")

    print("\nAll End-to-End API Integration Tests Passed Successfully!")


if __name__ == "__main__":
    run_e2e_test()
