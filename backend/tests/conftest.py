from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from bookandride_api import database
from bookandride_api import main
from bookandride_api.main import app, get_session


@pytest.fixture(autouse=True)
def setup_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    original_engine = database.engine
    database.engine = engine
    main.engine = engine

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_session, None)
        main.engine = original_engine
        database.engine = original_engine
        engine.dispose()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
