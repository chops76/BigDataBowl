"""Build standalone HTML viewer artifact with embedded curated events."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from databowl.data import load_combine_tracking, load_players


def extract_curated_events() -> list[dict]:
    """Extract a curated sample of combine drill events (including drills with ball)."""
    df = load_combine_tracking()
    players = load_players()

    player_map: dict[int, dict[str, str]] = {}
    if players is not None:
        for _, r in players.iterrows():
            raw_col = r.get("college_name")
            player_map[int(r["nfl_id"])] = {
                "name": str(r.get("display_name", "")),
                "pos": str(r.get("nfl_position", "")) if pd.notna(r.get("nfl_position")) else "",
                "college": str(raw_col) if pd.notna(raw_col) else "",
            }

    # Selected drills with and without ball
    drills = [
        "POST_CORNER_ROUTE_RIGHT",
        "GO_ROUTE_RIGHT",
        "CORNER_ROUTE",
        "COMEBACK_ROUTE_RIGHT",
        "FORTY_YARD_DASH",
        "THREE_CONE_DRILL",
        "SHORT_SHUTTLE",
        "BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION",
        "OL_PULL_DRILL_FOLD_BLOCK_RIGHT",
    ]

    curated = []
    for d in drills:
        sub = df[df["drill_name"] == d]
        if sub.empty:
            continue
        for ev in sub["event_id"].unique()[:2]:
            ev_df = sub[sub["event_id"] == ev].sort_values("time")
            first = ev_df.iloc[0]
            nid = int(first["nfl_id"])
            pinfo = player_map.get(nid, {})

            pts = []
            for _, r in ev_df.iterrows():
                pts.append(
                    {
                        "t": str(r["time"]),
                        "e": str(r["entity_type"]),
                        "x": round(float(r["x"]), 2),
                        "y": round(float(r["y"]), 2),
                        "s": round(float(r["s"]), 2),
                        "a": round(float(r["a"]), 2),
                        "dis": round(float(r["dis"]), 2),
                        "dir": round(float(r["dir"]), 1),
                    }
                )

            player_pts = [p for p in pts if p["e"] == "PLAYER"]
            ball_pts = [p for p in pts if p["e"] == "BALL"]
            prim = player_pts if player_pts else pts
            tot_dis = sum(p["dis"] for p in prim)
            max_s = max(p["s"] for p in prim)

            curated.append(
                {
                    "event_id": str(ev),
                    "draft_year": int(first["draft_year"]),
                    "drill_type": str(first["drill_type"]),
                    "drill_name": str(first["drill_name"]),
                    "nfl_id": nid,
                    "player_name": pinfo.get("name", ""),
                    "position": pinfo.get("pos", ""),
                    "college": pinfo.get("college", ""),
                    "attempt": int(first["attempt"]),
                    "has_ball": len(ball_pts) > 0,
                    "ball_frames": len(ball_pts),
                    "points": pts,
                    "stats": {
                        "total_dist": round(tot_dis, 1),
                        "max_speed": round(max_s, 1),
                        "num_frames": len(prim),
                        "duration_sec": round(len(prim) * 0.1, 1),
                    },
                }
            )

    return curated


def main() -> None:
    curated_events = extract_curated_events()

    artifact_dir = (
        Path("/home/dchopskie/.gemini/antigravity/brain") / "2e3d4ddb-e4dd-442f-a638-82792948cbad"
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_file = artifact_dir / "combine_route_viewer.html"

    template_path = Path("src/databowl/templates/viewer.html")
    html = template_path.read_text(encoding="utf-8")

    data_json = json.dumps(curated_events)
    injection = f"""
    // Embedded standalone curated dataset
    const EMBEDDED_EVENTS = {data_json};

    function initFromEmbedded() {{
      events = EMBEDDED_EVENTS;
      const years = Array.from(new Set(events.map(e => e.draft_year))).sort();
      const drillTypes = Array.from(new Set(events.map(e => e.drill_type))).sort();
      const allDrills = Array.from(new Set(events.map(e => e.drill_name))).sort();
      const drillsWithBall = Array.from(
        new Set(events.filter(e => e.has_ball).map(e => e.drill_name))
      ).sort();

      const drillsByType = {{}};
      events.forEach(e => {{
        if (!drillsByType[e.drill_type]) drillsByType[e.drill_type] = [];
        if (!drillsByType[e.drill_type].includes(e.drill_name)) {{
          drillsByType[e.drill_type].push(e.drill_name);
        }}
      }});

      const players = [];
      const seenP = new Set();
      events.forEach(e => {{
        if (!seenP.has(e.nfl_id)) {{
          seenP.add(e.nfl_id);
          players.push({{
            nfl_id: e.nfl_id,
            display_name: e.player_name || `Player ${{e.nfl_id}}`,
            position: e.position || '',
            college: e.college || ''
          }});
        }}
      }});

      options = {{
        years,
        drill_types: drillTypes,
        all_drills: allDrills,
        drills_by_type: drillsByType,
        drills_with_ball: drillsWithBall,
        players
      }};

      populateFilterDropdowns();
      filterEmbeddedEvents();
    }}

    function filterEmbeddedEvents() {{
      const year = document.getElementById('filter-year').value;
      const drillType = document.getElementById('filter-drill-type').value;
      const drillName = document.getElementById('filter-drill-name').value;
      const nflId = document.getElementById('filter-player').value;
      const attempt = document.getElementById('filter-attempt').value;
      const onlyBall = document.getElementById('filter-only-ball').checked;

      events = EMBEDDED_EVENTS.filter(e => {{
        if (year && String(e.draft_year) !== year) return false;
        if (drillType && e.drill_type !== drillType) return false;
        if (drillName && e.drill_name !== drillName) return false;
        if (nflId && String(e.nfl_id) !== nflId) return false;
        if (attempt && String(e.attempt) !== attempt) return false;
        if (onlyBall && !e.has_ball) return false;
        return true;
      }});

      const attemptSelect = document.getElementById('filter-attempt');
      const curAtt = attemptSelect.value;
      const uniqueAttempts = Array.from(new Set(events.map(e => e.attempt))).sort((a,b)=>a-b);
      attemptSelect.innerHTML = '<option value="">All</option>';
      uniqueAttempts.forEach(a => {{
        const opt = document.createElement('option');
        opt.value = a;
        opt.textContent = `Attempt ${{a}}`;
        if (String(a) === String(curAtt)) opt.selected = true;
        attemptSelect.appendChild(opt);
      }});

      currentEventIndex = 0;
      updateNavDisplay();
      if (events.length > 0) {{
        currentRouteData = events[currentEventIndex];
        currentRouteData.playerPoints = currentRouteData.points.filter(p => p.e === 'PLAYER');
        currentRouteData.ballPoints = currentRouteData.points.filter(p => p.e === 'BALL');
        const primary = currentRouteData.playerPoints.length > 0
          ? currentRouteData.playerPoints
          : currentRouteData.points;
        totalDurationSec = Math.max((primary.length - 1) * 0.1, 0.1);
        animElapsedSec = 0;
        loopPauseTimer = 0;
        updateMetadata(currentRouteData);
      }} else {{
        clearDisplay();
      }}
    }}
