"""Render the World Cup pages from data/ JSON into static HTML.

worldcup/index.html           — fixtures hub: Matches / Table / Predictions tabs
worldcup/matches/<slug>.html  — one match-report page per finished match
"""
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from analytics import decided_on, final_score, outcome

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATS_DIR = DATA_DIR / "stats"
TEMPLATES = Path(__file__).resolve().parent / "templates"

env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=False)
STYLE = (TEMPLATES / "_style.css").read_text()

STAT_ROWS = [
    ("possessionPct", "Possession"),
    ("totalShots", "Shots"),
    ("shotsOnTarget", "On Target"),
    ("wonCorners", "Corners"),
    ("foulsCommitted", "Fouls"),
    ("offsides", "Offsides"),
    ("saves", "Saves"),
    ("yellowCards", "Yellows"),
    ("redCards", "Reds"),
]


def parse_minute(s):
    m = re.match(r"(\d+)", str(s))
    return int(m.group(1)) if m else None


def fmt_day(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return d.strftime("%a · %b %-d")


# ------------------------------------------------------------------ SVGs

def xg_race_svg(m, shots):
    """Cumulative xG step chart over match minutes, goals marked."""
    w, h = 660, 240
    ml, mr, mt, mb = 34, 14, 14, 26
    pw, ph = w - ml - mr, h - mt - mb

    series = {m["team1"]: [], m["team2"]: []}
    for s in sorted(shots, key=lambda s: s.get("seconds") or 0):
        minute = parse_minute(s["minute"]) or 0
        if s["team"] in series:
            series[s["team"]].append((minute, s["xg"], s["goal"], s.get("player")))
    if not any(series.values()):
        return None

    max_min = max(95, max(pt[0] for pts in series.values() for pt in pts) + 3)
    max_xg = max(0.5, max(sum(p[1] for p in pts) for pts in series.values()) * 1.15)

    def X(minute):
        return ml + pw * minute / max_min

    def Y(v):
        return mt + ph * (1 - v / max_xg)

    parts = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
             f'width="100%" role="img" aria-label="Cumulative expected goals">']
    # gridlines
    step = 0.5 if max_xg <= 2.5 else 1.0
    v = step
    while v < max_xg:
        parts.append(f'<line x1="{ml}" y1="{Y(v):.1f}" x2="{w - mr}" y2="{Y(v):.1f}" '
                     f'stroke="#f0f0f0" stroke-width="1"/>')
        parts.append(f'<text x="{ml - 6}" y="{Y(v) + 3:.1f}" font-size="9" '
                     f'font-family="Manrope,sans-serif" fill="#bbb" '
                     f'text-anchor="end">{v:g}</text>')
        v += step
    for t in range(0, max_min, 15):
        parts.append(f'<text x="{X(t):.1f}" y="{h - 8}" font-size="9" '
                     f'font-family="Manrope,sans-serif" fill="#bbb" '
                     f'text-anchor="middle">{t}&#8242;</text>')
    parts.append(f'<line x1="{ml}" y1="{Y(0):.1f}" x2="{w - mr}" y2="{Y(0):.1f}" '
                 f'stroke="#ddd" stroke-width="1"/>')

    for team, color in ((m["team1"], "#0a0a0a"), (m["team2"], "#b5b5b5")):
        pts = series[team]
        cum = 0.0
        path = [f"M {ml} {Y(0):.1f}"]
        markers = []
        for minute, xg, goal, player in pts:
            path.append(f"L {X(minute):.1f} {Y(cum):.1f}")
            cum += xg
            path.append(f"L {X(minute):.1f} {Y(cum):.1f}")
            if goal:
                markers.append((X(minute), Y(cum), player, minute))
        path.append(f"L {w - mr} {Y(cum):.1f}")
        parts.append(f'<path d="{" ".join(path)}" fill="none" stroke="{color}" '
                     f'stroke-width="2.2" stroke-linejoin="round"/>')
        parts.append(f'<text x="{w - mr}" y="{Y(cum) - 6:.1f}" font-size="10" '
                     f'font-weight="700" font-family="Manrope,sans-serif" fill="{color}" '
                     f'text-anchor="end">{cum:.2f}</text>')
        for gx, gy, player, minute in markers:
            parts.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="5" fill="{color}" '
                         f'stroke="#fff" stroke-width="1.5"/>')
            label = f"{player} {minute}&#8242;" if player else f"{minute}&#8242;"
            parts.append(f'<text x="{gx:.1f}" y="{gy - 10:.1f}" font-size="9.5" '
                         f'font-weight="700" font-family="Manrope,sans-serif" '
                         f'fill="#0a0a0a" text-anchor="middle">{label}</text>')
    parts.append("</svg>")
    return "".join(parts)


