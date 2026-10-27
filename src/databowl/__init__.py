"""DataBowl package for NFL Big Data Bowl analytics."""

from __future__ import annotations

from databowl.data import (
    clean,
    get_combine_tracking_path,
    get_event_route,
    load_combine_tracking,
    load_csv,
    load_players,
)
from databowl.viewer import run_viewer
from databowl.visualization import draw_football_field, plot_route

__version__ = "0.1.0"

__all__ = [
    "clean",
    "draw_football_field",
    "get_combine_tracking_path",
    "get_event_route",
    "load_combine_tracking",
    "load_csv",
    "load_players",
    "plot_route",
    "run_viewer",
]
