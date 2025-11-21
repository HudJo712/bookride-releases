# Book & Ride API (DevOps conversion)

## What changed
- Switched to a `pyproject.toml`-driven, src-based package: code under `api/src/bookandride_api`, tests under `tests/`.
- Docker now installs the package directly from `pyproject.toml` and runs `uvicorn bookandride_api.main:app`.
- Extracted modules for concerns: `database.py` (engine/session/init), `auth.py` (API key verification), `schemas.py` (Pydantic models), `logging_config.py` (basic logger).
- Added helper exports and shims: `myproject` package re-exports `add_numbers`/`compute_total`; main `bookandride_api` exports `app`, `add_numbers`, `compute_total`.
- Hardened rental timestamp validation and protobuf handling; fixed UTC round-tripping and Accept/Content negotiation tests.
- Added basic logging in price/rental flows and pytest caplog coverage.
- Simplified test layout with shared FastAPI/SQLModel fixtures and additional targeted tests (auth, schemas, logging, pricing, rentals, books).

## Quickstart
```bash
python -m pip install -e ".[dev]"
pytest
```

## Running the API locally (Docker)
```bash
docker-compose build api_blue api_green
docker-compose up api_blue
# or api_green
```
Uvicorn entrypoint: `bookandride_api.main:app` on port 8080.

## Logging
- Basic console logger: `bookandride_api.logging_config.logger` (name: `bookandride`).
- App still configures the Elasticsearch handler via `logging_utils.configure_logging`; standalone helpers use the basic logger for lightweight messages.

## Tests of interest
- Pricing logic: `tests/test_pricing.py`, `tests/test_price.py`
- Books API validation: `tests/test_books_api.py`
- Rentals protobuf/Accept handling: `tests/test_rentals_api.py`
- Auth and schema validation: `tests/test_auth.py`, `tests/test_schemas.py`
- Logging behavior: `tests/test_logging.py`
- Simple helpers: `tests/test_core.py`
