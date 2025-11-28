import logging
from fastapi import FastAPI, Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("webhook-listener")

app = FastAPI(title="Bookride Webhook Listener")


@app.get("/healthz")
async def healthcheck():
    return {"status": "ok"}


@app.post("/alerts")
async def handle_alert(request: Request):
    """Receive Grafana webhook payloads and log them."""
    content_type = request.headers.get("content-type", "")
    try:
        payload = await request.json()
    except Exception:
        payload = (await request.body()).decode("utf-8", errors="replace")

    logger.info("Webhook received content_type=%s payload=%s", content_type, payload)
    return {"status": "received"}
