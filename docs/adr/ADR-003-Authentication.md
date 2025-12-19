# ADR-003: Authentication Approach

## Context
The API exposes both public book endpoints and state-changing rental endpoints. We need lightweight authentication that works in local development, avoids external dependencies, and fits the small partner ecosystem. Full OAuth or JWT-based identity would add operational burden without additional security guarantees in this environment.

## Decision
Use static API keys supplied via the `X-API-Key` header. Keys live in configuration (`API_KEYS` mapping in `api/main.py`) so they can be rotated via environment variables or secrets management later. Only endpoints that mutate user-specific rental state (`/rentals/start`, `/rentals/stop`) require the header; read-only operations remain unauthenticated.


