VALID = {"name": "John Doe", "email": "john@example.com", "age": 30, "password": "pass12345"}


def register(client):
    return client.post("/auth/register", json=VALID)


def login(client):
    return client.post("/auth/login", json={"email": VALID["email"], "password": VALID["password"]})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_hashes_password(client):
    response = register(client)

    assert response.status_code == 201
    assert "password" not in response.json()


def test_login_success_returns_token_pair(client):
    register(client)

    response = login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


def test_login_wrong_password_unauthorized(client):
    register(client)

    response = client.post(
        "/auth/login", json={"email": VALID["email"], "password": "wrongpass1"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_login_unknown_email_unauthorized(client):
    response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "pass12345"})

    assert response.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401

    register(client)
    token = login(client).json()["access_token"]
    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["email"] == VALID["email"]


def test_me_rejects_invalid_token(client):
    response = client.get("/auth/me", headers=auth_headers("not.a.token"))

    assert response.status_code == 401


def test_me_rejects_refresh_token_as_access(client):
    register(client)
    refresh = login(client).json()["refresh_token"]

    response = client.get("/auth/me", headers=auth_headers(refresh))

    assert response.status_code == 401  # неверный тип токена


def test_refresh_issues_new_pair(client):
    register(client)
    pair = login(client).json()

    response = client.post("/auth/refresh", json=pair)

    assert response.status_code == 200
    assert response.json()["access_token"] != pair["access_token"]


def test_logout_revokes_refresh_token(client):
    register(client)
    pair = login(client).json()

    assert client.post("/auth/logout", json=pair).status_code == 204

    # Старый refresh-токен больше не принимается
    response = client.post("/auth/refresh", json=pair)
    assert response.status_code == 401
