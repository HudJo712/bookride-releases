from __future__ import annotations

from fastapi.testclient import TestClient


def _scrape_metric(client: TestClient, metric_name: str) -> float:
    response = client.get("/metrics")
    assert response.status_code == 200
    for line in response.text.splitlines():
        if line.startswith(f"{metric_name} "):
            return float(line.split()[-1])
    raise AssertionError(f"{metric_name} not found in metrics output")


def test_active_rentals_gauge_tracks_start_and_stop(client: TestClient) -> None:
    headers = {"X-API-Key": "dev-key-123"}

    assert _scrape_metric(client, "bookandride_active_rentals") == 0.0

    start_response = client.post("/rentals/start", json={"bike_id": "bike-7"}, headers=headers)
    assert start_response.status_code == 200
    rental_id = start_response.json()["rental_id"]

    assert _scrape_metric(client, "bookandride_active_rentals") == 1.0

    stop_response = client.post("/rentals/stop", json={"rental_id": rental_id}, headers=headers)
    assert stop_response.status_code == 200

    assert _scrape_metric(client, "bookandride_active_rentals") == 0.0


def test_websocket_metrics_streams_active_rentals(client: TestClient) -> None:
    with client.websocket_connect("/ws/metrics") as websocket:
        message = websocket.receive_json()
        assert "active_rentals" in message
        assert isinstance(message["active_rentals"], int)
