def test_catalogue_is_seeded_and_public(client):
    response = client.get("/exercises")
    assert response.status_code == 200
    assert len(response.json()) == 22


def test_exercises_are_sorted_by_name(client):
    names = [e["name"] for e in client.get("/exercises").json()]
    assert names == sorted(names)


def test_filter_by_category(client):
    names = {e["name"] for e in client.get("/exercises", params={"category": "cardio"}).json()}
    assert names == {"Running", "Cycling", "Jump Rope", "Rowing Machine"}


def test_filter_by_muscle_group(client):
    results = client.get("/exercises", params={"muscle_group": "chest"}).json()
    assert all(e["muscle_group"] == "chest" for e in results)
    assert len(results) == 3


def test_search_is_case_insensitive(client):
    names = {e["name"] for e in client.get("/exercises", params={"search": "PRESS"}).json()}
    assert "Bench Press" in names and "Leg Press" in names


def test_get_one_exercise(client, exercise_ids):
    squat_id = exercise_ids["Squat"]
    response = client.get(f"/exercises/{squat_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Squat"


def test_unknown_exercise_returns_404(client):
    assert client.get("/exercises/9999").status_code == 404
