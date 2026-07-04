"""Derived analytics for the World Cup 2026 page.

- Elo ratings: seeded from pre-tournament strength, replayed over results.
- Poisson goal model driven by Elo difference -> match predictions.
- Monte Carlo: 10,000 tournament simulations (group stage + knockout).
- Upset index, goal-timing histogram, group standings, top scorers,
  and model accountability (Brier score) for finished matches.

Output: worldcup/data/analytics.json
"""
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
N_SIMS = 10_000
K_FACTOR = 50  # World Cup weighting in the classic Elo scheme

# Pre-tournament Elo seeds (approximate World Football Elo, June 2026).
# Deliberately a one-off snapshot: ratings self-correct as results come in.
ELO_SEEDS = {
    "Argentina": 2120, "Spain": 2100, "France": 2050, "England": 2040,
    "Brazil": 2020, "Portugal": 2010, "Netherlands": 1990, "Germany": 1960,
    "Belgium": 1950, "Croatia": 1930, "Morocco": 1920, "Uruguay": 1900,
    "Colombia": 1900, "Japan": 1880, "Mexico": 1860, "Ecuador": 1860,
    "Switzerland": 1850, "Turkey": 1850, "Norway": 1850, "USA": 1840,
    "Senegal": 1840, "Austria": 1830, "Iran": 1820, "South Korea": 1820,
    "Sweden": 1800, "Canada": 1790, "Egypt": 1790, "Algeria": 1780,
    "Ivory Coast": 1780, "Paraguay": 1780, "Australia": 1780,
    "Czech Republic": 1770, "Scotland": 1760, "Tunisia": 1760,
    "Bosnia & Herzegovina": 1760, "Ghana": 1750, "Panama": 1730,
    "South Africa": 1720, "Saudi Arabia": 1700, "Uzbekistan": 1700,
    "DR Congo": 1700, "Qatar": 1680, "New Zealand": 1670, "Jordan": 1670,
    "Iraq": 1660, "Cape Verde": 1650, "Curaçao": 1640, "Haiti": 1600,
}

# Host nations get a modest home-Elo bonus when playing in their own country.
HOST_CITIES = {
    "Mexico": ["Mexico City", "Guadalajara", "Monterrey"],
    "Canada": ["Toronto", "Vancouver"],
    "USA": ["Atlanta", "Boston", "Dallas", "Houston", "Kansas City",
            "Los Angeles", "Miami", "New York", "Philadelphia",
            "San Francisco", "Seattle"],
}
HOME_BONUS = 50


def host_country(ground):
    for country, cities in HOST_CITIES.items():
        if any(ground.startswith(c) for c in cities):
            return country
    return None


def effective_elos(elo, m):
    """Elo pair for a match, with home bonus for a host playing at home."""
    e1, e2 = elo[m["team1"]], elo[m["team2"]]
    home = host_country(m.get("ground", ""))
    if home == m["team1"]:
        e1 += HOME_BONUS
    elif home == m["team2"]:
        e2 += HOME_BONUS
    return e1, e2


def poisson_lambdas(e1, e2):
    """Expected goals per side from the Elo difference."""
    diff = e1 - e2
    lam1 = min(max(1.35 * 10 ** (diff / 1050), 0.2), 4.5)
    lam2 = min(max(1.35 * 10 ** (-diff / 1050), 0.2), 4.5)
    return lam1, lam2


def poisson_pmf(lam, kmax=8):
    return [math.exp(-lam) * lam**k / math.factorial(k) for k in range(kmax + 1)]


def predict(e1, e2):
    """Win/draw/win probabilities and most likely score from the Poisson grid."""
    lam1, lam2 = poisson_lambdas(e1, e2)
    p1, p2 = poisson_pmf(lam1), poisson_pmf(lam2)
    w1 = d = w2 = 0.0
    best, best_p = (0, 0), 0.0
    for a, pa in enumerate(p1):
        for b, pb in enumerate(p2):
            p = pa * pb
            if a > b:
                w1 += p
            elif a == b:
                d += p
            else:
                w2 += p
            if p > best_p:
                best, best_p = (a, b), p
    return {"p1": round(w1, 4), "pd": round(d, 4), "p2": round(w2, 4),
            "score": list(best), "lambdas": [round(lam1, 2), round(lam2, 2)]}


