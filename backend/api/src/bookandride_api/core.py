from __future__ import annotations

from .logging_config import logger


def add_numbers(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def compute_total(items: list[int]) -> int:
    """
    Compute the sum of a list of integers while logging the number of items processed.
    """
    logger.info("Computing total for %d items", len(items))
    return sum(items)
