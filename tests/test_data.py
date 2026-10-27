from pathlib import Path

import pandas as pd
import pytest

from databowl.data import (
    clean,
    get_combine_tracking_path,
    get_event_route,
    get_players_path,
    load_combine_tracking,
    load_csv,
    load_players,
)


def test_clean_drops_duplicates_and_empty_rows():
    df = pd.DataFrame({"a": [1, 1, None], "b": [2, 2, None]})
    out = clean(df)
    assert len(out) == 1
    assert list(out.columns) == ["a", "b"]


def test_load_csv(tmp_path: Path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("x,y\n1,2\n3,4\n")
    df = load_csv(csv_file)
    assert len(df) == 2
    assert list(df.columns) == ["x", "y"]


def test_get_combine_tracking_path_custom(tmp_path: Path):
    fake_csv = tmp_path / "combine_tracking.csv"
    fake_csv.write_text("draft_year\n2025\n")
    resolved = get_combine_tracking_path(fake_csv)
    assert resolved == fake_csv


def test_get_combine_tracking_path_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        get_combine_tracking_path(tmp_path / "nonexistent.csv")


def test_get_players_path_custom(tmp_path: Path):
    fake_csv = tmp_path / "players.csv"
    fake_csv.write_text("nfl_id\n12345\n")
    resolved = get_players_path(fake_csv)
    assert resolved == fake_csv

    missing = get_players_path(tmp_path / "does_not_exist.csv")
    assert missing is None


def test_load_combine_tracking_filtering(tmp_path: Path):
    csv_file = tmp_path / "combine_tracking.csv"
    csv_file.write_text(
        "draft_year,event_id,nfl_id,entity_type,time,drill_type,drill_name,attempt,x,y,s,a,dis,dir\n"
        "2024,ev1,1001,PLAYER,2024-03-01T10:00:00.000,FORTY_YARD_DASH,FORTY_YARD_DASH,1,10.0,0.0,5.0,2.0,0.5,90.0\n"
        "2025,ev2,1002,PLAYER,2025-03-01T10:00:00.000,SKILL_DRILLS_WR,GO_ROUTE_RIGHT,2,20.0,15.0,6.0,1.5,0.6,180.0\n"
    )
    df_all = load_combine_tracking(csv_file)
    assert len(df_all) == 2

    df_2025 = load_combine_tracking(csv_file, draft_year=2025)
    assert len(df_2025) == 1
    assert df_2025.iloc[0]["event_id"] == "ev2"

    df_drill = load_combine_tracking(csv_file, drill_type="FORTY_YARD_DASH")
    assert len(df_drill) == 1
    assert df_drill.iloc[0]["drill_type"] == "FORTY_YARD_DASH"

    df_name = load_combine_tracking(csv_file, drill_name="GO_ROUTE_RIGHT")
    assert len(df_name) == 1

    df_player = load_combine_tracking(csv_file, nfl_id=1001)
    assert len(df_player) == 1

    df_event = load_combine_tracking(csv_file, event_id="ev2")
    assert len(df_event) == 1


def test_load_players_returns_df_or_none(tmp_path: Path):
    players_csv = tmp_path / "players.csv"
    players_csv.write_text("nfl_id,display_name\n1001,John Doe\n")
    df = load_players(players_csv)
    assert df is not None
    assert len(df) == 1


def test_get_event_route(tmp_path: Path):
    df = pd.DataFrame(
        {
            "event_id": ["e1", "e1", "e2"],
            "time": [
                "2025-03-01T10:00:00.200",
                "2025-03-01T10:00:00.100",
                "2025-03-01T10:00:00.100",
            ],
            "entity_type": ["PLAYER", "PLAYER", "PLAYER"],
            "x": [15.0, 10.0, 20.0],
            "y": [1.0, 0.0, 2.0],
        }
    )
    route = get_event_route(df, "e1")
    assert len(route) == 2
    # Ensure ordered by time
    assert route.iloc[0]["time"] == "2025-03-01T10:00:00.100"
    assert route.iloc[1]["time"] == "2025-03-01T10:00:00.200"