def sample_poisson(lam):
    l, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= random.random()
        if p <= l:
            return k
        k += 1


def elo_update(e1, e2, g1, g2):
    we = 1 / (1 + 10 ** ((e2 - e1) / 400))
    w = 1.0 if g1 > g2 else 0.5 if g1 == g2 else 0.0
    margin = abs(g1 - g2)
    g = 1.0 if margin <= 1 else 1.5 if margin == 2 else (11 + margin) / 8
    delta = K_FACTOR * g * (w - we)
    return delta, we


def final_score(m):
    """Decisive goal tally: after extra time when it was played, else 90'."""
    s = m["score"]
    return s.get("et") or s["ft"]


def decided_on(m):
    """How the match was settled: "ft", "et" or "pen"."""
    s = m["score"]
    return "pen" if s.get("p") else "et" if s.get("et") else "ft"


def outcome(m):
    """0 = team1 won, 1 = draw, 2 = team2 won — extra time and pens included."""
    s = m["score"]
    if s.get("p"):
        p1, p2 = s["p"]
        return 0 if p1 > p2 else 2
    g1, g2 = final_score(m)
    return 0 if g1 > g2 else 2 if g2 > g1 else 1


# ---------------------------------------------------------------- replay

def replay_elo(matches):
    """Replay finished matches chronologically. Returns current ratings,
    per-match pre-game ratings/predictions, and per-team rating history."""
    elo = dict(ELO_SEEDS)
    history = {t: [r] for t, r in elo.items()}
    per_match = {}

    finished = [m for m in matches if m["status"] == "finished" and m.get("score")]
    finished.sort(key=lambda m: (m["date"], m["num"]))

    for m in finished:
        e1, e2 = effective_elos(elo, m)
        pred = predict(e1, e2)
        g1, g2 = final_score(m)
        if m["score"].get("p"):  # shootout winner rated as a one-goal win
            p1, p2 = m["score"]["p"]
            g1, g2 = (g1 + 1, g2) if p1 > p2 else (g1, g2 + 1)
        delta, _ = elo_update(e1, e2, g1, g2)
        per_match[m["num"]] = {
            "prediction": pred,
            "elo_before": [round(elo[m["team1"]]), round(elo[m["team2"]])],
            "elo_delta": round(delta, 1),
        }
        elo[m["team1"]] += delta
        elo[m["team2"]] -= delta
        history[m["team1"]].append(round(elo[m["team1"]]))
        history[m["team2"]].append(round(elo[m["team2"]]))

    return elo, per_match, history


# ---------------------------------------------------------------- groups

