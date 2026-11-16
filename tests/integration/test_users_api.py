VALID = {"name": "John Doe", "email": "john@example.com", "age": 30, "password": "pass12345"}
VALID_2 = {"name": "Jane Smith", "email": "jane@example.com", "age": 25, "password": "pass12345"}


def test_create_user(client):
    # Arrange — подготовлены данные VALID; Act
    response = client.post("/users", json=VALID)

    # Assert
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "John Doe"
    assert body["email"] == "john@example.com"
    assert "password" not in body  # пароль не утекает в ответ


def test_list_users_with_search_and_pagination(client):
    client.post("/users", json=VALID)
    client.post("/users", json=VALID_2)

    response = client.get("/users", params={"search": "jane", "limit": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "jane@example.com"


def test_get_user(client):
    user_id = client.post("/users", json=VALID).json()["id"]

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_get_user_not_found(client):
    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_update_user(client):
    user_id = client.post("/users", json=VALID).json()["id"]

    response = client.put(f"/users/{user_id}", json={"age": 31})

    assert response.status_code == 200
    assert response.json()["age"] == 31


def test_delete_user(client):
    user_id = client.post("/users", json=VALID).json()["id"]

    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 204
    assert client.get(f"/users/{user_id}").status_code == 404


# --- Граничные сценарии ---

def test_create_boundary_min_age(client):
    payload = {**VALID, "age": 18, "email": "a@example.com"}
    assert client.post("/users", json=payload).status_code == 201

    payload = {**VALID, "age": 17, "email": "b@example.com"}
    assert client.post("/users", json=payload).status_code == 422


def test_create_boundary_name_length(client):
    assert client.post("/users", json={**VALID, "name": "J"}).status_code == 422
    assert client.post("/users", json={**VALID, "name": "J" * 50}).status_code == 201


def test_create_boundary_password_length(client):
    payload = {**VALID, "email": "c@example.com", "password": "a1b2c3d4"}
    assert client.post("/users", json=payload).status_code == 201

    payload = {**VALID, "email": "d@example.com", "password": "a1b2c3"}
    assert client.post("/users", json=payload).status_code == 422


# --- Ошибочные сценарии ---

def test_create_duplicate_email_conflict(client):
    client.post("/users", json=VALID)

    response = client.post("/users", json={**VALID, "name": "Johnny"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_create_invalid_email_unprocessable(client):
    response = client.post("/users", json={**VALID, "email": "not-an-email"})

    assert response.status_code == 422
    assert "email" in response.json()["error"]["details"]


def test_create_missing_required_field(client):
    response = client.post("/users", json={"name": "John Doe"})

    assert response.status_code == 422


def test_update_not_found(client):
    response = client.put("/users/999", json={"age": 40})

    assert response.status_code == 404


def test_delete_not_found(client):
    assert client.delete("/users/999").status_code == 404


def test_update_email_conflict(client):
    client.post("/users", json=VALID)
    user2 = client.post("/users", json=VALID_2).json()

    response = client.put(f"/users/{user2['id']}", json={"email": "john@example.com"})

    assert response.status_code == 409