def star_path(cx, cy, r):
    import math
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


def shotmap_svg(m, shots):
    """Full pitch, team1 attacking right, team2 attacking left.
    Dot size ~ xG, star = goal, white fill = team2."""
    if not shots:
        return None
    w, h = 660, 420
    mx, my = 10, 10
    pw, ph = w - 2 * mx, h - 2 * my

    def px(xpct):
        return mx + pw * xpct / 100

    def py(ypct):
        return my + ph * ypct / 100

    P = []  # pitch furniture
    line = 'stroke="#d8d8d8" stroke-width="1.5" fill="none"'
    P.append(f'<rect x="{mx}" y="{my}" width="{pw}" height="{ph}" rx="6" {line}/>')
    P.append(f'<line x1="{px(50):.0f}" y1="{my}" x2="{px(50):.0f}" y2="{my + ph}" {line}/>')
    P.append(f'<circle cx="{px(50):.0f}" cy="{py(50):.0f}" r="{ph * 0.13:.0f}" {line}/>')
    for side in (0, 1):
        bx = px(0) if side == 0 else px(100 - 16.5)
        P.append(f'<rect x="{bx:.0f}" y="{py(21):.0f}" width="{pw * 0.165:.0f}" '
                 f'height="{ph * 0.58:.0f}" {line}/>')
        sx = px(0) if side == 0 else px(100 - 5.5)
        P.append(f'<rect x="{sx:.0f}" y="{py(36):.0f}" width="{pw * 0.055:.0f}" '
                 f'height="{ph * 0.28:.0f}" {line}/>')

    dots = []
    for s in shots:
        if s["team"] == m["team1"]:        # attacking right
            x, y = s["x"], s["y"]
            fill, stroke = "#0a0a0a", "#0a0a0a"
        elif s["team"] == m["team2"]:      # attacking left (mirror)
            x, y = 100 - s["x"], 100 - s["y"]
            fill, stroke = "#fff", "#0a0a0a"
        else:
            continue
        cx, cy = px(x), py(y)
        r = 4 + s["xg"] * 13
        title = (f"{s.get('player') or '?'} · {s['minute']}&#8242; · "
                 f"xG {s['xg']:.2f} · {s['type']}")
        if s["goal"]:
            dots.append(f'<path d="{star_path(cx, cy, r + 4)}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="1.5">'
                        f'<title>{title}</title></path>')
        else:
            opacity = "1" if "On Target" in s["type"] else "0.45"
            dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="1.3" opacity="{opacity}">'
                        f'<title>{title}</title></circle>')

    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'width="100%" role="img" aria-label="Shot map">'
            + "".join(P) + "".join(dots) + "</svg>")


