from __future__ import annotations

import os
from typing import Any, Iterator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookandride.db")
CONNECT_ARGS: dict[str, Any] = {}
if DATABASE_URL.startswith("sqlite"):
    CONNECT_ARGS["check_same_thread"] = False

engine = create_engine(DATABASE_URL, echo=False, connect_args=CONNECT_ARGS, pool_pre_ping=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
