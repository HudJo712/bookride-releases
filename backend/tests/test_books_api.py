from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
import uuid


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "Secret123"
    r = client.post("/register", json={"email": email, "password": password})
    assert r.status_code in (200, 201)
    r = client.post("/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_book_rejects_unsupported_content_type(client: TestClient, auth_headers: dict):
    response = client.post(
        "/books",
        content="id=1",
        headers={"Content-Type": "text/plain", **auth_headers},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"


def test_get_book_rejects_unknown_accept_header(client: TestClient, auth_headers: dict):
    book_payload = {"id": 1, "title": "1984", "author": "Orwell", "price": 8.99, "in_stock": True}
    create_response = client.post("/books", json=book_payload, headers=auth_headers)
    assert create_response.status_code == 201

    response = client.get("/books/1", headers={"Accept": "application/x-custom", **auth_headers})

    assert response.status_code == 406
    assert response.json()["detail"] == "Not Acceptable"


def test_create_book_schema_validation_error(client: TestClient, auth_headers: dict):
    invalid_payload = {"id": 2, "title": "No Author", "price": 5.0, "in_stock": True}

    response = client.post("/books", json=invalid_payload, headers=auth_headers)

    assert response.status_code == 422
    error = response.json()["detail"]
    assert error["error"] == "schema_validation"
    assert error["message"] == "'author' is a required property"
