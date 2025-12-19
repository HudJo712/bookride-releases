from __future__ import annotations

from bookandride_api.main import calculate_price


def test_price_under_cap():
    assert calculate_price(40) == 10.0
