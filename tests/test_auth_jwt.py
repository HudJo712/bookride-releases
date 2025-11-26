from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from api import main
    from api.main import app, get_session
except ImportError:
    import main  # type: ignore
    from main import app, get_session  # type: ignore


@pytest.fixture(autouse=True)
def setup_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    original_engine = getattr(main, "engine", None)
    main.engine = engine

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    yield
    app.dependency_overrides.pop(get_session, None)
    if original_engine is not None:
        main.engine = original_engine
    else:
        delattr(main, "engine")
    engine.dispose()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_register_login_and_access_books(client: TestClient):
    # register
    r = client.post("/register", json={"email": "bob@example.com", "password": "Secret123"})
    assert r.status_code in (200, 201)

    # login
    r = client.post("/login", json={"email": "bob@example.com", "password": "Secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token

    # access protected endpoint without token -> 401
    r = client.get("/books")
    assert r.status_code == 401

    # access with token -> 200
    r = client.get("/books", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
