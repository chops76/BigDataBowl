import threading
import urllib.request

import pandas as pd
import pytest

from databowl.viewer import CombineTrackingServer, find_free_port, load_template_html


@pytest.fixture
def test_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    tracking_df = pd.DataFrame(
        {
            "draft_year": [2024, 2024, 2025],
            "event_id": ["ev_1", "ev_1", "ev_2"],
            "nfl_id": [5001, 5001, 5002],
            "entity_type": ["PLAYER", "PLAYER", "PLAYER"],
            "time": [
                "2024-03-01T10:00:00.100",
                "2024-03-01T10:00:00.200",
                "2025-03-01T10:00:00.100",
            ],
            "drill_type": ["FORTY_YARD_DASH", "FORTY_YARD_DASH", "SKILL_DRILLS_WR"],
            "drill_name": ["FORTY_YARD_DASH", "FORTY_YARD_DASH", "GO_ROUTE_RIGHT"],
            "attempt": [1, 1, 2],
            "x": [10.0, 15.0, 25.0],
            "y": [0.0, 0.2, 10.0],
            "s": [3.0, 5.0, 6.0],
            "a": [1.0, 1.2, 0.5],
            "dis": [0.3, 0.5, 0.6],
            "dir": [90.0, 92.0, 180.0],
        }
    )
    players_df = pd.DataFrame(
        {
            "nfl_id": [5001, 5002],
            "display_name": ["Alice Runner", "Bob Receiver"],
            "nfl_position": ["RB", "WR"],
            "college_name": ["State Univ", "Tech Univ"],
        }
    )
    return tracking_df, players_df


def test_load_template_html():
    html = load_template_html()
    assert "<!DOCTYPE html>" in html
    assert "NFL Combine Route Viewer" in html


def test_server_indexing_and_payload(test_dataset):
    tracking_df, players_df = test_dataset
    port = find_free_port(8900)
    server = CombineTrackingServer(("127.0.0.1", port), tracking_df, players_df)

    try:
        # Check indexed options
        assert server.options_data["years"] == [2024, 2025]
        assert "FORTY_YARD_DASH" in server.options_data["drill_types"]
        assert "SKILL_DRILLS_WR" in server.options_data["drill_types"]
        assert len(server.events_list) == 2

        # Check payload
        payload = server.get_event_payload("ev_1")
        assert payload is not None
        assert payload["event_id"] == "ev_1"
        assert payload["player_name"] == "Alice Runner"
        assert payload["position"] == "RB"
        assert payload["attempt"] == 1
        assert "has_ball" in payload
        assert "drills_with_ball" in server.options_data
        assert len(payload["points"]) == 2
        assert payload["stats"]["num_frames"] == 2

        # Non-existent event
        assert server.get_event_payload("does_not_exist") is None
    finally:
        server.server_close()


def test_viewer_http_endpoints(test_dataset):
    tracking_df, players_df = test_dataset
    port = find_free_port(9200)
    server = CombineTrackingServer(("127.0.0.1", port), tracking_df, players_df)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    base_url = f"http://127.0.0.1:{port}"
    try:
        # Test index html
        with urllib.request.urlopen(f"{base_url}/") as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers["Content-Type"]

        # Test options endpoint
        with urllib.request.urlopen(f"{base_url}/api/options") as resp:
            assert resp.status == 200
            assert "application/json" in resp.headers["Content-Type"]

        # Test events endpoint with filtering
        with urllib.request.urlopen(f"{base_url}/api/events?year=2025") as resp:
            assert resp.status == 200
            assert "application/json" in resp.headers["Content-Type"]

        # Test route endpoint
        with urllib.request.urlopen(f"{base_url}/api/route?event_id=ev_1") as resp:
            assert resp.status == 200
            assert "application/json" in resp.headers["Content-Type"]

        # Test image endpoint
        with urllib.request.urlopen(f"{base_url}/api/image?event_id=ev_1") as resp:
            assert resp.status == 200
            assert "image/png" in resp.headers["Content-Type"]
            assert len(resp.read()) > 1000
    finally:
        server.shutdown()
        server.server_close()
