from __future__ import annotations

<<<<<<< HEAD:api/tests/test_rentals_api.py
<<<<<<< HEAD
=======
from datetime import datetime, timezone

>>>>>>> origin/green:tests/test_rentals_api.py
from fastapi.testclient import TestClient

from bookandride_api.rental_pb2 import PartnerRental as PbPartnerRental


<<<<<<< HEAD:api/tests/test_rentals_api.py
def test_create_rental_accepts_protobuf() -> None:
    client = TestClient(app)
    STORE["rentals"].clear()

=======
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from api.auth import create_access_token
    from api.main import app, get_session
    from api.models import PartnerRentalRecord
    from api.rental_pb2 import PartnerRental as PbPartnerRental
except ImportError:
    from auth import create_access_token  # type: ignore
    from main import app, get_session  # type: ignore
    from models import PartnerRentalRecord  # type: ignore
    from rental_pb2 import PartnerRental as PbPartnerRental  # type: ignore


@pytest.fixture(autouse=True)
def setup_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    try:
        import api.main as main_module  # type: ignore
    except ImportError:
        import main as main_module  # type: ignore
    original_engine = getattr(main_module, "engine", None)
    main_module.engine = engine

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    yield engine
    app.dependency_overrides.pop(get_session, None)
    if original_engine is not None:
        main_module.engine = original_engine
    else:
        delattr(main_module, "engine")
    engine.dispose()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def mint_partner_token():
    return create_access_token(user_id=1, email="partner@example.com", role="partner", scopes=["partner.rentals"])


def test_create_rental_accepts_protobuf(client: TestClient) -> None:
    token = mint_partner_token()
>>>>>>> temp-repo-b-branch
=======
def test_create_rental_accepts_protobuf(client: TestClient) -> None:
>>>>>>> origin/green:tests/test_rentals_api.py
    message = PbPartnerRental(
        id=1,
        user_id=42,
        bike_id="bike-7",
        start_time="2024-04-01T12:00:00Z",
        price_eur=3.5,
    )

    response = client.post(
        "/rentals",
        content=message.SerializeToString(),
        headers={
            "Content-Type": "application/x-protobuf",
            "Accept": "application/x-protobuf",
<<<<<<< HEAD
=======
            "Authorization": f"Bearer {token}",
>>>>>>> temp-repo-b-branch
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


<<<<<<< HEAD:api/tests/test_rentals_api.py
<<<<<<< HEAD
def test_get_rental_respects_protobuf_accept() -> None:
    client = TestClient(app)
    STORE["rentals"].clear()
    STORE["rentals"][5] = {
=======
def test_get_rental_respects_protobuf_accept(client: TestClient) -> None:
    payload = {
>>>>>>> origin/green:tests/test_rentals_api.py
        "id": 5,
        "user_id": 99,
        "bike_id": "bike-15",
        "start_time": "2024-05-02T08:30:00Z",
        "end_time": None,
        "price_eur": 7.0,
    }
    create_response = client.post("/rentals", json=payload)
    assert create_response.status_code == 200

    response = client.get(
        "/rentals/5",
        headers={"Accept": "application/x-protobuf"},
=======
def test_get_rental_respects_protobuf_accept(client: TestClient, setup_database) -> None:
    token = mint_partner_token()
    engine = setup_database
    with Session(engine) as session:
        record = PartnerRentalRecord(
            id=5,
            user_id=99,
            bike_id="bike-15",
            start_time=datetime(2024, 5, 2, 8, 30, tzinfo=timezone.utc),
            end_time=None,
            price_eur=7.0,
        )
        session.add(record)
        session.commit()

    response = client.get(
        "/rentals/5",
        headers={
            "Accept": "application/x-protobuf",
            "Authorization": f"Bearer {token}",
        },
>>>>>>> temp-repo-b-branch
    )

    assert response.status_code == 200
    rental_pb = PbPartnerRental()
    rental_pb.ParseFromString(response.content)

    assert rental_pb.id == 5
    assert rental_pb.user_id == 99
    assert rental_pb.bike_id == "bike-15"
    parsed_start = datetime.fromisoformat(rental_pb.start_time.replace("Z", "+00:00"))
    expected_start = datetime(2024, 5, 2, 8, 30, 0, tzinfo=timezone.utc)
    assert parsed_start == expected_start
    assert rental_pb.end_time == ""
    assert rental_pb.price_eur == 7.0
