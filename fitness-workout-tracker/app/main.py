from fastapi import FastAPI

import app.models  # noqa: F401  -- registers the tables on Base
from app.database import Base, engine
from app.routers import auth, exercises, reports, workouts

Base.metadata.create_all(bind=engine)

DESCRIPTION = """
A REST API for planning workouts, scheduling them, and tracking progress over time.

### How to use these docs

1. `POST /auth/signup` to create an account.
2. `POST /auth/login` to get a JWT access token.
3. Click the **Authorize** button (top right) and paste the token.
4. Every `/workouts` and `/reports` endpoint is now available.

### Notes

* All timestamps are **UTC**. You may send any offset (`2026-08-20T18:00:00+07:00`)
  and it will be converted and returned as UTC.
* Access tokens expire after 60 minutes.
* You can only ever see and modify your own workouts. Another user's workout
  returns `404`, not `403`, so that IDs cannot be probed.
"""

TAGS_METADATA = [
    {
        "name": "auth",
        "description": "Sign up, log in, and inspect the current user. "
                       "Passwords are hashed with bcrypt and never returned.",
    },
    {
        "name": "exercises",
        "description": "The shared exercise catalogue. Public - no token required. "
                       "Filter by category, muscle group, or name.",
    },
    {
        "name": "workouts",
        "description": "Create, schedule, update and delete your own workouts. "
                       "Requires authentication.",
    },
    {
        "name": "reports",
        "description": "Aggregated statistics over your **completed** workouts: "
                       "totals, per-exercise breakdowns, and progress over time.",
    },
    {"name": "meta", "description": "Service health."},
]

app = FastAPI(
    title="Fitness Workout Tracker API",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
    contact={"name": "lmcuong199", "url": "https://github.com/lmcuong199/Backend"},
    license_info={"name": "MIT"},
)

app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(reports.router)

@app.get("/health", tags=["meta"], summary="Liveness check")
def health():
    """Returns `{"status": "ok"}` if the service is running."""
    return {"status": "ok"}
