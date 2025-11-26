from __future__ import annotations

<<<<<<< HEAD
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel
=======
import os
from datetime import datetime
from typing import Iterator, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Session, SQLModel, create_engine


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/bookandride")
CONNECT_ARGS: dict[str, object] = {}
if DATABASE_URL.startswith("sqlite"):
    CONNECT_ARGS["check_same_thread"] = False

engine = create_engine(DATABASE_URL, echo=False, connect_args=CONNECT_ARGS, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
>>>>>>> temp-repo-b-branch


class BookRecord(SQLModel, table=True):
    __tablename__ = "books"

    id: int = Field(primary_key=True)
    title: str
    author: str
    price: float
    in_stock: bool


class PartnerRentalRecord(SQLModel, table=True):
    __tablename__ = "partner_rentals"

    id: int = Field(primary_key=True)
    user_id: int
    bike_id: str
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    end_time: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    price_eur: float


class RentalRecord(SQLModel, table=True):
    __tablename__ = "rentals"

    id: Optional[int] = Field(default=None, primary_key=True)
    user: str
    bike_id: str
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    stopped_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    total_minutes: Optional[int] = None
    price_eur: Optional[float] = None
<<<<<<< HEAD
=======


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    key_hash: str
    is_active: bool = True


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    scopes: str = Field(default="")
    role: str = Field(default="user")
>>>>>>> temp-repo-b-branch