"""

    old_init = """    async function init() {
      try {
        const resp = await fetch('/api/options');
        options = await resp.json();
        populateFilterDropdowns();
        await loadEvents();
      } catch (err) {
        console.error('Failed to initialize options:', err);
      }
      requestAnimationFrame(animationLoop);
    }"""

    new_init = """    async function init() {
      let loadedFromApi = false;
      try {
        const resp = await fetch('/api/options');
        if (resp.ok) {
          options = await resp.json();
          populateFilterDropdowns();
          await loadEvents();
          loadedFromApi = true;
        }
      } catch (err) {
        // Fallback to embedded data
      }

      if (!loadedFromApi) {
        initFromEmbedded();
      }
      requestAnimationFrame(animationLoop);
    }"""

    old_load_events = """    async function loadEvents() {"""
    new_load_events = """    async function loadEvents() {
      if (window.location.protocol === 'file:' || !window.location.host) {
        filterEmbeddedEvents();
        return;
      }"""

    old_load_route = """    async function loadCurrentRoute() {
      if (!events || events.length === 0) return;
      const ev = events[currentEventIndex];
      const resp = await fetch(`/api/route?event_id=${encodeURIComponent(ev.event_id)}`);
      currentRouteData = await resp.json();

      // Separate player and ball points
      currentRouteData.playerPoints = currentRouteData.points.filter(p => p.e === 'PLAYER');
      currentRouteData.ballPoints = currentRouteData.points.filter(p => p.e === 'BALL');

      const primary = currentRouteData.playerPoints.length > 0
        ? currentRouteData.playerPoints
        : currentRouteData.points;

      totalDurationSec = Math.max((primary.length - 1) * 0.1, 0.1);
      animElapsedSec = 0;
      loopPauseTimer = 0;

      updateMetadata(currentRouteData);
    }"""

    new_load_route = """    async function loadCurrentRoute() {
      if (!events || events.length === 0) return;
      const ev = events[currentEventIndex];
      if (ev.points) {
        currentRouteData = ev;
        currentRouteData.playerPoints = currentRouteData.points.filter(p => p.e === 'PLAYER');
        currentRouteData.ballPoints = currentRouteData.points.filter(p => p.e === 'BALL');
        const primary = currentRouteData.playerPoints.length > 0
          ? currentRouteData.playerPoints
          : currentRouteData.points;
        totalDurationSec = Math.max((primary.length - 1) * 0.1, 0.1);
        animElapsedSec = 0;
        loopPauseTimer = 0;
        updateMetadata(currentRouteData);
        return;
      }
      try {
        const resp = await fetch(`/api/route?event_id=${encodeURIComponent(ev.event_id)}`);
        currentRouteData = await resp.json();
        currentRouteData.playerPoints = currentRouteData.points.filter(p => p.e === 'PLAYER');
        currentRouteData.ballPoints = currentRouteData.points.filter(p => p.e === 'BALL');
        const primary = currentRouteData.playerPoints.length > 0
          ? currentRouteData.playerPoints
          : currentRouteData.points;
        totalDurationSec = Math.max((primary.length - 1) * 0.1, 0.1);
        animElapsedSec = 0;
        loopPauseTimer = 0;
        updateMetadata(currentRouteData);
      } catch (err) {
        console.error(err);
      }
    }"""

    html = html.replace("let options = {};", injection + "\n    let options = {};")
    html = html.replace(old_init, new_init)
    html = html.replace(old_load_events, new_load_events)
    html = html.replace(old_load_route, new_load_route)

    out_file.write_text(html, encoding="utf-8")
    print(f"Standalone viewer written to: {out_file} ({out_file.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