def prediction_svg(m, pred):
    """Rounded stacked probability bar with a marker over the actual outcome."""
    w, h = 660, 64
    x0, bw, y0, bh = 4, 652, 26, 26
    actual = outcome(m)
    segs = [(pred["p1"], m["team1"], "#0a0a0a", "#fff"),
            (pred["pd"], "draw", "#d9d9d9", "#555"),
            (pred["p2"], m["team2"], "#f1f1f1", "#555")]
    parts = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
             f'width="100%" role="img" aria-label="Pre-match win probabilities">',
             f'<defs><clipPath id="rnd"><rect x="{x0}" y="{y0}" width="{bw}" '
             f'height="{bh}" rx="13"/></clipPath></defs>',
             f'<g clip-path="url(#rnd)">']
    cx = x0
    marker = None
    for i, (p, label, bg, fg) in enumerate(segs):
        sw = bw * p
        parts.append(f'<rect x="{cx:.1f}" y="{y0}" width="{sw:.1f}" height="{bh}" fill="{bg}"/>')
        if sw > 80:
            parts.append(f'<text x="{cx + sw / 2:.1f}" y="{y0 + 17}" font-size="11" '
                         f'font-weight="700" font-family="Manrope,sans-serif" fill="{fg}" '
                         f'text-anchor="middle">{label} {p * 100:.0f}%</text>')
        if i == actual:
            marker = cx + sw / 2
        cx += sw
    parts.append("</g>")
    for i in range(1, 3):  # segment dividers
        bx = x0 + bw * sum(s[0] for s in segs[:i])
        parts.append(f'<line x1="{bx:.1f}" y1="{y0}" x2="{bx:.1f}" y2="{y0 + bh}" '
                     f'stroke="#fff" stroke-width="2"/>')
    if marker is not None:
        parts.append(f'<path d="M{marker:.1f},{y0 - 3} l-5,-9 l10,0 Z" fill="#0a0a0a"/>')
        parts.append(f'<text x="{marker:.1f}" y="{y0 - 16}" font-size="9.5" font-weight="800" '
                     f'font-family="Manrope,sans-serif" fill="#0a0a0a" '
                     f'text-anchor="middle">ACTUAL</text>')
    parts.append("</svg>")
    return "".join(parts)


# ------------------------------------------------------------- content

def scorer_lines(m):
    lines = []
    for side, team in (("goals1", "team1"), ("goals2", "team2")):
        gs = m.get(side, [])
        if gs:
            joined = ", ".join(
                f"{g.get('name', '?')} {g.get('minute', '?')}&#8242;"
                + (" (o.g.)" if g.get("owngoal") else "")
                + (" (pen.)" if g.get("penalty") else "")
                for g in gs)
            lines.append(f"<strong>{m[team]}</strong> {joined}")
    return lines


def narrative(m, info, stats, xg1, xg2):
    g1, g2 = final_score(m)
    res = outcome(m)
    winner = m["team1"] if res == 0 else m["team2"] if res == 2 else None
    loser = m["team2"] if res == 0 else m["team1"] if res == 2 else None
    how = {"pen": " on penalties", "et": " after extra time"}.get(decided_on(m), "")
    sentences = []

    pred = info["prediction"] if info else None
    if pred and winner:
        wp = pred["p1"] if winner == m["team1"] else pred["p2"]
        if wp < 0.30:
            sentences.append(f"A genuine shock — the model gave {winner} just "
                             f"{wp * 100:.0f}% before kick-off, and they beat "
                             f"{loser}{how} anyway.")
        elif wp < 0.5:
            sentences.append(f"A mild upset: {winner} ({wp * 100:.0f}% pre-match) "
                             f"got past {loser}{how}.")
        elif abs(g1 - g2) >= 3:
            sentences.append(f"{winner} made a statement — a {max(g1,g2)}–{min(g1,g2)} "
                             f"dismantling of {loser}.")
        else:
            sentences.append(f"The favourite delivered: {winner} ({wp * 100:.0f}% pre-match) "
                             f"beat {loser} {max(g1, g2)}–{min(g1, g2)}{how}.")
    elif pred:
        sentences.append(f"A {g1}–{g2} draw — the model had that at {pred['pd'] * 100:.0f}%.")

    if xg1 is not None and xg2 is not None and winner:
        wxg = xg1 if winner == m["team1"] else xg2
        lxg = xg2 if winner == m["team1"] else xg1
        if wxg > lxg * 3 and lxg < 0.7:
            sentences.append(f"The xG race ({wxg:.2f} vs {lxg:.2f}) says it was as "
                             f"one-sided as the scoreline suggests.")
        elif lxg > wxg:
            sentences.append(f"The xG race tells a different story though: {loser} created "
                             f"more ({lxg:.2f} vs {wxg:.2f}) and will feel hard done by.")

    minutes = [parse_minute(g.get("minute")) for g in m.get("goals1", []) + m.get("goals2", [])]
    minutes = [x for x in minutes if x is not None]
    if minutes and max(minutes) >= 85:
        sentences.append(f"The decisive moment came late, in the {max(minutes)}th minute.")

    if stats:
        try:
            s1 = stats["teams"][0]["stats"]
            s2 = stats["teams"][1]["stats"]
            reds = int(s1.get("redCards") or 0) + int(s2.get("redCards") or 0)
            if reds:
                sentences.append(f"Tempers frayed — {reds} red card{'s' if reds > 1 else ''} shown.")
        except (KeyError, IndexError, ValueError):
            pass

    return " ".join(sentences)


