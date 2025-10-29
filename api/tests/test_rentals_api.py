from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import STORE, app
from api.rental_pb2 import PartnerRental as PbPartnerRental


def test_create_rental_accepts_protobuf() -> None:
    client = TestClient(app)
    STORE["rentals"].clear()

    message = PbPartnerRental(
        id=1,
        user_id=42,
        bike_id="bike-7",
        start_time="2024-04-01T12:00:00Z",
        price_eur=3.5,
    )
    payload = message.SerializeToString()

    response = client.post(
        "/rentals",
        data=payload,
        headers={
            "Content-Type": "application/x-protobuf",
            "Accept": "application/x-protobuf",
        },
    )

    assert response.status_code == 200
    roundtrip = PbPartnerRental()
    roundtrip.ParseFromString(response.content)

    assert roundtrip.id == 1
    assert roundtrip.user_id == 42
    assert roundtrip.bike_id == "bike-7"
    assert roundtrip.start_time == "2024-04-01T12:00:00Z"
    assert roundtrip.end_time == ""
    assert roundtrip.price_eur == 3.5


def test_get_rental_respects_protobuf_accept() -> None:
    client = TestClient(app)
    STORE["rentals"].clear()
    STORE["rentals"][5] = {
        "id": 5,
        "user_id": 99,
        "bike_id": "bike-15",
        "start_time": "2024-05-02T08:30:00Z",
        "end_time": None,
        "price_eur": 7.0,
    }

    response = client.get(
        "/rentals/5",
        headers={"Accept": "application/x-protobuf"},
    )

    assert response.status_code == 200
    rental_pb = PbPartnerRental()
    rental_pb.ParseFromString(response.content)

    assert rental_pb.id == 5
    assert rental_pb.user_id == 99
    assert rental_pb.bike_id == "bike-15"
    assert rental_pb.start_time == "2024-05-02T08:30:00Z"
    assert rental_pb.end_time == ""
    assert rental_pb.price_eur == 7.0
