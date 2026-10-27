"""Data loading, querying, and cleaning utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
COMPETITION_SUBDIR = "nfl-big-data-bowl-2027"


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate rows and rows that are entirely empty."""
    return df.drop_duplicates().dropna(how="all").reset_index(drop=True)


def get_combine_tracking_path(custom_path: str | Path | None = None) -> Path:
    """Resolve the path to combine_tracking.csv."""
    if custom_path is not None:
        p = Path(custom_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Custom combine tracking path not found: {custom_path}")

    candidates = [
        RAW_DIR / COMPETITION_SUBDIR / "combine_tracking.csv",
        RAW_DIR / "combine_tracking.csv",
        DATA_DIR / "combine_tracking.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "combine_tracking.csv not found in data/raw. Run `make data` to download."
    )


def get_players_path(custom_path: str | Path | None = None) -> Path | None:
    """Resolve the path to players.csv if it exists."""
    if custom_path is not None:
        p = Path(custom_path)
        return p if p.exists() else None

    candidates = [
        RAW_DIR / COMPETITION_SUBDIR / "players.csv",
        RAW_DIR / "players.csv",
        DATA_DIR / "players.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def load_combine_tracking(
    path: str | Path | None = None,
    draft_year: int | None = None,
    drill_type: str | None = None,
    drill_name: str | None = None,
    nfl_id: int | None = None,
    event_id: str | None = None,
) -> pd.DataFrame:
    """Load and optionally filter combine tracking data."""
    csv_path = get_combine_tracking_path(path)
    df = pd.read_csv(csv_path)

    if draft_year is not None:
        df = df[df["draft_year"] == draft_year]
    if drill_type is not None:
        df = df[df["drill_type"] == drill_type]
    if drill_name is not None:
        df = df[df["drill_name"] == drill_name]
    if nfl_id is not None:
        df = df[df["nfl_id"] == nfl_id]
    if event_id is not None:
        df = df[df["event_id"] == event_id]

    return df.reset_index(drop=True)


def load_players(path: str | Path | None = None) -> pd.DataFrame | None:
    """Load players metadata if available."""
    p_path = get_players_path(path)
    if p_path is None or not p_path.exists():
        return None
    return pd.read_csv(p_path)


def get_event_route(
    df: pd.DataFrame,
    event_id: str,
    entity_type: str | None = None,
) -> pd.DataFrame:
    """Extract ordered tracking frames for a specific event attempt."""
    sub = df[df["event_id"] == event_id]
    if entity_type is not None:
        sub = sub[sub["entity_type"] == entity_type]
    return sub.sort_values(by="time").reset_index(drop=True)
