from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest

matplotlib.use("Agg")

from databowl.visualization import draw_football_field, plot_route


@pytest.fixture
def sample_tracking_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "draft_year": [2025] * 8,
            "event_id": ["ev_wr_1"] * 8,
            "nfl_id": [58000] * 8,
            "entity_type": ["PLAYER"] * 5 + ["BALL"] * 3,
            "time": [
                "2025-03-01T10:00:00.100",
                "2025-03-01T10:00:00.200",
                "2025-03-01T10:00:00.300",
                "2025-03-01T10:00:00.400",
                "2025-03-01T10:00:00.500",
                "2025-03-01T10:00:00.300",
                "2025-03-01T10:00:00.400",
                "2025-03-01T10:00:00.500",
            ],
            "drill_type": ["SKILL_DRILLS_WR"] * 8,
            "drill_name": ["POST_CORNER_ROUTE_RIGHT"] * 8,
            "attempt": [1] * 8,
            "x": [20.0, 25.0, 30.0, 35.0, 40.0, 22.0, 28.0, 38.0],
            "y": [10.0, 12.0, 15.0, 20.0, 25.0, 11.0, 14.0, 24.0],
            "s": [2.0, 4.0, 6.0, 7.0, 5.0, 8.0, 10.0, 6.0],
            "a": [1.0, 1.5, 0.5, -0.5, -1.0, 0.0, -1.0, -2.0],
            "dis": [0.2, 0.5, 0.6, 0.7, 0.5, 0.8, 1.0, 0.6],
            "dir": [45.0, 50.0, 55.0, 60.0, 65.0, 48.0, 52.0, 58.0],
        }
    )


def test_draw_football_field():
    fig, ax = plt.subplots(figsize=(10, 5))
    draw_football_field(ax, x_min=0, x_max=120, y_min=0, y_max=53.33)
    assert ax.get_xlim() == (0.0, 120.0)
    assert ax.get_ylim() == (0.0, 53.33)
    plt.close(fig)


def test_plot_route_basic(sample_tracking_df: pd.DataFrame):
    fig, ax = plot_route(sample_tracking_df, zoom_to_route=True)
    assert ax is not None
    # Check that route limits are zoomed around the player's points (x in [20, 40])
    xlim = ax.get_xlim()
    assert xlim[0] < 20.0
    assert xlim[1] > 40.0
    plt.close(fig)


def test_plot_route_full_field(sample_tracking_df: pd.DataFrame):
    fig, ax = plot_route(sample_tracking_df, zoom_to_route=False)
    assert ax.get_xlim() == (0.0, 120.0)
    assert ax.get_ylim() == (0.0, 53.33)
    plt.close(fig)


def test_plot_route_save_file(sample_tracking_df: pd.DataFrame, tmp_path: Path):
    out_file = tmp_path / "route.png"
    fig, ax = plot_route(sample_tracking_df, save_path=out_file)
    assert out_file.exists()
    assert out_file.stat().st_size > 0
    plt.close(fig)


def test_plot_route_empty_raises():
    empty_df = pd.DataFrame(columns=["event_id", "time", "x", "y"])
    with pytest.raises(ValueError, match="No tracking data found"):
        plot_route(empty_df)


def test_plot_route_existing_ax(sample_tracking_df: pd.DataFrame):
    fig, custom_ax = plt.subplots()
    ret_fig, ret_ax = plot_route(sample_tracking_df, ax=custom_ax)
    assert ret_ax is custom_ax
    assert ret_fig is fig
    plt.close(fig)
