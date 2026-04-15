from fastapi.testclient import TestClient

from app.main import create_app


def test_trip_workflow_with_equal_split():
    client = TestClient(create_app("sqlite+pysqlite:///:memory:"))

    with client:
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
        )
        assert trip_response.status_code == 201
        trip_id = trip_response.json()["id"]
        assert trip_response.json()["currency"] == "INR"

        alice_response = client.post(f"/trips/{trip_id}/participants", json={"name": "Alice"})
        bob_response = client.post(f"/trips/{trip_id}/participants", json={"name": "Bob"})
        cara_response = client.post(f"/trips/{trip_id}/participants", json={"name": "Cara"})
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
        )
        assert cab_response.status_code == 201
        assert cab_response.json()["shares"] == [
            {"participant_id": bob_id, "participant_name": "Bob", "amount": 450.0},
            {"participant_id": cara_id, "participant_name": "Cara", "amount": 450.0},
        ]

        detail_response = client.get(f"/trips/{trip_id}")
        assert detail_response.status_code == 200
        assert len(detail_response.json()["participants"]) == 3
        assert len(detail_response.json()["expenses"]) == 2

        summary_response = client.get(f"/trips/{trip_id}/summary")
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
        trip_id = client.post("/trips", json={"name": "Workshop Trip"}).json()["id"]
        alice_id = client.post(f"/trips/{trip_id}/participants", json={"name": "Alice"}).json()["id"]
        bob_id = client.post(f"/trips/{trip_id}/participants", json={"name": "Bob"}).json()["id"]

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
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Custom shares must add up to the expense amount"
