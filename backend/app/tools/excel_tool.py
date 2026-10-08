"""Excel tool — reads XLSX/XLS files into DataFrames."""
from __future__ import annotations
import io
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


def read_excel(file_path: str | Path, sheet_name: str | int = 0) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
        logger.debug("Read Excel %s: %d rows", path.name, len(df))
        return df
    except Exception as exc:
        raise ValueError(f"Failed to read Excel '{path}': {exc}") from exc


def read_excel_from_bytes(content: bytes, filename: str = "upload.xlsx") -> pd.DataFrame:
    try:
        return pd.read_excel(io.BytesIO(content))
    except Exception as exc:
        raise ValueError(f"Failed to parse uploaded Excel '{filename}': {exc}") from exc
