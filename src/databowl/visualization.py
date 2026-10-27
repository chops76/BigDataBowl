"""Football field and route visualization utilities."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath

# Pointed oval football marker for matplotlib plots
_FOOTBALL_VERTS = [
    (-1.4, 0.0),
    (-0.6, 0.75),
    (0.6, 0.75),
    (1.4, 0.0),
    (0.6, -0.75),
    (-0.6, -0.75),
    (-1.4, 0.0),
]
_FOOTBALL_CODES = [
    MplPath.MOVETO,
    MplPath.CURVE4,
    MplPath.CURVE4,
    MplPath.CURVE4,
    MplPath.CURVE4,
    MplPath.CURVE4,
    MplPath.CLOSEPOLY,
]
FOOTBALL_MARKER = MplPath(_FOOTBALL_VERTS, _FOOTBALL_CODES)


def draw_football_field(
    ax: plt.Axes,
    x_min: float = 0.0,
    x_max: float = 120.0,
    y_min: float = 0.0,
    y_max: float = 53.33,
    show_yard_numbers: bool = True,
    show_hashmarks: bool = True,
    field_color: str = "#1d532b",
    stripe_color: str = "#246132",
    endzone_color: str = "#143d22",
) -> plt.Axes:
    """Draw a green American football field with NFL markings.

    Field coordinates:
    - x: 0 to 120 (0-10 left endzone, 10-110 playing field, 110-120 right endzone).
    - y: 0 to 53.33 (sideline to sideline, 53 1/3 yards).
    """
    ax.set_facecolor(field_color)

    # 5-yard lawn mowing stripes
    stripe_start = int(np.floor(x_min / 5.0) * 5)
    stripe_end = int(np.ceil(x_max / 5.0) * 5)
    for x in range(stripe_start, stripe_end, 5):
        if (x // 5) % 2 == 1:
            ax.axvspan(x, x + 5, color=stripe_color, zorder=1)

    # End zones (0-10 and 110-120)
    if x_min < 10:
        ax.axvspan(0, 10, color=endzone_color, zorder=2)
    if x_max > 110:
        ax.axvspan(110, 120, color=endzone_color, zorder=2)

    # Goal lines and 5/10-yard lines
    line_start = max(10, int(np.floor(x_min / 5.0) * 5))
    line_end = min(110, int(np.ceil(x_max / 5.0) * 5))
    for x in range(line_start, line_end + 1, 5):
        if x in (10, 110):
            # Bold goal lines
            ax.axvline(x, color="white", linewidth=2.0, alpha=0.9, zorder=3)
        elif x % 10 == 0:
            # 10-yard lines
            ax.axvline(x, color="white", linewidth=1.2, alpha=0.75, zorder=3)
        else:
            # 5-yard lines
            ax.axvline(x, color="white", linewidth=0.7, alpha=0.4, zorder=3)

    # Sidelines and end lines
    ax.axhline(0, color="white", linewidth=1.5, alpha=0.8, zorder=3)
    ax.axhline(53.33, color="white", linewidth=1.5, alpha=0.8, zorder=3)
    ax.axvline(0, color="white", linewidth=1.5, alpha=0.8, zorder=3)
    ax.axvline(120, color="white", linewidth=1.5, alpha=0.8, zorder=3)

    # Hash marks (NFL inbounds hashes at y=23.366 and y=29.966, plus sideline ticks)
    if show_hashmarks:
        hash_start = max(11, int(np.floor(x_min)))
        hash_end = min(110, int(np.ceil(x_max)))
        for x in range(hash_start, hash_end):
            if x % 5 != 0:
                ax.plot([x, x], [23.1, 23.6], color="white", linewidth=0.6, alpha=0.5, zorder=3)
                ax.plot([x, x], [29.7, 30.2], color="white", linewidth=0.6, alpha=0.5, zorder=3)
                ax.plot([x, x], [0.0, 0.4], color="white", linewidth=0.6, alpha=0.5, zorder=3)
                ax.plot([x, x], [52.93, 53.33], color="white", linewidth=0.6, alpha=0.5, zorder=3)

    # Yard numbers
    if show_yard_numbers:
        for x in range(20, 110, 10):
            if x_min - 5 <= x <= x_max + 5:
                num = x - 10 if x <= 60 else 120 - x - 10
                # Bottom sideline numbers
                ax.text(
                    x,
                    7.0,
                    str(num),
                    color="white",
                    fontsize=10,
                    fontweight="bold",
                    alpha=0.65,
                    ha="center",
                    va="center",
                    zorder=3,
                )
                # Top sideline numbers (inverted)
                ax.text(
                    x,
                    53.33 - 7.0,
                    str(num),
                    color="white",
                    fontsize=10,
                    fontweight="bold",
                    alpha=0.65,
                    ha="center",
                    va="center",
                    rotation=180,
                    zorder=3,
                )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal")
    ax.set_xlabel("Field Length (yards)", color="#d1d5db", fontsize=10)
    ax.set_ylabel("Field Width (yards)", color="#d1d5db", fontsize=10)
    ax.tick_params(colors="#9ca3af")
    for spine in ax.spines.values():
        spine.set_color("#4b5563")

    return ax


def plot_route(
    data: pd.DataFrame,
    event_id: str | None = None,
    entity_type: str = "PLAYER",
    zoom_to_route: bool = True,
    padding: float = 6.0,
    show_start_finish: bool = True,
    show_ball: bool = True,
    ax: plt.Axes | None = None,
    title: str | None = None,
    save_path: str | Path | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot the route run for an attempt on a football-styled field.

    Parameters
    ----------
    data : pd.DataFrame
        Tracking data for one or more events.
    event_id : str | None
        Specific event identifier. Required if `data` contains multiple events.
    entity_type : str
        Primary entity to highlight ('PLAYER' or 'BALL'). Defaults to 'PLAYER'.
    zoom_to_route : bool
        If True, zoom in on the route bounding box with padding.
    padding : float
        Padding yards added around the route when zooming.
    show_start_finish : bool
        Whether to draw green Start and red Finish markers.
    show_ball : bool
        Whether to also plot the ball trajectory if available for the attempt.
    ax : plt.Axes | None
        Existing axes to draw on. If None, creates a new figure and axes.
    title : str | None
        Custom title. If None, generates title with drill, year, attempt, and player ID.
    save_path : str | Path | None
        Optional file path to save the generated figure.

    Returns
    -------
    tuple[plt.Figure, plt.Axes]
    """
    df = data.copy()
    if event_id is not None:
        df = df[df["event_id"] == event_id]
    elif len(df["event_id"].unique()) > 1:
        first_event = df["event_id"].iloc[0]
        df = df[df["event_id"] == first_event]

    if df.empty:
        raise ValueError("No tracking data found for the specified attempt.")

    # Sort frames chronologically
    df = df.sort_values(by="time").reset_index(drop=True)

    # Extract metadata from the first row
    first_row = df.iloc[0]
    drill_name = str(first_row.get("drill_name", "UNKNOWN"))
    drill_type = str(first_row.get("drill_type", ""))
    draft_year = first_row.get("draft_year", "")
    nfl_id = first_row.get("nfl_id", "")
    attempt = first_row.get("attempt", "")
    current_event_id = str(first_row.get("event_id", ""))

    # Separate player and ball data
    player_df = df[df["entity_type"] == "PLAYER"]
    ball_df = df[df["entity_type"] == "BALL"]

    # Select primary entity data
    primary_df = player_df if entity_type == "PLAYER" and not player_df.empty else df
    if primary_df.empty:
        primary_df = df

    # Determine view boundaries (encompassing both player and ball if present)
    bounds_df = df if (show_ball and not ball_df.empty) else primary_df
    if zoom_to_route:
        x_min = float(bounds_df["x"].min() - padding)
        x_max = float(bounds_df["x"].max() + padding)
        y_min = float(bounds_df["y"].min() - padding)
        y_max = float(bounds_df["y"].max() + padding)

        # Enforce minimum dimension of 16 yards for context
        if (x_max - x_min) < 16:
            mid_x = (x_min + x_max) / 2
            x_min, x_max = mid_x - 8.0, mid_x + 8.0
        if (y_max - y_min) < 14:
            mid_y = (y_min + y_max) / 2
            y_min, y_max = mid_y - 7.0, mid_y + 7.0
    else:
        x_min, x_max = 0.0, 120.0
        y_min, y_max = 0.0, 53.33

    # Create figure if not provided
    fig: plt.Figure
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 6), facecolor="#111827")
    else:
        fig = ax.figure  # type: ignore[assignment]

    # Draw the green football field
    draw_football_field(ax, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)

    # Plot Ball route if available
    if show_ball and not ball_df.empty:
        ax.plot(
            ball_df["x"],
            ball_df["y"],
            color="#fb923c",
            linewidth=2.2,
            linestyle="--",
            alpha=0.9,
            zorder=5,
            label="Ball Trajectory",
        )
        # Mark ball start and catch/end with authentic football symbol
        ax.scatter(
            ball_df["x"].iloc[0],
            ball_df["y"].iloc[0],
            color="#78350f",
            edgecolors="white",
            linewidth=1.5,
            s=160,
            marker=FOOTBALL_MARKER,
            zorder=6,
            label="Football (Start)",
        )
        ax.scatter(
            ball_df["x"].iloc[-1],
            ball_df["y"].iloc[-1],
            color="#78350f",
            edgecolors="white",
            linewidth=1.8,
            s=220,
            marker=FOOTBALL_MARKER,
            zorder=6,
            label="Football (Catch/End)",
        )

    # Plot Route run (white line on green turf)
    route_label = f"{entity_type.capitalize()} Route"
    ax.plot(
        primary_df["x"],
        primary_df["y"],
        color="white",
        linewidth=2.8,
        alpha=0.95,
        solid_capstyle="round",
        zorder=7,
        label=route_label,
    )

    # Start and Finish markers
    if show_start_finish and not primary_df.empty:
        start_x = primary_df["x"].iloc[0]
        start_y = primary_df["y"].iloc[0]
        end_x = primary_df["x"].iloc[-1]
        end_y = primary_df["y"].iloc[-1]

        ax.scatter(
            start_x,
            start_y,
            color="#22c55e",
            edgecolors="white",
            linewidth=2,
            s=130,
            zorder=8,
            label="Start",
        )
        ax.scatter(
            end_x,
            end_y,
            color="#ef4444",
            edgecolors="white",
            linewidth=2,
            s=130,
            zorder=8,
            label="Finish",
        )

    # Compute route metrics
    total_dist = (
        float(primary_df["dis"].sum())
        if "dis" in primary_df
        else float(np.sum(np.hypot(np.diff(primary_df["x"]), np.diff(primary_df["y"]))))
    )
    max_speed = float(primary_df["s"].max()) if "s" in primary_df else 0.0
    num_frames = len(primary_df)
    duration_sec = num_frames * 0.1

    # Configure Title & Subtitles
    header = title if title is not None else f"{drill_name} ({drill_type})"
    subtitle = (
        f"Year: {draft_year} | Player: {nfl_id} | Attempt: {attempt} | "
        f"Entity: {entity_type} | Event: {current_event_id[:16]}...\n"
        f"Distance: {total_dist:.1f} yds | Max Speed: {max_speed:.1f} yd/s | "
        f"Duration: {duration_sec:.1f}s ({num_frames} frames)"
    )
    ax.set_title(f"{header}\n{subtitle}", color="white", fontsize=11, fontweight="bold", pad=12)

    # Legend
    leg = ax.legend(
        loc="upper right",
        facecolor="#1f2937",
        edgecolor="#374151",
        labelcolor="white",
        fontsize=9,
        framealpha=0.85,
    )
    leg.set_zorder(10)

    if save_path is not None:
        fig.savefig(save_path, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())

    return fig, ax
