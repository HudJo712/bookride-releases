#!/usr/bin/env python
"""Seed or rotate application users for JWT authentication."""

from __future__ import annotations

import argparse

from sqlmodel import Session, select

from api.auth import hash_password
from api.models import User, engine, init_db


def upsert_user(username: str, password: str, scopes: str) -> None:
    hashed = hash_password(password)
    with Session(engine) as session:
        record = session.exec(select(User).where(User.username == username)).first()
        if record:
            record.password_hash = hashed
            record.scopes = scopes
        else:
            record = User(username=username, password_hash=hashed, scopes=scopes)
        session.add(record)
        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an application user.")
    parser.add_argument("--username", required=True, help="Unique username for the user")
    parser.add_argument("--password", required=True, help="Plaintext password (hashed before storage)")
    parser.add_argument(
        "--scopes",
        default="",
        help="Space-delimited scopes to embed in tokens (e.g. 'books:write rentals:write')",
    )
    args = parser.parse_args()

    init_db()
    upsert_user(args.username, args.password, args.scopes.strip())
    print(f"Stored user '{args.username}' with scopes: {args.scopes.strip() or '(none)'}")


if __name__ == "__main__":
    main()
