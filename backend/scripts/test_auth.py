"""Verification script for simple username & password authentication."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import SessionLocal
from app.models.user import User
from app.auth.security import verify_password, create_access_token, decode_access_token


def test_auth():
    print("[TestTrace] Testing Simple Username/Password Authentication...")
    db = SessionLocal()
    try:
        # 1. Lookup by username
        user = db.query(User).filter_by(username="student").first()
        assert user is not None, "Student user not found!"
        print(f"  [PASS] Found student user: {user.username} ({user.email})")

        # 2. Test password verification
        is_valid = verify_password("Student@12345", user.password_hash)
        assert is_valid, "Password verification failed!"
        print("  [PASS] Verified password 'Student@12345' against PBKDF2 hash")

        # 3. Test wrong password
        is_invalid = verify_password("WrongPassword", user.password_hash)
        assert not is_invalid, "Wrong password was accepted!"
        print("  [PASS] Rejected wrong password as expected")

        # 4. Test Token generation and decoding
        token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
        payload = decode_access_token(token)
        assert payload is not None and payload["sub"] == user.id, "Token payload mismatch!"
        print(f"  [PASS] Successfully created and verified JWT token for user_id={user.id}")

        print("\nAll authentication checks passed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    test_auth()
