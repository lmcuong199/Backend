from fastapi import FastAPI

import app.models  # noqa: F401  -- registers the tables on Base
from app.database import Base, engine
from app.routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fitness Workout Tracker API",
    description="Track workouts, schedule sessions, and review your progress.",
    version="0.1.0",
)

app.include_router(auth.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
