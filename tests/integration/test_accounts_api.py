VALID = {"name": "John Doe", "email": "john@example.com", "age": 30, "password": "pass12345"}
VALID_2 = {"name": "Jane Smith", "email": "jane@example.com", "age": 25, "password": "pass12345"}


def setup_two_accounts(client, balance=100):
    u1 = client.post("/users", json=VALID).json()
    u2 = client.post("/users", json=VALID_2).json()
    client.post("/accounts", json={"user_id": u1["id"], "balance": balance})
    client.post("/accounts", json={"user_id": u2["id"], "balance": 0})
    return u1["id"], u2["id"]


def test_transfer_success(client):
    src, dst = setup_two_accounts(client, balance=100)

    response = client.post(
        "/accounts/transfer", json={"from_user_id": src, "to_user_id": dst, "amount": 40}
    )

    assert response.status_code == 204
    assert client.get(f"/accounts/{src}").json()["balance"] == 60
    assert client.get(f"/accounts/{dst}").json()["balance"] == 40


def test_transfer_insufficient_funds(client):
    src, dst = setup_two_accounts(client, balance=10)

    response = client.post(
        "/accounts/transfer", json={"from_user_id": src, "to_user_id": dst, "amount": 50}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "insufficient_funds"
    # Деньги не списались
    assert client.get(f"/accounts/{src}").json()["balance"] == 10
    assert client.get(f"/accounts/{dst}").json()["balance"] == 0


def test_transfer_account_not_found(client):
    src, _ = setup_two_accounts(client)

    response = client.post(
        "/accounts/transfer", json={"from_user_id": src, "to_user_id": 999, "amount": 10}
    )

    assert response.status_code == 404


def test_transfer_to_self_rejected(client):
    src, _ = setup_two_accounts(client)

    response = client.post(
        "/accounts/transfer", json={"from_user_id": src, "to_user_id": src, "amount": 10}
    )

    assert response.status_code == 422


def test_transfer_negative_amount_rejected(client):
    src, dst = setup_two_accounts(client)

    response = client.post(
        "/accounts/transfer", json={"from_user_id": src, "to_user_id": dst, "amount": -5}
    )

    assert response.status_code == 422


def test_failed_transfer_rolls_back(client):
    """При ошибке списания зачисление не происходит (атомарность)."""
    src, dst = setup_two_accounts(client, balance=10)

    client.post("/accounts/transfer", json={"from_user_id": src, "to_user_id": dst, "amount": 999})

    assert client.get(f"/accounts/{src}").json()["balance"] == 10
    assert client.get(f"/accounts/{dst}").json()["balance"] == 0
