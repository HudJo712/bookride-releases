# ADR-002: Database Schema

## Status
Accepted

## Context
The Book & Ride API originally stored book and rental data in an in-memory dictionary, which meant volatile state, no cross-instance consistency, and no way to share data with other services. We introduced SQLModel-based persistence so the FastAPI application could rely on PostgreSQL (or SQLite in tests) for durable storage.

## Decision
Persist API entities in three SQL tables that align with the logical models exposed by the service:

```sql
CREATE TABLE books (
    id          INTEGER PRIMARY KEY,
    title       TEXT        NOT NULL,
    author      TEXT        NOT NULL,
    price       NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    in_stock    BOOLEAN     NOT NULL
);

CREATE TABLE partner_rentals (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER     NOT NULL CHECK (user_id > 0),
    bike_id     TEXT        NOT NULL,
    start_time  TIMESTAMPTZ NOT NULL,
    end_time    TIMESTAMPTZ,
    price_eur   NUMERIC(10,2) NOT NULL CHECK (price_eur >= 0)
);

CREATE TABLE rentals (
    id            SERIAL       PRIMARY KEY,
    user_name     TEXT         NOT NULL,
    bike_id       TEXT         NOT NULL,
    started_at    TIMESTAMPTZ  NOT NULL,
    stopped_at    TIMESTAMPTZ,
    total_minutes INTEGER,
    price_eur     NUMERIC(10,2),
    CHECK (total_minutes IS NULL OR total_minutes >= 0),
    CHECK (price_eur IS NULL OR price_eur >= 0)
);
```

## Consequences
- **Durability & Scaling** – Requests processed by different API instances share a single source of truth, enabling horizontal scaling and safe restarts.
- **Integration-ready** – Partner-provided rentals can be reconciled with internally generated rentals through shared identifiers (`bike_id`, `user_id`), easing reporting and follow-on services.
- **Testing considerations** – Unit tests now create an in-memory SQLite engine and override the session dependency to keep the test suite fast while exercising the persistence layer.

## Diagram

```
books
 ├─ id (PK)
 ├─ title
 ├─ author
 ├─ price
 └─ in_stock

partner_rentals
 ├─ id (PK)
 ├─ user_id
 ├─ bike_id
 ├─ start_time
 ├─ end_time
 └─ price_eur

rentals
 ├─ id (PK)
 ├─ user_name
 ├─ bike_id
 ├─ started_at
 ├─ stopped_at
 ├─ total_minutes
 └─ price_eur
```

Legend: `PK` denotes primary key. `partner_rentals.user_id` is supplied by an upstream identity provider. `rentals.bike_id` aligns with `partner_rentals.bike_id` when the ride originates from a partner feed or internal session bookkeeping.