def build_stat_rows(m, stats):
    if not stats or len(stats.get("teams", [])) != 2:
        return []
    s1, s2 = stats["teams"][0]["stats"], stats["teams"][1]["stats"]
    rows = []
    for key, label in STAT_ROWS:
        v1, v2 = s1.get(key), s2.get(key)
        if v1 is None or v2 is None:
            continue
        try:
            f1, f2 = float(v1), float(v2)
        except ValueError:
            continue
        total = f1 + f2
        w1 = 100 * f1 / total if total else 0
        rows.append({"label": label, "v1": v1, "v2": v2,
                     "w1": round(w1, 1), "w2": round(100 - w1, 1)})
    return rows


TIMELINE_TAGS = [
    ("goal", "GOAL", True),
    ("penalty - scored", "PEN GOAL", True),
    ("own goal", "OWN GOAL", True),
    ("yellow card", "YELLOW", False),
    ("red card", "RED", False),
    ("penalty - missed", "PEN MISS", False),
    ("penalty - saved", "PEN SAVED", False),
    ("substitution", "SUB", False),
]


def build_timeline(stats):
    if not stats:
        return []
    out = []
    for ev in stats.get("events", []):
        typ = ev.get("type", "").lower()
        for needle, tag, is_goal in TIMELINE_TAGS:
            if needle in typ:
                text = ev.get("text") or " / ".join(p for p in ev.get("players", []) if p)
                out.append({"minute": ev.get("minute", ""), "tag": tag,
                            "is_goal": is_goal, "text": text})
                break
    return out


def subs_used(lineup, stats):
    if not stats:
        return []
    on = []
    for ev in stats.get("events", []):
        if "substitution" in ev.get("type", "").lower() and ev.get("team") and lineup.get("team"):
            if ev["team"] == lineup["team"] and ev.get("players"):
                on.append(ev["players"][0])
    return on


# --------------------------------------------------------------- bracket

KO_ROUNDS = ["Round of 32", "Round of 16", "Quarter-final",
             "Semi-final", "Final"]
KO_LABELS = {
    "Round of 32": "Round of 32", "Round of 16": "Round of 16",
    "Quarter-final": "Quarter-finals", "Semi-final": "Semi-finals",
    "Final": "Final",
}
REF_RE = re.compile(r"^([WL])(\d+)$")

# Fixed bracket topology by match number (openfootball's 2026 schedule order):
# match -> the two earlier matches whose winners feed it. This is a constant of
# the tournament, so the tree survives openfootball resolving "Winner 74" slots
# into real team names as games are played (which would otherwise break a
# ref-parsing traversal). 73-88 = R32, 89-96 = R16, 97-100 = QF, 101-102 = SF,
# 103 = third place, 104 = Final.
KO_FEEDERS = {
    89: (74, 77), 90: (73, 75), 91: (76, 78), 92: (79, 80),
    93: (83, 84), 94: (81, 82), 95: (86, 88), 96: (85, 87),
    97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96),
    101: (97, 98), 102: (99, 100),
    104: (101, 102), 103: (101, 102),
}