def table_from_results(results, teams):
    """results: list of (team1, team2, g1, g2). Standard 3/1/0 table."""
    rows = {t: {"team": t, "p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0}
            for t in teams}
    for t1, t2, g1, g2 in results:
        r1, r2 = rows[t1], rows[t2]
        r1["p"] += 1; r2["p"] += 1
        r1["gf"] += g1; r1["ga"] += g2
        r2["gf"] += g2; r2["ga"] += g1
        if g1 > g2:
            r1["w"] += 1; r1["pts"] += 3; r2["l"] += 1
        elif g1 < g2:
            r2["w"] += 1; r2["pts"] += 3; r1["l"] += 1
        else:
            r1["d"] += 1; r2["d"] += 1; r1["pts"] += 1; r2["pts"] += 1
    out = sorted(rows.values(),
                 key=lambda r: (-r["pts"], -(r["gf"] - r["ga"]), -r["gf"], r["team"]))
    for r in out:
        r["gd"] = r["gf"] - r["ga"]
    return out


def group_fixtures(matches):
    groups = defaultdict(list)
    for m in matches:
        if m.get("group"):
            groups[m["group"]].append(m)
    return dict(sorted(groups.items()))


# ------------------------------------------------------------ simulation

def simulate_tournament(matches, elo):
    """One tournament simulation from the current state. Returns the round
    reached per team: g=group exit, r32, r16, qf, sf, f, champ, third."""
    groups = group_fixtures(matches)
    group_results = defaultdict(list)
    for m in matches:
        if m.get("group") and m["status"] == "finished":
            g1, g2 = m["score"]["ft"]
            group_results[m["group"]].append((m["team1"], m["team2"], g1, g2))

    for gname, ms in groups.items():
        for m in ms:
            if m["status"] != "finished":
                e1, e2 = effective_elos(elo, m)
                lam1, lam2 = poisson_lambdas(e1, e2)
                group_results[gname].append(
                    (m["team1"], m["team2"], sample_poisson(lam1), sample_poisson(lam2)))

    winners, runners, thirds = {}, {}, []
    for gname, ms in groups.items():
        teams = sorted({m["team1"] for m in ms} | {m["team2"] for m in ms})
        # random jitter as a stand-in for fair-play/drawing-of-lots tiebreaks
        table = table_from_results(group_results[gname], teams)
        winners[gname] = table[0]["team"]
        runners[gname] = table[1]["team"]
        t3 = table[2]
        thirds.append((t3["pts"], t3["gd"], t3["gf"], random.random(), t3["team"]))

    thirds.sort(reverse=True)
    best_thirds = [t[-1] for t in thirds[:8]]

    # Approximate Round-of-32 bracket: same shape as the official one
    # (8x winner-vs-third, 4x winner-vs-runner-up, 4x runner-up pairs,
    # same-group clashes avoided), without FIFA's exact slotting tables.
    gnames = list(groups.keys())  # A..L
    w = [winners[g] for g in gnames]
    ru = [runners[g] for g in gnames]
    random.shuffle(best_thirds)
    r32 = []
    for i in range(8):
        r32.append((w[i], best_thirds[i]))
    r32.append((w[8], ru[9]))
    r32.append((w[9], ru[8]))
    r32.append((w[10], ru[11]))
    r32.append((w[11], ru[10]))
    r32.append((ru[0], ru[3]))
    r32.append((ru[1], ru[2]))
    r32.append((ru[4], ru[7]))
    r32.append((ru[5], ru[6]))

    reached = {t: "g" for g in gnames
               for t in [winners[g], runners[g]]}
    for t in best_thirds:
        reached[t] = "r32"
    for g in gnames:
        reached[winners[g]] = "r32"
        reached[runners[g]] = "r32"

    def play_knockout(t1, t2):
        lam1, lam2 = poisson_lambdas(elo[t1], elo[t2])
        g1, g2 = sample_poisson(lam1), sample_poisson(lam2)
        if g1 == g2:  # extra time, then effectively penalties
            g1 += sample_poisson(lam1 / 3)
            g2 += sample_poisson(lam2 / 3)
            if g1 == g2:
                return (t1, t2) if random.random() < 0.5 else (t2, t1)
        return (t1, t2) if g1 > g2 else (t2, t1)

    stage_names = ["r16", "qf", "sf", "f", "champ"]
    field = r32
    for stage in stage_names:
        nxt = []
        for i in range(0, len(field), 2):
            win1, lose1 = play_knockout(*field[i])
            if stage == "champ":
                reached[win1] = "champ"
                reached[lose1] = "f"
                continue
            win2, lose2 = play_knockout(*field[i + 1])
            reached[win1] = stage
            reached[win2] = stage
            nxt.append((win1, win2))
        field = nxt
        if stage == "f":
            # field is [(finalist, finalist)]; last loop iteration handles it
            pass
    return reached


def run_simulations(matches, elo):
    order = ["g", "r32", "r16", "qf", "sf", "f", "champ"]
    rank = {s: i for i, s in enumerate(order)}
    counts = defaultdict(lambda: defaultdict(int))
    for _ in range(N_SIMS):
        reached = simulate_tournament(matches, elo)
        for team, stage in reached.items():
            # team reached `stage` and everything before it
            for s in order[1:rank[stage] + 1]:
                counts[team][s] += 1
            counts[team]["champ_only"] += stage == "champ"
    out = []
    for team in ELO_SEEDS:
        c = counts[team]
        out.append({
            "team": team,
            "r32": round(c["r32"] / N_SIMS, 4),
            "r16": round(c["r16"] / N_SIMS, 4),
            "qf": round(c["qf"] / N_SIMS, 4),
            "sf": round(c["sf"] / N_SIMS, 4),
            "f": round(c["f"] / N_SIMS, 4),
            "champ": round(c["champ"] / N_SIMS, 4),
        })
    out.sort(key=lambda r: -r["champ"])
    return out


# ------------------------------------------------------------- the rest

MINUTE_RE = re.compile(r"(\d+)")


def parse_minute(s):
    m = MINUTE_RE.match(str(s))
    return int(m.group(1)) if m else None


def goal_timing(matches):
    buckets = [0] * 6  # 1-15, 16-30, 31-45+, 46-60, 61-75, 76-90+
    for m in matches:
        if m["status"] != "finished":
            continue
        for g in m.get("goals1", []) + m.get("goals2", []):
            minute = parse_minute(g.get("minute", ""))
            if minute is None:
                continue
            idx = min((minute - 1) // 15, 5)
            buckets[idx] += 1
    return buckets


def top_scorers(matches):
    tally = defaultdict(lambda: {"goals": 0, "team": ""})
    for m in matches:
        if m["status"] != "finished":
            continue
        for side, team in (("goals1", m["team1"]), ("goals2", m["team2"])):
            for g in m.get(side, []):
                name = g.get("name")
                if not name or g.get("owngoal"):
                    continue
                tally[name]["goals"] += 1
                tally[name]["team"] = team
    out = [{"name": n, **v} for n, v in tally.items()]
    out.sort(key=lambda r: (-r["goals"], r["name"]))
    return out[:10]


def upsets_and_brier(matches, per_match):
    upsets, brier_terms = [], []
    for m in matches:
        info = per_match.get(m["num"])
        if not info or m["status"] != "finished" or not m.get("score"):
            continue
        pred = info["prediction"]
        g1, g2 = m["score"]["ft"]  # the model prices the 90-minute result
        actual = [int(g1 > g2), int(g1 == g2), int(g1 < g2)]
        probs = [pred["p1"], pred["pd"], pred["p2"]]
        brier_terms.append(sum((p - a) ** 2 for p, a in zip(probs, actual)))
        res = outcome(m)  # but an upset is about who actually went through
        winner_prob = probs[0] if res == 0 else probs[2] if res == 2 else None
        if winner_prob is not None and winner_prob < 0.5:
            winner = m["team1"] if res == 0 else m["team2"]
            loser = m["team2"] if res == 0 else m["team1"]
            f1, f2 = final_score(m)
            how = decided_on(m)
            upsets.append({
                "num": m["num"], "slug": m["slug"], "date": m["date"],
                "winner": winner, "loser": loser,
                "score": f"{f1}–{f2}" + (" (pens)" if how == "pen"
                                         else " (aet)" if how == "et" else ""),
                "win_prob": round(winner_prob, 3),
            })
    upsets.sort(key=lambda u: u["win_prob"])
    brier = round(sum(brier_terms) / len(brier_terms), 4) if brier_terms else None
    return upsets, brier, len(brier_terms)


def standings(matches):
    out = {}
    for gname, ms in group_fixtures(matches).items():
        teams = sorted({m["team1"] for m in ms} | {m["team2"] for m in ms})
        results = [(m["team1"], m["team2"], *m["score"]["ft"])
                   for m in ms if m["status"] == "finished"]
        out[gname] = table_from_results(results, teams)
    return out


def main():
    random.seed(2026)  # reproducible builds: same inputs -> same page
    matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]

    elo, per_match, history = replay_elo(matches)

    # predictions for upcoming matches use current ratings
    for m in matches:
        if m["num"] not in per_match and m.get("group"):
            e1, e2 = effective_elos(elo, m)
            per_match[m["num"]] = {"prediction": predict(e1, e2),
                                   "elo_before": [round(e1), round(e2)],
                                   "elo_delta": None}

    sims = run_simulations(matches, elo)
    upsets, brier, n_scored = upsets_and_brier(matches, per_match)

    elo_table = sorted(
        ({"team": t, "elo": round(r), "delta": round(r - ELO_SEEDS[t])}
         for t, r in elo.items()),
        key=lambda x: -x["elo"])

    out = {
        "elo": elo_table,
        "elo_history": history,
        "per_match": {str(k): v for k, v in per_match.items()},
        "sims": sims,
        "n_sims": N_SIMS,
        "upsets": upsets,
        "brier": brier,
        "n_scored": n_scored,
        "goal_timing": goal_timing(matches),
        "top_scorers": top_scorers(matches),
        "standings": standings(matches),
    }
    path = DATA_DIR / "analytics.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"wrote {path}")
    print("model: brier", brier, "over", n_scored, "matches")
    print("top 5 title odds:",
          [(s['team'], s['champ']) for s in sims[:5]])


if __name__ == "__main__":
    main()
