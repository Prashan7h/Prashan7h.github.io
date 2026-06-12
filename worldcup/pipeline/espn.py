"""Fetch per-match data from ESPN: boxscore stats, key events, lineups,
and shot-level play-by-play with a naive xG computed from shot location.

ESPN's free feed has no xG, but the play-by-play carries field coordinates
for every attempt — so we fit a simple distance/angle logistic model.

Output: worldcup/data/stats/<espn_id>.json (cached forever once written)
"""
import json
import math
import re
import sys
import time
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATS_DIR = DATA_DIR / "stats"

ESPN_SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary"
ESPN_PLAYS = ("https://sports.core.api.espn.com/v2/sports/soccer/leagues/"
              "fifa.world/events/{eid}/competitions/{eid}/plays")

STAT_KEYS = [
    "possessionPct", "totalShots", "shotsOnTarget", "wonCorners",
    "foulsCommitted", "offsides", "saves", "yellowCards", "redCards",
]

def is_shot_type(typ):
    """ESPN play types: 'Shot On Target', 'Goal', 'Goal - Header',
    'Penalty - Scored', etc. Goal kicks are not shots."""
    if typ.lower().startswith("goal kick"):
        return False
    return typ.startswith(("Goal", "Shot", "Penalty"))


def shot_xg(x, y, header=False, penalty=False):
    """Naive xG from shot location (x: 0-100 toward goal, y: 0-100, centre 50).
    Logistic on distance + goalmouth angle; constants hand-tuned, not trained."""
    if penalty:
        return 0.76
    dx = (100 - x) * 1.05  # pitch ~105m x 68m
    dy = (y - 50) * 0.68
    dist = math.hypot(dx, dy)
    post = 7.32 / 2
    angle = abs(math.atan2(dy + post, dx) - math.atan2(dy - post, dx))
    z = -1.1 + 2.2 * angle - 0.075 * dist
    xg = 1 / (1 + math.exp(-z))
    if header:
        xg *= 0.65
    return round(min(xg, 0.95), 3)


def team_id_from_ref(ref):
    m = re.search(r"/teams/(\d+)", ref or "")
    return m.group(1) if m else None


def fetch_all_plays(eid):
    items = []
    page = 1
    while True:
        r = requests.get(ESPN_PLAYS.format(eid=eid),
                         params={"limit": 1000, "page": page}, timeout=30)
        r.raise_for_status()
        d = r.json()
        items.extend(d.get("items", []))
        if page >= d.get("pageCount", 1):
            return items
        page += 1


def extract_shots(plays, id_to_name):
    shots = []
    for p in plays:
        typ = p.get("type", {}).get("text", "")
        if not is_shot_type(typ) or p.get("fieldPositionX") is None:
            continue
        text = p.get("text", "")
        clock = p.get("clock", {})
        shots.append({
            "minute": clock.get("displayValue", "").rstrip("'"),
            "seconds": clock.get("value"),
            "team": id_to_name.get(team_id_from_ref(p.get("team", {}).get("$ref"))),
            "player": (p.get("participants") or [{}])[0]
                      .get("athlete", {}).get("$ref", ""),  # resolved below if possible
            "type": typ,
            "x": p["fieldPositionX"],
            "y": p["fieldPositionY"],
            "goal": bool(p.get("scoreValue")),
            "xg": shot_xg(p["fieldPositionX"], p["fieldPositionY"],
                          header="header" in text.lower(),
                          penalty="penalty" in typ.lower() or "penalty" in text.lower()),
            "text": text,
        })
    # player name: pull from the play text ("... Name (Team) ...")
    for s in shots:
        m = re.search(r"(?:missed\.|saved\.|blocked\.|\d, \d\.|Goal!.*?\d\.)\s*([^(]+?)\s*\(", s["text"])
        s["player"] = m.group(1).strip() if m else None
    return shots


def extract_lineups(summary):
    lineups = []
    for r in summary.get("rosters", []):
        starters, subs = [], []
        for entry in r.get("roster", []):
            item = {
                "name": entry.get("athlete", {}).get("displayName"),
                "jersey": entry.get("jersey"),
                "position": entry.get("position", {}).get("abbreviation"),
            }
            (starters if entry.get("starter") else subs).append(item)
        lineups.append({
            "team": r.get("team", {}).get("displayName"),
            "formation": r.get("formation"),
            "starters": starters,
            "subs": subs,
        })
    return lineups


def extract(summary, plays):
    out = {"teams": [], "events": [], "shots": [], "lineups": [],
           "attendance": None, "venue": None}

    id_to_name = {}
    for t in summary.get("boxscore", {}).get("teams", []):
        team = t["team"]
        id_to_name[str(team.get("id"))] = team["displayName"]
        stats = {s["name"]: s.get("displayValue") for s in t.get("statistics", [])}
        out["teams"].append({"name": team["displayName"],
                             "stats": {k: stats.get(k) for k in STAT_KEYS}})

    for ev in summary.get("keyEvents", []):
        out["events"].append({
            "type": ev.get("type", {}).get("text", ""),
            "minute": ev.get("clock", {}).get("displayValue", ""),
            "team": ev.get("team", {}).get("displayName"),
            "text": ev.get("text", ""),
            "players": [p.get("athlete", {}).get("displayName")
                        for p in ev.get("participants", []) if p.get("athlete")],
        })

    out["shots"] = extract_shots(plays, id_to_name)
    out["lineups"] = extract_lineups(summary)

    info = summary.get("gameInfo", {})
    out["attendance"] = info.get("attendance")
    venue = info.get("venue", {})
    if venue:
        addr = venue.get("address", {})
        out["venue"] = ", ".join(
            x for x in [venue.get("fullName"), addr.get("city"), addr.get("country")] if x)
    return out


def main():
    matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]
    STATS_DIR.mkdir(parents=True, exist_ok=True)

    todo = [m for m in matches
            if m["status"] == "finished" and m.get("espn_id")
            and not (STATS_DIR / f"{m['espn_id']}.json").exists()]
    print(f"{len(todo)} finished matches need stats")

    for m in todo:
        try:
            r = requests.get(ESPN_SUMMARY, params={"event": m["espn_id"]}, timeout=30)
            r.raise_for_status()
            summary = r.json()
            try:
                plays = fetch_all_plays(m["espn_id"])
            except Exception as e:
                print(f"  warning: no plays for {m['slug']}: {e}", file=sys.stderr)
                plays = []
            data = extract(summary, plays)
            (STATS_DIR / f"{m['espn_id']}.json").write_text(
                json.dumps(data, indent=1, ensure_ascii=False))
            n_shots = len(data["shots"])
            xg = {}
            for s in data["shots"]:
                xg[s["team"]] = xg.get(s["team"], 0) + s["xg"]
            print(f"  {m['team1']} vs {m['team2']}: {n_shots} shots, "
                  f"xG {' / '.join(f'{v:.2f}' for v in xg.values())}")
        except Exception as e:
            print(f"  warning: no stats for {m['slug']}: {e}", file=sys.stderr)
        time.sleep(1)


if __name__ == "__main__":
    main()