def build_bracket(matches, pages):
    """Knockout tree, ordered top-to-bottom, with each slot resolved to a
    real team where the feeding match is decided. Slots stay as placeholders
    (group codes like '2A', or 'Winner 74') until the result is known."""
    ko = {m["num"]: m for m in matches if not m.get("group") and m.get("round")}
    if not ko:
        return None
    real_teams = {t for m in matches if m.get("group")
                  for t in (m["team1"], m["team2"])}

    def parse_ref(slot):
        mm = REF_RE.match(slot.strip())
        return (mm.group(1), int(mm.group(2))) if mm else None

    def ko_result(num):
        """(winner, loser) names if match `num` is decided, else None."""
        m = ko.get(num)
        if not m or not m.get("score"):
            return None
        s1, s2 = resolve_name(m["team1"]), resolve_name(m["team2"])
        if not s1 or not s2:
            return None
        res = outcome(m)
        if res == 1:
            return None  # level, shootout result not in the data yet
        return (s1, s2) if res == 0 else (s2, s1)

    def resolve_name(slot):
        if slot in real_teams:
            return slot
        ref = parse_ref(slot)
        if ref:
            o = ko_result(ref[1])
            if o:
                return o[0] if ref[0] == "W" else o[1]
        return None

    def side(slot):
        name = resolve_name(slot)
        if name:
            return {"name": name, "placeholder": False}
        ref = parse_ref(slot)
        label = (f"Winner {ref[1]}" if ref and ref[0] == "W"
                 else f"Loser {ref[1]}" if ref else slot)
        return {"name": label, "placeholder": True}

    def tie(m):
        win1 = win2 = False
        score = note = None
        if m.get("score"):
            res = outcome(m)
            win1, win2 = res == 0, res == 2
            score = final_score(m)
            how = decided_on(m)
            if how == "pen":
                note = "{}–{} pens".format(*m["score"]["p"])
            elif how == "et":
                note = "aet"
        return {
            "num": m["num"],
            "s1": side(m["team1"]), "s2": side(m["team2"]),
            "win1": win1, "win2": win2,
            "score": score, "note": note,
            "has_page": m["num"] in pages, "slug": m["slug"],
            "when": datetime.strptime(m["date"], "%Y-%m-%d").strftime("%b %-d"),
        }

    # in-order traversal from the final over the fixed topology, so each round
    # lists ties top-to-bottom and the pairs align with the next round.
    cols = {r: [] for r in KO_ROUNDS}

    def visit(num):
        if num not in ko:
            return
        kids = KO_FEEDERS.get(num)
        if kids:
            visit(kids[0])
        if ko[num]["round"] in cols:
            cols[ko[num]["round"]].append(tie(ko[num]))
        if kids:
            visit(kids[1])

    final = next((m for m in ko.values() if m["round"] == "Final"), None)
    if final:
        visit(final["num"])

    columns = []
    for r in KO_ROUNDS:
        ties = cols[r]
        if not ties:
            continue
        pairs = [ties[i:i + 2] for i in range(0, len(ties), 2)] if r != "Final" else None
        columns.append({"label": KO_LABELS[r], "ties": ties, "pairs": pairs})

    third = next((tie(m) for m in ko.values()
                  if m["round"] == "Match for third place"), None)
    return {"columns": columns, "third": third}


# ----------------------------------------------------------------- main

