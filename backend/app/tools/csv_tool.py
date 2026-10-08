"""CSV tool — reads CSV files into pandas DataFrames."""
from __future__ import annotations
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


def read_csv(file_path: str | Path) -> pd.DataFrame:
    """Read a CSV file and return a DataFrame. Raises on error."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    try:
        df = pd.read_csv(path)
        logger.debug("Read CSV %s: %d rows, %d cols", path.name, len(df), len(df.columns))
        return df
    except Exception as exc:
        raise ValueError(f"Failed to read CSV '{path}': {exc}") from exc


def read_csv_from_bytes(content: bytes, filename: str = "upload.csv") -> pd.DataFrame:
    """Read a CSV from raw bytes (uploaded file)."""
    import io
    try:
        return pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise ValueError(f"Failed to parse uploaded CSV '{filename}': {exc}") from exc
