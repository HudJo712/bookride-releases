## Grafana webhook contact points

- Primary contact point `bookride-webhook` (type `webhook`) bound to alert rule `Bookride API Down`. Default URL points to the built-in listener so it can log and forward to Discord.
- Secondary contact point `bookride-webhook-listener` (type `webhook`) bound to the same rule for debugging/inspection (webhook.site or the local listener).
- Target URLs come from environment:
  - `GRAFANA_WEBHOOK_URL`: defaults to `http://webhook-listener:8000/alerts` so the listener can fan out to Discord; set to webhook.site if you just want to inspect raw payloads.
  - `GRAFANA_WEBHOOK_LISTENER_URL`: debugging URL (default `http://webhook-listener:8000/alerts`; set to webhook.site UUID if you prefer).
  - `DISCORD_WEBHOOK_URL`: when set, the listener forwards alerts to this Discord webhook using a friendly message with `ALERT_CONTACT_NAME`.

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
