def test_register_creates_user_and_returns_token(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "jane@example.com", "password": "supersecret", "name": "Jane"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "jane@example.com"
    assert body["access_token"]


def test_register_rejects_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "supersecret", "name": "Dupe"}
    client.post("/api/auth/register", json=payload)

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 409


def test_login_with_correct_credentials_returns_token(client):
    client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "supersecret", "name": "Log In"},
    )

    response = client.post(
        "/api/auth/login", json={"email": "login@example.com", "password": "supersecret"}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_returns_401(client):
    client.post(
        "/api/auth/register",
        json={"email": "wrong@example.com", "password": "supersecret", "name": "Wrong"},
    )

    response = client.post(
        "/api/auth/login", json={"email": "wrong@example.com", "password": "not-it"}
    )

    assert response.status_code == 401


def test_me_requires_valid_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    register = client.post(
        "/api/auth/register",
        json={"email": "me@example.com", "password": "supersecret", "name": "Me"},
    )
    token = register.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
