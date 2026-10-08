"""Order tool — order and shipment data access."""
from __future__ import annotations
import logging
import pandas as pd
from app.tools.csv_tool import read_csv
from app.config import DATA_DIR

logger = logging.getLogger(__name__)

_order_cache: pd.DataFrame | None = None


def _get_orders() -> pd.DataFrame:
    global _order_cache
    if _order_cache is None:
        _order_cache = read_csv(DATA_DIR / "sample_orders.csv")
    return _order_cache


def get_order(order_id: str) -> dict | None:
    """Look up an order by its order_id. Returns None if not found."""
    orders = _get_orders()
    if "order_id" not in orders.columns:
        raise ValueError("Orders data must have an 'order_id' column.")

    match = orders[orders["order_id"].astype(str).str.upper() == order_id.upper()]
    if match.empty:
        return None
    row = match.iloc[0].where(pd.notnull(match.iloc[0]), None).to_dict()
    return row


def get_order_by_email(email: str) -> list[dict]:
    """Look up orders by customer email."""
    orders = _get_orders()
    if "customer_email" not in orders.columns:
        return []
    match = orders[orders["customer_email"].astype(str).str.lower() == email.lower()]
    return match.to_dict(orient="records")


def list_all_orders() -> list[dict]:
    return _get_orders().to_dict(orient="records")
