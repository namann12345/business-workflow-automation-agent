"""Calculator tool — deterministic business rule calculations."""
from __future__ import annotations


def reorder_quantity(current_stock: float, minimum_stock: float) -> float:
    """Suggested reorder = minimum_stock - current_stock (if below threshold)."""
    return max(0.0, minimum_stock - current_stock)


def price_diff_percent(internal_price: float, vendor_price: float) -> float:
    """Percentage difference between internal and vendor price."""
    if internal_price == 0:
        return 100.0
    return abs(internal_price - vendor_price) / internal_price * 100.0


def is_price_exception(diff_percent: float, threshold: float = 10.0) -> bool:
    return diff_percent > threshold


def success_rate(total: int, successes: int) -> float:
    if total == 0:
        return 0.0
    return successes / total * 100.0


def failure_rate(total: int, failures: int) -> float:
    if total == 0:
        return 0.0
    return failures / total * 100.0


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
