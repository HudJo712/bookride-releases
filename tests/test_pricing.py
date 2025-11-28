from bookandride_api.main import calculate_price


def test_price_under_cap():
    assert calculate_price(40) == 10.0


def test_price_reaches_cap():
    assert calculate_price(50) == 12.0


def test_price_over_cap():
    assert calculate_price(100) == 12.0
