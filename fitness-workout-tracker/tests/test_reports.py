import pytest


@pytest.fixture
def training_history(alice, make_workout, exercise_ids):
    """Three completed bench sessions at 60 -> 70 -> 80 kg, plus one pending workout."""
    bench = exercise_ids["Bench Press"]
    squat = exercise_ids["Squat"]
    plank = exercise_ids["Plank"]

    make_workout(alice, "Week 1", "2026-01-05T10:00:00Z", [
        {"exercise_id": bench, "sets": 3, "reps": 10, "weight": 60},
        {"exercise_id": plank, "sets": 3, "reps": 1, "weight": None},
    ], completed=True)
    make_workout(alice, "Week 2", "2026-01-12T10:00:00Z", [
        {"exercise_id": bench, "sets": 3, "reps": 10, "weight": 70},
        {"exercise_id": squat, "sets": 5, "reps": 5, "weight": 100},
    ], completed=True)
    make_workout(alice, "Week 3", "2026-01-19T10:00:00Z", [
        {"exercise_id": bench, "sets": 3, "reps": 10, "weight": 80},
    ], completed=True)
    make_workout(alice, "Not done yet", "2030-01-01T10:00:00Z", [
        {"exercise_id": bench, "sets": 1, "reps": 1, "weight": 999},
    ])


def test_reports_require_authentication(client):
    assert client.get("/reports/summary").status_code == 401
    assert client.get("/reports/exercises").status_code == 401


def test_summary_counts_every_status(client, alice, training_history):
    body = client.get("/reports/summary", headers=alice).json()
    assert body["total_workouts"] == 4
    assert body["by_status"] == {"pending": 1, "completed": 3, "cancelled": 0}


def test_summary_totals_only_completed_workouts(client, alice, training_history):
    body = client.get("/reports/summary", headers=alice).json()
    # 3*10*60 + plank(0) + 3*10*70 + 5*5*100 + 3*10*80
    assert body["total_volume"] == 8800.0
    assert body["total_sets"] == 17
    assert body["total_reps"] == 118


def test_summary_date_range(client, alice, training_history):
    body = client.get(
        "/reports/summary", params={"date_from": "2026-01-10T00:00:00Z"}, headers=alice
    ).json()
    assert body["total_volume"] == 7000.0

    body = client.get(
        "/reports/summary",
        params={"date_from": "2026-01-10T00:00:00Z", "date_to": "2026-01-15T00:00:00Z"},
        headers=alice,
    ).json()
    assert body["total_volume"] == 4600.0


def test_date_filter_respects_timezone_offsets(client, alice, training_history):
    with_offset = client.get(
        "/reports/summary", params={"date_from": "2026-01-12T17:00:00+07:00"}, headers=alice
    ).json()
    same_in_utc = client.get(
        "/reports/summary", params={"date_from": "2026-01-12T10:00:00Z"}, headers=alice
    ).json()
    assert with_offset["total_volume"] == same_in_utc["total_volume"] == 7000.0


def test_empty_history_does_not_crash(client, alice):
    body = client.get("/reports/summary", headers=alice).json()
    assert body["total_workouts"] == 0
    assert body["total_volume"] == 0.0
    assert body["first_workout_at"] is None
    assert client.get("/reports/exercises", headers=alice).json() == []


def test_per_exercise_stats(client, alice, training_history):
    rows = client.get("/reports/exercises", headers=alice).json()
    by_name = {r["exercise_name"]: r for r in rows}

    assert by_name["Bench Press"]["times_performed"] == 3
    assert by_name["Bench Press"]["max_weight"] == 80.0
    assert by_name["Bench Press"]["total_volume"] == 6300.0


def test_per_exercise_is_sorted_by_volume(client, alice, training_history):
    volumes = [r["total_volume"] for r in client.get("/reports/exercises", headers=alice).json()]
    assert volumes == sorted(volumes, reverse=True)


def test_bodyweight_exercise_has_zero_volume_not_null(client, alice, training_history):
    rows = client.get("/reports/exercises", headers=alice).json()
    plank = next(r for r in rows if r["exercise_name"] == "Plank")
    assert plank["total_volume"] == 0.0
    assert plank["max_weight"] is None
    assert plank["total_sets"] == 3


def test_progress_is_chronological(client, alice, training_history, exercise_ids):
    bench_id = exercise_ids["Bench Press"]
    body = client.get(f"/reports/progress/{bench_id}", headers=alice).json()
    assert [p["weight"] for p in body["points"]] == [60.0, 70.0, 80.0]
    assert body["max_weight"] == 80.0


def test_progress_excludes_pending_workouts(client, alice, training_history, exercise_ids):
    bench_id = exercise_ids["Bench Press"]
    body = client.get(f"/reports/progress/{bench_id}", headers=alice).json()
    assert all(p["weight"] != 999 for p in body["points"])


def test_progress_percentage_change(client, alice, training_history, exercise_ids):
    bench_id = exercise_ids["Bench Press"]
    body = client.get(f"/reports/progress/{bench_id}", headers=alice).json()
    assert body["volume_change_pct"] == 33.3


def test_progress_change_is_null_with_one_data_point(client, alice, training_history, exercise_ids):
    squat_id = exercise_ids["Squat"]
    body = client.get(f"/reports/progress/{squat_id}", headers=alice).json()
    assert len(body["points"]) == 1
    assert body["volume_change_pct"] is None


def test_progress_for_unknown_exercise_returns_404(client, alice):
    assert client.get("/reports/progress/9999", headers=alice).status_code == 404


def test_reports_are_isolated_per_user(client, alice, bob, training_history, exercise_ids):
    body = client.get("/reports/summary", headers=bob).json()
    assert body["total_workouts"] == 0
    assert body["total_volume"] == 0.0

    bench_id = exercise_ids["Bench Press"]
    progress = client.get(f"/reports/progress/{bench_id}", headers=bob).json()
    assert progress["points"] == []
