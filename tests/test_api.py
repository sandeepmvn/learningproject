from fastapi.testclient import TestClient

from app.main import create_app
from app import services


def _auth_headers(client: TestClient, username: str = "tester", password: str = "strongpass123") -> dict[str, str]:
    register_response = client.post("/auth/register", json={"username": username, "password": password})
    assert register_response.status_code == 201

    token_response = client.post("/auth/token", data={"username": username, "password": password})
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_trip_workflow_with_equal_split():
    client = TestClient(create_app("sqlite+pysqlite:///:memory:"))

    with client:
        auth_headers = _auth_headers(client)
        trip_response = client.post(
            "/trips",
            json={
                "name": "Goa Team Trip",
                "description": "Engineering offsite",
                "destination": "Goa",
                "start_date": "2026-05-10",
                "end_date": "2026-05-14",
                "currency": "inr",
            },
            headers=auth_headers,
        )
        assert trip_response.status_code == 201
        trip_id = trip_response.json()["id"]
        assert trip_response.json()["currency"] == "INR"

        alice_response = client.post(
            f"/trips/{trip_id}/participants",
            json={"name": "Alice"},
            headers=auth_headers,
        )
        bob_response = client.post(
            f"/trips/{trip_id}/participants",
            json={"name": "Bob"},
            headers=auth_headers,
        )
        cara_response = client.post(
            f"/trips/{trip_id}/participants",
            json={"name": "Cara"},
            headers=auth_headers,
        )
        assert alice_response.status_code == 201
        assert bob_response.status_code == 201
        assert cara_response.status_code == 201

        alice_id = alice_response.json()["id"]
        bob_id = bob_response.json()["id"]
        cara_id = cara_response.json()["id"]

        dinner_response = client.post(
            f"/trips/{trip_id}/expenses",
            json={
                "title": "Team Dinner",
                "amount": 3000,
                "paid_by_participant_id": alice_id,
                "category": "Food",
                "spent_on": "2026-05-10",
            },
            headers=auth_headers,
        )
        assert dinner_response.status_code == 201
        assert dinner_response.json()["shares"] == [
            {"participant_id": alice_id, "participant_name": "Alice", "amount": 1000.0},
            {"participant_id": bob_id, "participant_name": "Bob", "amount": 1000.0},
            {"participant_id": cara_id, "participant_name": "Cara", "amount": 1000.0},
        ]

        cab_response = client.post(
            f"/trips/{trip_id}/expenses",
            json={
                "title": "Airport Cab",
                "amount": 900,
                "paid_by_participant_id": bob_id,
                "split_participant_ids": [bob_id, cara_id],
            },
            headers=auth_headers,
        )
        assert cab_response.status_code == 201
        assert cab_response.json()["shares"] == [
            {"participant_id": bob_id, "participant_name": "Bob", "amount": 450.0},
            {"participant_id": cara_id, "participant_name": "Cara", "amount": 450.0},
        ]

        detail_response = client.get(f"/trips/{trip_id}", headers=auth_headers)
        assert detail_response.status_code == 200
        assert len(detail_response.json()["participants"]) == 3
        assert len(detail_response.json()["expenses"]) == 2

        summary_response = client.get(f"/trips/{trip_id}/summary", headers=auth_headers)
        assert summary_response.status_code == 200
        summary = summary_response.json()

        assert summary["total_expenses"] == 3900.0
        assert summary["balances"] == [
            {"participant_id": alice_id, "participant_name": "Alice", "paid": 3000.0, "owes": 1000.0, "balance": 2000.0},
            {"participant_id": bob_id, "participant_name": "Bob", "paid": 900.0, "owes": 1450.0, "balance": -550.0},
            {"participant_id": cara_id, "participant_name": "Cara", "paid": 0.0, "owes": 1450.0, "balance": -1450.0},
        ]
        assert summary["settlements"] == [
            {
                "from_participant_id": bob_id,
                "from_participant_name": "Bob",
                "to_participant_id": alice_id,
                "to_participant_name": "Alice",
                "amount": 550.0,
            },
            {
                "from_participant_id": cara_id,
                "from_participant_name": "Cara",
                "to_participant_id": alice_id,
                "to_participant_name": "Alice",
                "amount": 1450.0,
            },
        ]


def test_custom_split_validation():
    client = TestClient(create_app("sqlite+pysqlite:///:memory:"))

    with client:
        auth_headers = _auth_headers(client, username="tester2")
        trip_id = client.post("/trips", json={"name": "Workshop Trip"}, headers=auth_headers).json()["id"]
        alice_id = client.post(
            f"/trips/{trip_id}/participants",
            json={"name": "Alice"},
            headers=auth_headers,
        ).json()["id"]
        bob_id = client.post(
            f"/trips/{trip_id}/participants",
            json={"name": "Bob"},
            headers=auth_headers,
        ).json()["id"]

        response = client.post(
            f"/trips/{trip_id}/expenses",
            json={
                "title": "Supplies",
                "amount": 500,
                "paid_by_participant_id": alice_id,
                "split_mode": "custom",
                "custom_shares": [
                    {"participant_id": alice_id, "amount": 300},
                    {"participant_id": bob_id, "amount": 100},
                ],
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Custom shares must add up to the expense amount"


def test_protected_endpoints_require_authentication():
    client = TestClient(create_app("sqlite+pysqlite:///:memory:"))

    with client:
        response = client.get("/trips")
        assert response.status_code == 401


def test_register_login_and_invalid_login():
    client = TestClient(create_app("sqlite+pysqlite:///:memory:"))

    with client:
        register_response = client.post(
            "/auth/register",
            json={"username": "alice", "password": "supersecure123"},
        )
        assert register_response.status_code == 201
        assert register_response.json()["username"] == "alice"
        assert register_response.json()["is_active"] is True
        assert "hashed_password" not in register_response.json()

        duplicate_response = client.post(
            "/auth/register",
            json={"username": "alice", "password": "supersecure123"},
        )
        assert duplicate_response.status_code == 409

        token_response = client.post(
            "/auth/token",
            data={"username": "alice", "password": "supersecure123"},
        )
        assert token_response.status_code == 200
        assert token_response.json()["token_type"] == "bearer"
        assert token_response.json()["access_token"]

        invalid_login_response = client.post(
            "/auth/token",
            data={"username": "alice", "password": "wrongpass123"},
        )
        assert invalid_login_response.status_code == 401


def test_access_token_expiry_reads_environment_variable(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5")
    assert services.get_access_token_expire_minutes() == 5

    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "invalid")
    assert services.get_access_token_expire_minutes() == services.DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES

    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "0")
    assert services.get_access_token_expire_minutes() == services.DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES

    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
    assert services.get_access_token_expire_minutes() == services.DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
