import logging
import os
from typing import Any, Dict

import httpx
from fastapi import FastAPI, Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("webhook-listener")

app = FastAPI(title="Bookride Webhook Listener")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
ALERT_CONTACT_NAME = os.getenv("ALERT_CONTACT_NAME", "Grafana friend")


@app.get("/healthz")
async def healthcheck():
    return {"status": "ok"}


@app.post("/alerts")
async def handle_alert(request: Request):
    """Receive Grafana webhook payloads and log them."""
    content_type = request.headers.get("content-type", "")
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        payload = (await request.body()).decode("utf-8", errors="replace")

    logger.info("Webhook received content_type=%s payload=%s", content_type, payload)

    if DISCORD_WEBHOOK_URL and isinstance(payload, dict):
        await forward_to_discord(payload)

    return {"status": "received"}


async def forward_to_discord(payload: Dict[str, Any]):
    """Transform Grafana webhook JSON into a Discord-friendly message."""
    common_labels = payload.get("commonLabels") or {}
    common_annotations = payload.get("commonAnnotations") or {}
    alertname = common_labels.get("alertname", "Grafana Alert")
    status = payload.get("status", "").upper() or "UNKNOWN"
    summary = common_annotations.get("summary") or "n/a"
    description = common_annotations.get("description") or "n/a"

    message = (
        f"Hey {ALERT_CONTACT_NAME}, Grafana alert \"{alertname}\" is {status}.\n"
        f"Summary: {summary}\n"
        f"Description: {description}"
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(DISCORD_WEBHOOK_URL, json={"content": message})
            logger.info(
                "Forwarded alert to Discord status=%s", resp.status_code
            )
    except Exception as exc:
        logger.error("Failed to forward alert to Discord: %s", exc)
