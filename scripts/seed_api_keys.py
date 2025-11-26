#!/usr/bin/env python
"""Utility to insert or rotate API keys stored in the database."""

from __future__ import annotations

import argparse
import os

import bcrypt
from sqlmodel import Session, select

from api.models import ApiKey, engine, init_db


def upsert_api_key(name: str, raw_key: str, pepper: str) -> None:
    hashed = bcrypt.hashpw((pepper + raw_key).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with Session(engine) as session:
        record = session.exec(select(ApiKey).where(ApiKey.name == name)).first()
        if record:
            record.key_hash = hashed
            record.is_active = True
        else:
            record = ApiKey(name=name, key_hash=hashed, is_active=True)
        session.add(record)
        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or rotate API keys stored in the database.")
    parser.add_argument("--name", required=True, help="Identifier for the API key owner (e.g. service-a)")
    parser.add_argument("--key", required=True, help="Plaintext API key to store (will be hashed with pepper)")
    parser.add_argument(
        "--pepper",
        default=os.getenv("API_KEY_PEPPER", ""),
        help="Additional shared secret concatenated before hashing (defaults to API_KEY_PEPPER env).",
    )
    args = parser.parse_args()

    init_db()
    upsert_api_key(args.name, args.key, args.pepper)
    print(f"Stored API key for '{args.name}'. Distribute the plaintext secret out-of-band.")


if __name__ == "__main__":
    main()
