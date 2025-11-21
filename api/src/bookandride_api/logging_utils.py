from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

import requests


EXTRA_FIELD_WHITELIST: Iterable[str] = (
    "path",
    "method",
    "status_code",
    "response_time_ms",
    "user_id",
    "action",
    "bike_id",
    "rental_id",
    "duration_min",
    "price_eur",
)


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class ElasticsearchHandler(logging.Handler):
    """
    Lightweight logging handler that ships JSON logs directly to Elasticsearch.
    """

    def __init__(
        self,
        endpoint: str,
        index: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 2.0,
        verify_ssl: bool = False,
    ) -> None:
        super().__init__()
        self.endpoint = endpoint.rstrip("/")
        self.index = index.strip("/")
        self.auth = (username, password) if username and password else None
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self._last_failure_logged_at = 0.0

    def emit(self, record: logging.LogRecord) -> None:
        body = self._build_payload(record)
        url = f"{self.endpoint}/{self.index}/_doc"
        try:
            response = self.session.post(
                url,
                json=body,
                auth=self.auth,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            self._report_failure(f"Failed to ship log to Elasticsearch: {exc}")
        except Exception as exc:  # pragma: no cover - defensive
            self._report_failure(f"Unexpected logging failure: {exc}")

    def _build_payload(self, record: logging.LogRecord) -> Dict[str, Any]:
        document: Dict[str, Any] = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "service": os.getenv("SERVICE_NAME", "bookride-api"),
            "env": os.getenv("APP_ENV", "dev"),
        }
        for field in EXTRA_FIELD_WHITELIST:
            value = getattr(record, field, None)
            if value is not None:
                document[field] = value
        if record.exc_info:
            document["exception"] = record.exc_info[1].__class__.__name__
        return document

    def _report_failure(self, message: str) -> None:
        now = time.monotonic()
        # Rate-limit stderr noise so failures don't spam every request.
        if now - self._last_failure_logged_at >= 30:
            sys.stderr.write(f"[bookride][logging] {message}\n")
            self._last_failure_logged_at = now


def configure_logging() -> logging.Logger:
    """
    Configure the root Book&Ride logger with stream + Elasticsearch handlers.
    Safe to call multiple times (idempotent).
    """

    logger = logging.getLogger("bookride")
    if getattr(logger, "_bookride_configured", False):
        return logger

    log_level = os.getenv("BOOKRIDE_LOG_LEVEL", "INFO").upper()
    logger.setLevel(log_level)

    endpoint = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    index = os.getenv("ELASTICSEARCH_LOG_INDEX", "logs-demo")
    username = os.getenv("ELASTIC_USERNAME")
    password = os.getenv("ELASTIC_PASSWORD")
    timeout = float(os.getenv("ELASTICSEARCH_TIMEOUT", "2"))
    verify_ssl = _bool_env("ELASTICSEARCH_SSL_VERIFY", False)

    es_handler = ElasticsearchHandler(
        endpoint=endpoint,
        index=index,
        username=username,
        password=password,
        timeout=timeout,
        verify_ssl=verify_ssl,
    )
    logger.addHandler(es_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(console_handler)

    logger._bookride_configured = True  # type: ignore[attr-defined]
    return logger


def log_user_action(logger: logging.Logger, action: str, user_id: str, **fields: Any) -> None:
    payload = {"action": action, "user_id": user_id}
    payload.update(fields)
    logger.info("user action", extra=payload)
