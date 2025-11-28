## Grafana webhook contact point

- Contact point provisioned as `bookride-webhook` (type `webhook`) and bound to alert rule `Bookride API Down`.
- Target URL comes from `GRAFANA_WEBHOOK_URL` (default `http://webhook-listener:8000/alerts`), so set this in `.env` if you prefer webhook.site.

### Option A: webhook.site
1. Generate a URL at https://webhook.site and set `GRAFANA_WEBHOOK_URL=https://webhook.site/<uuid>` in `.env`.
2. `docker compose up -d grafana prometheus` (or `docker compose up -d` for everything).
3. Trigger an alert (e.g., stop the API containers) and watch the request at webhook.site.

### Option B: built-in FastAPI listener
1. `docker compose up -d webhook-listener grafana prometheus`.
2. Verify listener: `curl http://localhost:8000/healthz` → `{"status":"ok"}`.
3. When the alert fires, see payloads via `docker compose logs -f webhook-listener`.

### Grafana UI quick checks
- Alert rules: `http://localhost:3000/alerting/list` (rule: Bookride API Down).
- Contact points: `http://localhost:3000/alerting/notifications` (contact: bookride-webhook).
