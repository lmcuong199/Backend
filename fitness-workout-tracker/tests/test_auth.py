def test_signup_returns_user_without_password(client):
    response = client.post("/auth/signup", json={"email": "new@example.com", "password": "supersecret1"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body
    assert "password" not in body


def test_duplicate_email_is_rejected(client):
    payload = {"email": "dup@example.com", "password": "supersecret1"}
    client.post("/auth/signup", json=payload)
    assert client.post("/auth/signup", json=payload).status_code == 409


def test_password_is_hashed_in_database(client):
    client.post("/auth/signup", json={"email": "hash@example.com", "password": "supersecret1"})
    from app.database import SessionLocal
    from app.models import User
    db = SessionLocal()
    user = db.query(User).filter(User.email == "hash@example.com").one()
    db.close()
    assert user.hashed_password != "supersecret1"
    assert user.hashed_password.startswith("$2b$")


def test_login_returns_bearer_token(client):
    client.post("/auth/signup", json={"email": "log@example.com", "password": "supersecret1"})
    response = client.post("/auth/login", json={"email": "log@example.com", "password": "supersecret1"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_wrong_password_and_unknown_email_look_identical(client):
    client.post("/auth/signup", json={"email": "same@example.com", "password": "supersecret1"})
    wrong = client.post("/auth/login", json={"email": "same@example.com", "password": "wrongpassword"})
    missing = client.post("/auth/login", json={"email": "nobody@example.com", "password": "supersecret1"})
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json()["detail"] == missing.json()["detail"]


def test_me_requires_a_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_the_logged_in_user(client, alice):
    response = client.get("/auth/me", headers=alice)
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


def test_tampered_token_is_rejected(client, alice):
    token = alice["Authorization"].split()[1]
    forged = token[:-4] + ("aaaa" if not token.endswith("aaaa") else "bbbb")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_expired_token_is_rejected(client, alice, monkeypatch):
    import app.security as security
    from app.models import User
    from app.database import SessionLocal

    db = SessionLocal()
    user_id = db.query(User).filter(User.email == "alice@example.com").one().id
    db.close()

    monkeypatch.setattr(security, "ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    stale = security.create_access_token(user_id)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {stale}"}).status_code == 401


def test_invalid_signup_payloads_are_rejected(client):
    assert client.post("/auth/signup", json={"email": "notanemail", "password": "supersecret1"}).status_code == 422
    assert client.post("/auth/signup", json={"email": "a@b.com", "password": "short"}).status_code == 422
    assert client.post("/auth/signup", json={"email": "a@b.com", "password": "x" * 100}).status_code == 422
