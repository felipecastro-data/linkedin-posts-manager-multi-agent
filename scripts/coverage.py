"""Pillar and lens coverage, plus the posting slots in the horizon.

Usage: python3 scripts/coverage.py runs/<id>/sheet.json runs/<id>/coverage.json [--today YYYY-MM-DD]
"""

import argparse
from collections import Counter

from common import load_config, next_saturdays, read_json, today_from_arg, write_json


def counts(rows, key, names):
    c = Counter(r[key] for r in rows)
    return {n: c.get(n, 0) for n in names}


def last_used(rows, key, names):
    out = {n: None for n in names}
    for r in rows:
        if r["date"] and r[key] in out and (out[r[key]] is None or r["date"] > out[r[key]]):
            out[r[key]] = r["date"]
    return out


def summary_line(rows, pillars, lenses):
    """Compact text used in the Agent Runs tab."""
    pc = counts(rows, "pillar", pillars)
    lc = counts(rows, "lens", lenses)
    p = ", ".join(f"{k} {v}" for k, v in sorted(pc.items(), key=lambda x: -x[1]))
    l = ", ".join(f"{k} {v}" for k, v in sorted(lc.items(), key=lambda x: -x[1]))
    return f"Pillars: {p} | Lenses: {l}"


def build(sheet, cfg, today):
    st = cfg["status"]
    pillars, lenses = sheet["pillars"], sheet["lenses"]
    rows = sheet["schedule"]
    published = [r for r in rows if r["status"] in (st["posted"], st["scheduled"])]
    queued = [r for r in rows if r["status"] == st["queued"]]
    active = published + queued

    slots = []
    by_date = {}
    for r in active:
        if r["date"]:
            by_date.setdefault(r["date"], []).append(r)
    for d in next_saturdays(today, cfg["schedule"]["horizon_saturdays"], cfg["schedule"]["weekday"]):
        occupants = by_date.get(d.isoformat(), [])
        slots.append({
            "date": d.isoformat(),
            "rows": [{"row": r["row"], "status": r["status"], "pillar": r["pillar"], "lens": r["lens"]} for r in occupants],
            "fixed": any(r["status"] != st["queued"] for r in occupants),
        })
    horizon_end = slots[-1]["date"]

    return {
        "today": today.isoformat(),
        "horizon": {"start": slots[0]["date"], "end": horizon_end, "slots": slots},
        "published": {"pillar": counts(published, "pillar", pillars), "lens": counts(published, "lens", lenses)},
        "queued": {"pillar": counts(queued, "pillar", pillars), "lens": counts(queued, "lens", lenses)},
        "last_published": {"pillar": last_used(published, "pillar", pillars), "lens": last_used(published, "lens", lenses)},
        "never_used": {
            "pillar": [p for p in pillars if not any(r["pillar"] == p for r in active)],
            "lens": [l for l in lenses if not any(r["lens"] == l for r in active)],
        },
        "never_published": {
            "pillar": [p for p in pillars if not any(r["pillar"] == p for r in published)],
            "lens": [l for l in lenses if not any(r["lens"] == l for r in published)],
        },
        "pairs_used": sorted({f"{r['pillar']} x {r['lens']}" for r in active}),
        "backlog_beyond_horizon": [r["row"] for r in queued if r["date"] and r["date"] > horizon_end],
        "summary": summary_line(active, pillars, lenses),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("--today")
    a = ap.parse_args()
    cov = build(read_json(a.sheet), load_config(), today_from_arg(a.today))
    write_json(a.out, cov)
    open_slots = [s["date"] for s in cov["horizon"]["slots"] if not s["rows"]]
    print(f"horizon {cov['horizon']['start']}..{cov['horizon']['end']} open_slots={open_slots}")
    print(f"never used: pillars={cov['never_used']['pillar']} lenses={cov['never_used']['lens']}")


if __name__ == "__main__":
    main()
