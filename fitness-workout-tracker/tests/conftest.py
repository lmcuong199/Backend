"""Shared test setup. pytest imports this before any test file."""
import os
import tempfile
from pathlib import Path

# MUST run before app.database is imported, or the app binds to your real workout.db
TEST_DB = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

# bcrypt is deliberately slow (~0.6s per hash). Tests do not need that cost.
os.environ["BCRYPT_ROUNDS"] = "4"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.seed import seed_exercises


@pytest.fixture(autouse=True)
def fresh_database():
    """Wipe and reseed before every single test, so tests can't affect each other."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_exercises(db)
    db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def _register(client, email):
    client.post("/auth/signup", json={"email": email, "password": "supersecret1"})
    response = client.post("/auth/login", json={"email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def alice(client):
    return _register(client, "alice@example.com")


@pytest.fixture
def bob(client):
    return _register(client, "bob@example.com")


@pytest.fixture
def exercise_ids(client):
    return {e["name"]: e["id"] for e in client.get("/exercises").json()}


@pytest.fixture
def make_workout(client):
    """Helper: create a workout and optionally mark it completed."""
    def _make(headers, name, scheduled_at=None, entries=None, completed=False):
        body = {"name": name, "scheduled_at": scheduled_at, "entries": entries or []}
        response = client.post("/workouts", json=body, headers=headers)
        assert response.status_code == 201, response.text
        workout_id = response.json()["id"]
        if completed:
            client.patch(f"/workouts/{workout_id}", json={"status": "completed"}, headers=headers)
        return workout_id
    return _make
