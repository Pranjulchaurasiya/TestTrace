import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import Base, engine
from app.routers import auth, exams, attempts, proctor

# Ensure database tables exist automatically on launch
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TestTrace API",
    description="AI-Assisted Secure Assessment and Proctoring Platform API",
    version="1.0.0",
)

# Enable CORS for React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(exams.router)
app.include_router(attempts.router)
app.include_router(proctor.router)


@app.on_event("startup")
def setup_initial_accounts():
    """Ensures requested user accounts exist with correct credentials.
    Uses separate transactions per account so one failure doesn't affect others.
    Uses delete+recreate to avoid unique constraint issues when renaming old accounts.
    """
    from sqlalchemy import func as sqlfunc
    from app.database.database import SessionLocal
    from app.models.user import User
    from app.auth.security import get_password_hash

    # Each entry: list of old usernames to purge, then the desired final account
    accounts = [
        {
            "old_usernames": ["admin"],
            "username": "admin",
            "name": "Pranjul Chaurasiya",
            "email": "admin@testtrace.org",
            "password": "Pranjul27",
            "role": "ADMIN",
        },
        {
            "old_usernames": ["Teacher@2026", "teacher"],
            "username": "Teacher@2026",
            "name": "Teacher",
            "email": "teacher@testtrace.org",
            "password": "Password@2026",
            "role": "TEACHER",
        },
        {
            "old_usernames": ["Prashant@pc", "student"],
            "username": "Prashant@pc",
            "name": "Prashant",
            "email": "prashant@testtrace.org",
            "password": "Prashant@2011",
            "role": "STUDENT",
        },
    ]

    for acc in accounts:
        db = SessionLocal()
        try:
            # Look up by any matching username or email
            existing = None
            for uname in acc["old_usernames"]:
                existing = db.query(User).filter(
                    (sqlfunc.lower(User.username) == uname.lower()) |
                    (sqlfunc.lower(User.email) == acc["email"].lower())
                ).first()
                if existing:
                    break

            if existing:
                # Update credentials & username in-place (keeps ID and relationships intact!)
                existing.username = acc["username"]
                existing.name = acc["name"]
                existing.email = acc["email"]
                existing.password_hash = get_password_hash(acc["password"])
                existing.role = acc["role"]
                existing.is_active = True
                db.commit()
                print(f"[Startup] Account updated: {acc['username']} ({acc['role']})")
            else:
                new_user = User(
                    username=acc["username"],
                    name=acc["name"],
                    email=acc["email"],
                    password_hash=get_password_hash(acc["password"]),
                    role=acc["role"],
                    is_active=True,
                )
                db.add(new_user)
                db.commit()
                print(f"[Startup] Account created: {acc['username']} ({acc['role']})")
        except Exception as e:
            db.rollback()
            print(f"[Startup] ERROR for {acc['username']}: {e}")
        finally:
            db.close()


@app.get("/")
def root():
    return {
        "platform": "TestTrace",
        "tagline": "Test knowledge. Trace integrity.",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
    }
