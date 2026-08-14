import pytest


@pytest.fixture
def push_day(exercise_ids):
    return {
        "name": "Push Day",
        "scheduled_at": "2026-08-20T18:00:00+07:00",
        "comment": "lighter shoulders",
        "entries": [
            {"exercise_id": exercise_ids["Bench Press"], "sets": 4, "reps": 8, "weight": 60},
            {"exercise_id": exercise_ids["Overhead Press"], "sets": 3, "reps": 10, "weight": 30},
            {"exercise_id": exercise_ids["Plank"], "sets": 3, "reps": 1, "weight": None},
        ],
    }


def test_create_workout(client, alice, push_day):
    response = client.post("/workouts", json=push_day, headers=alice)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert len(body["entries"]) == 3
    assert "user_id" not in body


def test_entries_keep_their_order(client, alice, push_day):
    entries = client.post("/workouts", json=push_day, headers=alice).json()["entries"]
    assert [e["position"] for e in entries] == [0, 1, 2]
    assert entries[0]["exercise"]["name"] == "Bench Press"


def test_scheduled_at_is_converted_to_utc(client, alice, push_day):
    body = client.post("/workouts", json=push_day, headers=alice).json()
    assert body["scheduled_at"].startswith("2026-08-20T11:00:00")


def test_creating_requires_authentication(client, push_day):
    assert client.post("/workouts", json=push_day).status_code == 401


def test_unknown_exercise_id_is_rejected(client, alice, push_day):
    push_day["entries"] = [{"exercise_id": 9999, "sets": 1, "reps": 1}]
    response = client.post("/workouts", json=push_day, headers=alice)
    assert response.status_code == 400
    assert "9999" in response.json()["detail"]


def test_failed_create_writes_nothing(client, alice, push_day, exercise_ids):
    push_day["name"] = "Should Not Exist"
    push_day["entries"] = [
        {"exercise_id": exercise_ids["Squat"], "sets": 1, "reps": 1},
        {"exercise_id": 9999, "sets": 1, "reps": 1},
    ]
    client.post("/workouts", json=push_day, headers=alice)
    assert client.get("/workouts", headers=alice).json() == []


def test_invalid_payloads_are_rejected(client, alice, push_day, exercise_ids):
    empty = dict(push_day, entries=[])
    assert client.post("/workouts", json=empty, headers=alice).status_code == 422

    zero_sets = dict(push_day, entries=[{"exercise_id": exercise_ids["Squat"], "sets": 0, "reps": 1}])
    assert client.post("/workouts", json=zero_sets, headers=alice).status_code == 422

    no_name = dict(push_day, name="")
    assert client.post("/workouts", json=no_name, headers=alice).status_code == 422


def test_list_is_sorted_by_date_with_unscheduled_last(client, alice, make_workout, exercise_ids):
    entry = [{"exercise_id": exercise_ids["Squat"], "sets": 1, "reps": 1}]
    make_workout(alice, "Someday", None, entry)
    make_workout(alice, "Later", "2026-08-20T10:00:00Z", entry)
    make_workout(alice, "Sooner", "2026-08-18T10:00:00Z", entry)

    names = [w["name"] for w in client.get("/workouts", headers=alice).json()]
    assert names == ["Sooner", "Later", "Someday"]


def test_filter_by_status_and_upcoming(client, alice, make_workout, exercise_ids):
    entry = [{"exercise_id": exercise_ids["Squat"], "sets": 1, "reps": 1}]
    make_workout(alice, "Done", "2020-01-01T10:00:00Z", entry, completed=True)
    make_workout(alice, "Planned", "2030-01-01T10:00:00Z", entry)

    pending = client.get("/workouts", params={"status": "pending"}, headers=alice).json()
    assert [w["name"] for w in pending] == ["Planned"]

    upcoming = client.get("/workouts", params={"upcoming": "true"}, headers=alice).json()
    assert [w["name"] for w in upcoming] == ["Planned"]


def test_patch_only_changes_what_you_send(client, alice, push_day):
    workout_id = client.post("/workouts", json=push_day, headers=alice).json()["id"]
    response = client.patch(f"/workouts/{workout_id}", json={"status": "completed"}, headers=alice)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["name"] == "Push Day"
    assert len(body["entries"]) == 3


def test_patch_can_clear_a_field_and_replace_entries(client, alice, push_day, exercise_ids):
    workout_id = client.post("/workouts", json=push_day, headers=alice).json()["id"]

    cleared = client.patch(f"/workouts/{workout_id}", json={"comment": None}, headers=alice).json()
    assert cleared["comment"] is None

    new_entries = [{"exercise_id": exercise_ids["Squat"], "sets": 5, "reps": 5, "weight": 100}]
    replaced = client.patch(
        f"/workouts/{workout_id}", json={"entries": new_entries}, headers=alice
    ).json()
    assert len(replaced["entries"]) == 1
    assert replaced["entries"][0]["exercise"]["name"] == "Squat"


def test_invalid_status_is_rejected(client, alice, push_day):
    workout_id = client.post("/workouts", json=push_day, headers=alice).json()["id"]
    response = client.patch(f"/workouts/{workout_id}", json={"status": "finished"}, headers=alice)
    assert response.status_code == 422


def test_delete_removes_workout_and_its_entries(client, alice, push_day):
    workout_id = client.post("/workouts", json=push_day, headers=alice).json()["id"]
    assert client.delete(f"/workouts/{workout_id}", headers=alice).status_code == 204
    assert client.get(f"/workouts/{workout_id}", headers=alice).status_code == 404

    from app.database import SessionLocal
    from app.models import WorkoutExercise

    db = SessionLocal()
    orphans = db.query(WorkoutExercise).filter(WorkoutExercise.workout_id == workout_id).count()
    db.close()
    assert orphans == 0


# --- ownership: the security property of the whole project -------------------


def test_users_only_see_their_own_workouts(client, alice, bob, push_day):
    client.post("/workouts", json=push_day, headers=alice)
    assert client.get("/workouts", headers=bob).json() == []


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_other_users_cannot_touch_your_workout(client, alice, bob, push_day, method):
    workout_id = client.post("/workouts", json=push_day, headers=alice).json()["id"]

    call = getattr(client, method)
    kwargs = {"headers": bob}
    if method == "patch":
        kwargs["json"] = {"name": "hacked"}

    assert call(f"/workouts/{workout_id}", **kwargs).status_code == 404
    assert client.get(f"/workouts/{workout_id}", headers=alice).json()["name"] == "Push Day"
