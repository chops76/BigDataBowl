"""Interactive NFL Combine Route Viewer web application and server."""

from __future__ import annotations

import argparse
import io
import json
import logging
import socket
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from databowl.data import get_combine_tracking_path, load_combine_tracking, load_players
from databowl.visualization import plot_route

logger = logging.getLogger("databowl.viewer")
TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "viewer.html"


def load_template_html() -> str:
    """Load the single-page application HTML template."""
    if TEMPLATE_PATH.exists():
        return TEMPLATE_PATH.read_text(encoding="utf-8")
    return "<h1>Combine Route Viewer HTML template not found.</h1>"


class CombineViewerHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the Combine Route Viewer."""

    server: CombineTrackingServer  # type: ignore[assignment]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug(
            "%s - - [%s] %s",
            self.address_string(),
            self.log_date_time_string(),
            format % args,
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path in ("/", "/index.html"):
            self._serve_html()
        elif path == "/api/options":
            self._serve_options()
        elif path == "/api/events":
            self._serve_events(query)
        elif path == "/api/route":
            self._serve_route(query)
        elif path == "/api/image":
            self._serve_image(query)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def _serve_html(self) -> None:
        content = load_template_html().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_options(self) -> None:
        data = self.server.options_data
        body = json.dumps(data).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_events(self, query: dict[str, list[str]]) -> None:
        year_str = query.get("year", [None])[0]
        drill_type = query.get("drill_type", [None])[0]
        drill_name = query.get("drill_name", [None])[0]
        nfl_id_str = query.get("nfl_id", [None])[0]
        attempt_str = query.get("attempt", [None])[0]
        has_ball_param = query.get("has_ball", [None])[0]

        filtered = self.server.events_list
        if year_str:
            y = int(year_str)
            filtered = [e for e in filtered if e["draft_year"] == y]
        if drill_type:
            filtered = [e for e in filtered if e["drill_type"] == drill_type]
        if drill_name:
            filtered = [e for e in filtered if e["drill_name"] == drill_name]
        if nfl_id_str:
            nid = int(nfl_id_str)
            filtered = [e for e in filtered if e["nfl_id"] == nid]
        if attempt_str:
            att = int(attempt_str)
            filtered = [e for e in filtered if e["attempt"] == att]
        if has_ball_param is not None and has_ball_param.lower() in ("true", "1", "yes"):
            filtered = [e for e in filtered if e.get("has_ball", False)]

        body = json.dumps(filtered).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_route(self, query: dict[str, list[str]]) -> None:
        event_id = query.get("event_id", [None])[0]
        if not event_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing event_id parameter")
            return

        route_payload = self.server.get_event_payload(event_id)
        if route_payload is None:
            self.send_error(HTTPStatus.NOT_FOUND, f"Event {event_id} not found")
            return

        body = json.dumps(route_payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_image(self, query: dict[str, list[str]]) -> None:
        event_id = query.get("event_id", [None])[0]
        if not event_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing event_id")
            return

        event_df = self.server.tracking_df[self.server.tracking_df["event_id"] == event_id]
        if event_df.empty:
            self.send_error(HTTPStatus.NOT_FOUND, f"Event {event_id} not found")
            return

        zoom = query.get("zoom", ["true"])[0].lower() in ("true", "1")
        fig, _ = plot_route(event_df, zoom_to_route=zoom)
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=100,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
        )
        plt.close(fig)

        img_bytes = buf.getvalue()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(img_bytes)))
        self.end_headers()
        self.wfile.write(img_bytes)


class CombineTrackingServer(ThreadingHTTPServer):
    """Server that holds tracking data in memory and serves the viewer application."""

    def __init__(
        self,
        server_address: tuple[str, int],
        tracking_df: pd.DataFrame,
        players_df: pd.DataFrame | None = None,
    ) -> None:
        super().__init__(server_address, CombineViewerHandler)
        self.tracking_df = tracking_df
        self.players_df = players_df
        self._index_dataset()

    def _index_dataset(self) -> None:
        df = self.tracking_df
        players = self.players_df

        # Player dictionary
        self.player_map: dict[int, dict[str, str]] = {}
        if players is not None:
            p_cols = ["nfl_id", "display_name", "nfl_position", "college_name"]
            valid_cols = [c for c in p_cols if c in players.columns]
            if "nfl_id" in valid_cols:
                for _, row in players[valid_cols].drop_duplicates().iterrows():
                    nid = int(row["nfl_id"])
                    raw_pos = row.get("nfl_position")
                    raw_col = row.get("college_name")
                    pos = str(raw_pos) if pd.notna(raw_pos) else ""
                    col = str(raw_col) if pd.notna(raw_col) else ""
                    self.player_map[nid] = {
                        "display_name": str(row.get("display_name", "")),
                        "position": pos,
                        "college": col,
                    }

        # Events list with ball flag
        ball_events = set(df[df["entity_type"] == "BALL"]["event_id"].unique())
        drills_with_ball = sorted(
            str(d) for d in df[df["entity_type"] == "BALL"]["drill_name"].unique()
        )

        events_gb = df.groupby("event_id").first().reset_index()
        events_list = []
        for _, row in events_gb.iterrows():
            ev_id = str(row["event_id"])
            nid = int(row["nfl_id"]) if pd.notna(row["nfl_id"]) else None
            p_info = self.player_map.get(nid, {}) if nid is not None else {}
            events_list.append(
                {
                    "event_id": ev_id,
                    "draft_year": int(row["draft_year"]),
                    "drill_type": str(row["drill_type"]),
                    "drill_name": str(row["drill_name"]),
                    "nfl_id": nid,
                    "attempt": int(row["attempt"]),
                    "has_ball": (ev_id in ball_events),
                    "player_name": p_info.get("display_name", ""),
                    "position": p_info.get("position", ""),
                    "college": p_info.get("college", ""),
                }
            )
        self.events_list = events_list

        # Options data for filters
        years = sorted(int(y) for y in df["draft_year"].unique())
        drill_types = sorted(str(t) for t in df["drill_type"].unique())
        all_drills = sorted(str(d) for d in df["drill_name"].unique())

        drills_by_type: dict[str, list[str]] = {}
        for dt, sub in df.groupby("drill_type"):
            drills_by_type[str(dt)] = sorted(str(d) for d in sub["drill_name"].unique())

        players_list = []
        unique_nfl_ids = sorted(int(x) for x in df["nfl_id"].unique() if pd.notna(x))
        for nid in unique_nfl_ids:
            p_info = self.player_map.get(nid, {})
            players_list.append(
                {
                    "nfl_id": nid,
                    "display_name": p_info.get("display_name", f"Player {nid}"),
                    "position": p_info.get("position", ""),
                    "college": p_info.get("college", ""),
                }
            )

        self.options_data = {
            "years": years,
            "drill_types": drill_types,
            "all_drills": all_drills,
            "drills_by_type": drills_by_type,
            "drills_with_ball": drills_with_ball,
            "players": players_list,
        }

    def get_event_payload(self, event_id: str) -> dict[str, Any] | None:
        sub = self.tracking_df[self.tracking_df["event_id"] == event_id]
        if sub.empty:
            return None

        sub = sub.sort_values(by="time").reset_index(drop=True)
        first_row = sub.iloc[0]
        nid = int(first_row["nfl_id"]) if pd.notna(first_row["nfl_id"]) else None
        p_info = self.player_map.get(nid, {}) if nid is not None else {}

        points = []
        for _, row in sub.iterrows():
            points.append(
                {
                    "t": str(row["time"]),
                    "e": str(row["entity_type"]),
                    "x": round(float(row["x"]), 3),
                    "y": round(float(row["y"]), 3),
                    "s": round(float(row["s"]), 2),
                    "a": round(float(row["a"]), 2),
                    "dis": round(float(row["dis"]), 2),
                    "dir": round(float(row["dir"]), 1),
                }
            )

        player_sub = sub[sub["entity_type"] == "PLAYER"]
        ball_sub = sub[sub["entity_type"] == "BALL"]
        has_ball = not ball_sub.empty
        primary = player_sub if not player_sub.empty else sub
        total_dist = float(primary["dis"].sum()) if "dis" in primary else 0.0
        max_speed = float(primary["s"].max()) if "s" in primary else 0.0
        max_accel = float(primary["a"].max()) if "a" in primary else 0.0
        num_frames = len(primary)

        return {
            "event_id": event_id,
            "draft_year": int(first_row["draft_year"]),
            "drill_type": str(first_row["drill_type"]),
            "drill_name": str(first_row["drill_name"]),
            "nfl_id": nid,
            "player_name": p_info.get("display_name", ""),
            "position": p_info.get("position", ""),
            "college": p_info.get("college", ""),
            "attempt": int(first_row["attempt"]),
            "has_ball": has_ball,
            "ball_frames": len(ball_sub),
            "points": points,
            "stats": {
                "total_dist": total_dist,
                "max_speed": max_speed,
                "max_accel": max_accel,
                "num_frames": num_frames,
                "duration_sec": num_frames * 0.1,
            },
        }


def find_free_port(start_port: int = 8080) -> int:
    """Find a free TCP port starting at `start_port`."""
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


def run_viewer(
    host: str = "127.0.0.1",
    port: int = 8080,
    data_path: str | Path | None = None,
    open_browser: bool = True,
) -> CombineTrackingServer:
    """Start the Combine Route Viewer server."""
    csv_path = get_combine_tracking_path(data_path)
    logger.info("Loading combine tracking from %s...", csv_path)
    df = load_combine_tracking(csv_path)
    players = load_players()

    actual_port = find_free_port(port)
    server_address = (host, actual_port)
    server = CombineTrackingServer(server_address, df, players)

    url = f"http://{host}:{actual_port}"
    print(f"\n🏈 NFL Combine Route Viewer is live at: {url}")
    print(f"Loaded {len(df):,} tracking rows across {len(server.events_list):,} drill attempts.")
    print("Press Ctrl+C to stop the server.\n")

    if open_browser:
        webbrowser.open(url)

    return server


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="NFL Combine Route Viewer")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--data", default=None, help="Path to combine_tracking.csv")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open browser",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    server = run_viewer(
        host=args.host,
        port=args.port,
        data_path=args.data,
        open_browser=not args.no_browser,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping viewer server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
