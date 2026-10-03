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
    """Ensures requested user accounts exist with updated credentials."""
    from app.database.database import SessionLocal
    from app.models.user import User
    from app.auth.security import get_password_hash

    db = SessionLocal()
    try:
        # Admin: username=admin, password=Pranjul27
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

        # Teacher: username=Teacher@2026, password=Password@2026
        teacher = db.query(User).filter((User.username == "Teacher@2026") | (User.username == "teacher")).first()
        if not teacher:
            teacher = User(
                username="Teacher@2026",
                name="Teacher",
                email="teacher@testtrace.org",
                password_hash=get_password_hash("Password@2026"),
                role="TEACHER",
            )
            db.add(teacher)
        else:
            teacher.username = "Teacher@2026"
            teacher.password_hash = get_password_hash("Password@2026")

        # Student: username=Prashant@pc, password=Prashant@2011
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
    except Exception as e:
        print(f"[Startup] Account setup warning: {e}")
        db.rollback()
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
