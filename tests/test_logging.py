from __future__ import annotations

from bookandride_api.core import compute_total
from bookandride_api.logging_config import logger
from bookandride_api.main import calculate_price


def test_basic_logging(caplog):
    caplog.set_level("INFO")

    logger.info("Hello world")

    assert "Hello world" in caplog.text


def test_compute_total_logs_and_returns_sum(caplog):
    caplog.set_level("INFO")

    total = compute_total([1, 2, 3])

    assert total == 6
    assert "3 items" in caplog.text


def test_price_logging(caplog):
    caplog.set_level("INFO")

    result = calculate_price(40)

    assert result == 10.0
    assert "price" in caplog.text.lower()
