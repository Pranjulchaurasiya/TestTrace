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


@app.get("/")
def root():
    return {
        "platform": "TestTrace",
        "tagline": "Test knowledge. Trace integrity.",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
    }
