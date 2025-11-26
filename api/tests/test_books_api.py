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
    from api.auth import create_access_token, hash_password
    from api.main import app, get_session
    from api.models import User
except ImportError:
    import main  # type: ignore
    from auth import create_access_token, hash_password  # type: ignore
    from main import app, get_session  # type: ignore
    from models import User  # type: ignore


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
    yield engine
    app.dependency_overrides.pop(get_session, None)
    if original_engine is not None:
        main.engine = original_engine
    else:
        delattr(main, "engine")
    engine.dispose()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def user_token(setup_database):
    engine = setup_database or getattr(main, "engine", None)
    assert engine is not None
    with Session(engine) as session:
        user = User(
            username="tester",
            email="tester@example.com",
            password_hash=hash_password("Secret123"),
            role="user",
            scopes="books:write books:read",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token(user_id=user.id, email=user.email, role=user.role, scopes=user.scopes.split())
    return token


def test_create_book_rejects_unsupported_content_type(client: TestClient, user_token: str):
    response = client.post(
        "/books",
        data="id=1",
        headers={"Content-Type": "text/plain", "Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"


def test_get_book_rejects_unknown_accept_header(client: TestClient, user_token: str):
    book_payload = {"id": 1, "title": "1984", "author": "Orwell", "price": 8.99, "in_stock": True}
    create_response = client.post("/books", json=book_payload, headers={"Authorization": f"Bearer {user_token}"})
    assert create_response.status_code == 201

    response = client.get("/books/1", headers={"Accept": "application/x-custom", "Authorization": f"Bearer {user_token}"})

    assert response.status_code == 406
    assert response.json()["detail"] == "Not Acceptable"


def test_create_book_schema_validation_error(client: TestClient, user_token: str):
    invalid_payload = {"id": 2, "title": "No Author", "price": 5.0, "in_stock": True}

    response = client.post("/books", json=invalid_payload, headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 422
    error = response.json()["detail"]
    assert error["error"] == "schema_validation"
    assert error["message"] == "'author' is a required property"
