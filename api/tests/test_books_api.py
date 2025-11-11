from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from api import main
from api.main import app, get_session


@pytest.fixture(autouse=True)
def setup_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    original_engine = main.engine
    main.engine = engine

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    yield
    app.dependency_overrides.pop(get_session, None)
    main.engine = original_engine
    engine.dispose()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_book_rejects_unsupported_content_type(client: TestClient):
    response = client.post(
        "/books",
        data="id=1",
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"


def test_get_book_rejects_unknown_accept_header(client: TestClient):
    book_payload = {"id": 1, "title": "1984", "author": "Orwell", "price": 8.99, "in_stock": True}
    create_response = client.post("/books", json=book_payload)
    assert create_response.status_code == 201

    response = client.get("/books/1", headers={"Accept": "application/x-custom"})

    assert response.status_code == 406
    assert response.json()["detail"] == "Not Acceptable"


def test_create_book_schema_validation_error(client: TestClient):
    invalid_payload = {"id": 2, "title": "No Author", "price": 5.0, "in_stock": True}

    response = client.post("/books", json=invalid_payload)

    assert response.status_code == 422
    error = response.json()["detail"]
    assert error["error"] == "schema_validation"
    assert error["message"] == "'author' is a required property"
