# ADR-001: Architecture Choice

## Context
Book & Ride delivers a unified API for book catalog management, partner rental ingestion, and live rental lifecycle. The workload is tightly coupled: every endpoint uses the same validation stack, authentication (API keys), and persistence layer. The platform must be easy to run locally via Docker Compose, serve traffic behind NGINX, and expose metrics to Prometheus.

## Decision
Adopt a modular monolith packaged as a single FastAPI service. NGINX frontends HTTP traffic, while PostgreSQL backs persistence. Supporting services (Postgres, NGINX, Prometheus) are infrastructure components, not separate business domains, so they stay outside the monolith boundary. The FastAPI container scales horizontally if needed without introducing cross-service RPC, schema duplication, or eventual consistency concerns.

