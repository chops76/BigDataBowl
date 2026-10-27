"""Data loading and cleaning utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# SAMPLE CODE To test CI
def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate rows and rows that are entirely empty."""
    return df.drop_duplicates().dropna(how="all").reset_index(drop=True)
