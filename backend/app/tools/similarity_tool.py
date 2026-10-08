"""Similarity tool — text-based similarity for duplicate product detection."""
from __future__ import annotations
import re
import logging
import pandas as pd
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Lowercase, remove punctuation, collapse spaces."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def string_similarity(a: str, b: str) -> float:
    """Return similarity ratio 0.0–1.0 using SequenceMatcher."""
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def classify_duplicate(similarity: float, same_sku: bool) -> str:
    """Classify duplicate confidence level."""
    if same_sku:
        return "definite"
    if similarity >= 0.90:
        return "definite"
    if similarity >= 0.75:
        return "likely"
    if similarity >= 0.55:
        return "possible"
    return "none"


def find_duplicates(df: pd.DataFrame) -> list[dict]:
    """
    Find duplicate products in a catalog DataFrame.
    Expects columns: sku, product_name (plus any extras).
    Returns a list of duplicate group dicts.
    """
    required = {"sku", "product_name"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"Product catalog missing columns: {required - set(df.columns)}")

    df = df.copy().reset_index(drop=True)
    df["_norm_name"] = df["product_name"].apply(normalize_text)
    df["_norm_sku"] = df["sku"].astype(str).str.upper().str.strip()

    pairs: list[dict] = []
    n = len(df)
    for i in range(n):
        for j in range(i + 1, n):
            row_i = df.iloc[i]
            row_j = df.iloc[j]
            same_sku = row_i["_norm_sku"] == row_j["_norm_sku"]
            sim = string_similarity(row_i["_norm_name"], row_j["_norm_name"])
            level = classify_duplicate(sim, same_sku)
            if level != "none":
                pairs.append({
                    "product_a": row_i["product_name"],
                    "sku_a": row_i["sku"],
                    "product_b": row_j["product_name"],
                    "sku_b": row_j["sku"],
                    "similarity": round(sim, 3),
                    "same_sku": same_sku,
                    "confidence": level,
                })
    return sorted(pairs, key=lambda p: (-["definite","likely","possible"].index(p["confidence"]) if p["confidence"] in ["definite","likely","possible"] else 3, -p["similarity"]))
