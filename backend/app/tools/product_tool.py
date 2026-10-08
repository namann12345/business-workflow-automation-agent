"""Product tool — product and inventory data access."""
from __future__ import annotations
import logging
import pandas as pd
from app.tools.csv_tool import read_csv
from app.config import DATA_DIR

logger = logging.getLogger(__name__)


def get_inventory() -> pd.DataFrame:
    """Load inventory from sample data."""
    return read_csv(DATA_DIR / "sample_inventory.csv")


def get_products() -> pd.DataFrame:
    """Load product catalog from sample data."""
    return read_csv(DATA_DIR / "sample_products.csv")


def get_vendor_prices() -> pd.DataFrame:
    """Load vendor price list from sample data."""
    return read_csv(DATA_DIR / "sample_vendors.csv")


def check_restock(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply restock decision logic.
    Expects columns: product_name, current_stock, minimum_stock.
    Returns only rows where current_stock < minimum_stock with reorder quantity.
    """
    required = {"product_name", "current_stock", "minimum_stock"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"Inventory data missing columns: {required - set(df.columns)}")

    df = df.copy()
    df["current_stock"] = pd.to_numeric(df["current_stock"], errors="coerce").fillna(0)
    df["minimum_stock"] = pd.to_numeric(df["minimum_stock"], errors="coerce").fillna(0)
    low = df[df["current_stock"] < df["minimum_stock"]].copy()
    low["reorder_quantity"] = (low["minimum_stock"] - low["current_stock"]).astype(int)
    return low


def validate_price_differences(products: pd.DataFrame, vendors: pd.DataFrame,
                                threshold: float = 10.0) -> pd.DataFrame:
    """
    Match products to vendors by SKU and flag price differences > threshold %.
    Returns a DataFrame of exceptions.
    """
    # Normalize SKU column names
    if "sku" not in products.columns:
        raise ValueError("Products CSV must have a 'sku' column.")
    if "sku" not in vendors.columns:
        raise ValueError("Vendor CSV must have a 'sku' column.")

    merged = products.merge(vendors, on="sku", suffixes=("_internal", "_vendor"))
    merged["internal_price"] = pd.to_numeric(merged["price_internal"], errors="coerce").fillna(0)
    merged["vendor_price"] = pd.to_numeric(merged["price_vendor"], errors="coerce").fillna(0)

    merged["price_diff_pct"] = (
        (merged["internal_price"] - merged["vendor_price"]).abs()
        / merged["internal_price"].replace(0, 1)
        * 100
    )
    exceptions = merged[merged["price_diff_pct"] > threshold].copy()
    return exceptions


def get_product_catalog() -> pd.DataFrame:
    """Load full product catalog (for duplicate detection)."""
    return read_csv(DATA_DIR / "sample_products.csv")
