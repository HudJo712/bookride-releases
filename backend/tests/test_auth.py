from __future__ import annotations

from fastapi.testclient import TestClient


def test_start_rental_rejects_invalid_api_key(client: TestClient) -> None:
    response = client.post("/rentals/start", json={"bike_id": "bike-1"}, headers={"X-API-Key": "bad-key"})

    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]
