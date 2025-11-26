<<<<<<< HEAD
from api.main import calculate_price
=======
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from api.main import calculate_price
except ImportError:
    from main import calculate_price  # type: ignore
>>>>>>> temp-repo-b-branch


def test_price_under_cap():
    assert calculate_price(40) == 10.0


def test_price_at_cap():
    assert calculate_price(50) == 12.0


def test_price_over_cap():
    assert calculate_price(100) == 12.0