def main():
    matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]
    analytics = json.loads((DATA_DIR / "analytics.json").read_text())
    per_match = analytics["per_match"]
    today = date.today().isoformat()

    def stats_for(m):
        p = STATS_DIR / f"{m.get('espn_id')}.json"
        return json.loads(p.read_text()) if m.get("espn_id") and p.exists() else None

    # ---- match pages
    (ROOT / "matches").mkdir(exist_ok=True)
    tpl = env.get_template("match.html.j2")
    pages = set()
    for m in matches:
        if m["status"] != "finished" or not m.get("score"):
            continue
        stats = stats_for(m)
        if not stats:
            continue
        info = per_match.get(str(m["num"]))
        pred = info["prediction"] if info else None
        shots = stats.get("shots", [])

        # map ESPN team names back to openfootball ones for the charts
        espn_names = {t["name"] for t in stats.get("teams", [])}
        name_fix = {}
        for en in espn_names:
            if en not in (m["team1"], m["team2"]):
                target = m["team1"] if any(
                    w in en for w in m["team1"].split()) else m["team2"]
                name_fix[en] = target
        for s in shots:
            s["team"] = name_fix.get(s["team"], s["team"])

        xg1 = round(sum(s["xg"] for s in shots if s["team"] == m["team1"]), 2) if shots else None
        xg2 = round(sum(s["xg"] for s in shots if s["team"] == m["team2"]), 2) if shots else None

        res = outcome(m)
        actual_p = (pred["p1"] if res == 0 else pred["pd"] if res == 1 else pred["p2"]) if pred else None
        verdict = ""
        if actual_p is not None:
            verdict = ("The model called it." if actual_p >= 0.5 else
                       "Reality had other plans." if actual_p < 0.25 else
                       "A plausible-but-not-favoured outcome.")
        elo_direction = ""
        if info and info.get("elo_delta") is not None:
            gainer = m["team1"] if info["elo_delta"] > 0 else m["team2"]
            other = m["team2"] if info["elo_delta"] > 0 else m["team1"]
            elo_direction = f"from {other} to {gainer}"

        m["final1"], m["final2"] = final_score(m)
        note = []
        if m["score"].get("p"):
            note.append("PENS {}–{}".format(*m["score"]["p"]))
        if m["score"].get("et"):
            note.append("AET")
        if m["score"].get("ht"):
            note.append("HT {}–{}".format(*m["score"]["ht"]))
        m["score_note"] = " · ".join(note) or "FULL TIME"
        m["scorer_lines"] = scorer_lines(m)
        lineups = stats.get("lineups", [])
        for l in lineups:
            l["subs_used"] = subs_used(l, stats)

        html = tpl.render(
            style=STYLE, m=m, info=info, pred=pred, verdict=verdict,
            elo_direction=elo_direction,
            xg1=xg1, xg2=xg2,
            narrative=narrative(m, info, stats, xg1, xg2),
            xg_race_svg=xg_race_svg(m, shots) if shots else None,
            shotmap_svg=shotmap_svg(m, shots) if shots else None,
            pred_svg=prediction_svg(m, pred) if pred else None,
            stat_rows=build_stat_rows(m, stats),
            timeline=build_timeline(stats),
            lineups=lineups,
        )
        (ROOT / "matches" / f"{m['slug']}.html").write_text(html)
        pages.add(m["num"])
    print(f"wrote {len(pages)} match pages")

    # ---- fixtures hub
    by_day = {}
    for m in matches:
        m["has_page"] = m["num"] in pages
        if m.get("score"):
            res = outcome(m)
            m["win1"], m["win2"] = res == 0, res == 2
            m["final1"], m["final2"] = final_score(m)
            m["chip"] = {"pen": "PENS", "et": "AET"}.get(decided_on(m), "FT")
        else:
            m["win1"] = m["win2"] = False
        m["time_short"] = (m.get("time") or "").split(" ")[0]
        by_day.setdefault(m["date"], []).append(m)

    days = [{"label": fmt_day(d), "is_today": d == today, "matches": ms}
            for d, ms in sorted(by_day.items())]

    upcoming = []
    for m in sorted((x for x in matches if x["status"] != "finished"),
                    key=lambda x: (x["date"], x["num"]))[:8]:
        info = per_match.get(str(m["num"]))
        if info:
            m["pred"] = info["prediction"]
            upcoming.append(m)

    sims = analytics["sims"]
    bracket = build_bracket(matches, pages)
    html = env.get_template("index.html.j2").render(
        style=STYLE,
        n_sims=analytics["n_sims"],
        bracket=bracket,
        n_finished=sum(1 for m in matches if m["status"] == "finished"),
        days=days,
        standings=analytics["standings"],
        sims=sims,
        max_champ=max(s["champ"] for s in sims) or 1,
        upcoming=upcoming,
        upsets=analytics["upsets"],
        brier=analytics["brier"],
        n_scored=analytics["n_scored"],
        build_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
    (ROOT / "index.html").write_text(html)
    print(f"wrote {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
