from __future__ import annotations

import os
from typing import Any, Iterator

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine, select

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookandride.db")
CONNECT_ARGS: dict[str, Any] = {}
if DATABASE_URL.startswith("sqlite"):
    CONNECT_ARGS["check_same_thread"] = False

engine = create_engine(DATABASE_URL, echo=False, connect_args=CONNECT_ARGS, pool_pre_ping=True)


def init_db() -> None:
    _ensure_database_exists()
    SQLModel.metadata.create_all(engine)
    _ensure_rental_user_id_column()
    _backfill_rental_user_ids()
    _ensure_user_balance_column()
    _ensure_book_loans_columns()
    _seed_bikes()
    _seed_books()


def _ensure_database_exists() -> None:
    url = make_url(DATABASE_URL)
    if url.get_backend_name() not in {"postgresql", "postgresql+psycopg2"}:
        return
    database_name = url.database
    if not database_name:
        return
    admin_url = url.set(database="postgres")
    try:
        admin_engine = create_engine(admin_url, echo=False, connect_args=CONNECT_ARGS, pool_pre_ping=True)
        with admin_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(
                text(f'CREATE DATABASE "{database_name}"')
            )
    except OperationalError:
        # Database might already exist or server might be unavailable.
        pass
    except Exception as exc:
        if "already exists" not in str(exc).lower():
            raise
    finally:
        try:
            admin_engine.dispose()
        except Exception:
            pass


def _ensure_rental_user_id_column() -> None:
    inspector = inspect(engine)
    if "rentals" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("rentals")}
    if "user_id" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE rentals ADD COLUMN user_id INTEGER"))


def _backfill_rental_user_ids() -> None:
    inspector = inspect(engine)
    if "rentals" not in inspector.get_table_names() or "users" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("rentals")}
    if "user_id" not in columns or "user" not in columns:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE rentals
                SET user_id = (
                    SELECT users.id FROM users WHERE users.email = rentals.user
                )
                WHERE user_id IS NULL
                  AND user IS NOT NULL
                  AND EXISTS (
                      SELECT 1 FROM users WHERE users.email = rentals.user
                  )
                """
            )
        )


def _ensure_user_balance_column() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "balance_due" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN balance_due REAL DEFAULT 0"))


def _ensure_book_loans_columns() -> None:
    inspector = inspect(engine)
    if "book_loans" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("book_loans")}
    statements: list[str] = []
    if "due_at" not in columns:
        statements.append("ALTER TABLE book_loans ADD COLUMN due_at TIMESTAMP")
    if "upfront_fee_eur" not in columns:
        statements.append("ALTER TABLE book_loans ADD COLUMN upfront_fee_eur REAL")
    if "fine_eur" not in columns:
        statements.append("ALTER TABLE book_loans ADD COLUMN fine_eur REAL")
    if "fine_applied" not in columns:
        statements.append("ALTER TABLE book_loans ADD COLUMN fine_applied INTEGER DEFAULT 0")
    if not statements:
        return
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def _seed_bikes() -> None:
    from .models import BikeRecord

    with Session(engine) as session:
        existing = session.exec(select(BikeRecord).limit(1)).first()
        if existing:
            return
        bikes = [
            BikeRecord(
                id="bike-101",
                model="City Sprint",
                color="Sunset Orange",
                year=2023,
                rate_per_minute=0.25,
                price_cap_eur=12.0,
                is_active=True,
            ),
            BikeRecord(
                id="bike-204",
                model="Harbor Cruiser",
                color="Seafoam Green",
                year=2022,
                rate_per_minute=0.3,
                price_cap_eur=12.0,
                is_active=True,
            ),
            BikeRecord(
                id="bike-305",
                model="Night Shift",
                color="Midnight Blue",
                year=2024,
                rate_per_minute=0.35,
                price_cap_eur=12.0,
                is_active=True,
            ),
        ]
        session.add_all(bikes)
        session.commit()


def _seed_books() -> None:
    from .models import BookRecord

    with Session(engine) as session:
        books = [
            BookRecord(
                id=101,
                title="City Streets & Stories",
                author="Mara Linton",
                price=5.0,
                in_stock=True,
            ),
            BookRecord(
                id=204,
                title="Harbor Mornings",
                author="Elias Ford",
                price=5.0,
                in_stock=True,
            ),
            BookRecord(
                id=305,
                title="Night Shift Notes",
                author="Priya Shah",
                price=5.0,
                in_stock=True,
            ),
        ]
        for book in books:
            existing = session.get(BookRecord, book.id)
            if existing:
                existing.title = book.title
                existing.author = book.author
                existing.price = book.price
                if not existing.in_stock:
                    existing.in_stock = True
                session.add(existing)
            else:
                session.add(book)
        session.commit()


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
