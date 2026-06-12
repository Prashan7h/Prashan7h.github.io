"""Fetch World Cup 2026 schedule + results.

Primary: openfootball worldcup.json (schedule, results, goal scorers).
Overlay: ESPN scoreboard (more current results, ESPN event ids used by espn.py).
Output: worldcup/data/matches.json
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

OPENFOOTBALL_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
)
ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
)
TOURNAMENT_START = date(2026, 6, 11)
TOURNAMENT_END = date(2026, 7, 19)

# ESPN team names -> openfootball team names
TEAM_ALIASES = {
    "Czechia": "Czech Republic",
    "Bosnia-Herzegovina": "Bosnia & Herzegovina",
    "United States": "USA",
    "Côte d'Ivoire": "Ivory Coast",
    "Türkiye": "Turkey",
    "Korea Republic": "South Korea",
    "IR Iran": "Iran",
    "Cabo Verde": "Cape Verde",
    "Curaçao": "Curaçao",
}


def canonical(name):
    return TEAM_ALIASES.get(name, name)


def match_key(team1, team2):
    return frozenset((canonical(team1), canonical(team2)))


def fetch_openfootball():
    r = requests.get(OPENFOOTBALL_URL, timeout=30)
    r.raise_for_status()
    return r.json()["matches"]


def fetch_espn_events():
    """All ESPN events from tournament start through today + 7 days."""
    end = min(date.today() + timedelta(days=7), TOURNAMENT_END)
    dates = f"{TOURNAMENT_START:%Y%m%d}-{end:%Y%m%d}"
    r = requests.get(ESPN_SCOREBOARD, params={"dates": dates, "limit": 200}, timeout=30)
    r.raise_for_status()
    return r.json().get("events", [])


def build_matches():
    of_matches = fetch_openfootball()
    try:
        espn_events = fetch_espn_events()
    except Exception as e:  # ESPN is an overlay; never fail the run on it
        print(f"warning: ESPN scoreboard unavailable: {e}", file=sys.stderr)
        espn_events = []

    espn_by_key = {}
    for ev in espn_events:
        comp = ev["competitions"][0]
        names = [c["team"]["displayName"] for c in comp["competitors"]]
        if len(names) == 2:
            espn_by_key[match_key(*names)] = ev

    matches = []
    for i, m in enumerate(of_matches):
        rec = {
            "num": i + 1,
            "round": m.get("round", ""),
            "date": m["date"],
            "time": m.get("time", ""),
            "team1": canonical(m["team1"]),
            "team2": canonical(m["team2"]),
            "group": m.get("group"),
            "ground": m.get("ground", ""),
            "score": m.get("score"),
            "goals1": m.get("goals1", []),
            "goals2": m.get("goals2", []),
            "espn_id": None,
            "status": "finished" if m.get("score") else "scheduled",
        }

        ev = espn_by_key.get(match_key(rec["team1"], rec["team2"]))
        if ev:
            comp = ev["competitions"][0]
            rec["espn_id"] = ev["id"]
            rec["utc_date"] = ev["date"]
            status = comp["status"]["type"]
            if status.get("completed") and not rec["score"]:
                # openfootball hasn't caught up yet; take FT score from ESPN
                by_name = {
                    canonical(c["team"]["displayName"]): int(c.get("score", 0))
                    for c in comp["competitors"]
                }
                rec["score"] = {"ft": [by_name[rec["team1"]], by_name[rec["team2"]]]}
                rec["status"] = "finished"
            elif status.get("state") == "in":
                rec["status"] = "live"
            if comp.get("attendance"):
                rec["attendance"] = comp["attendance"]
            if comp.get("venue"):
                rec["venue"] = comp["venue"].get("fullName", "")

        rec["slug"] = "{}-{}-vs-{}".format(
            rec["date"],
            rec["team1"].lower().replace(" ", "-").replace("&", "and"),
            rec["team2"].lower().replace(" ", "-").replace("&", "and"),
        )
        matches.append(rec)

    return matches


def main():
    matches = build_matches()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "matches.json"
    out.write_text(json.dumps({"matches": matches}, indent=1, ensure_ascii=False))
    finished = sum(1 for m in matches if m["status"] == "finished")
    print(f"wrote {out}: {len(matches)} matches, {finished} finished")


if __name__ == "__main__":
    main()
