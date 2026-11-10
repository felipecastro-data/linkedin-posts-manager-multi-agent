"""Check a Strategist proposal against the hard rules and build the diff.

Usage: python3 scripts/validate_proposal.py runs/<id>/sheet.json runs/<id>/proposal.json \
           runs/<id>/validation.json runs/<id>/diff.md [--today YYYY-MM-DD]

proposal.json is the full desired queue (every queued row kept, edited, moved
or added) plus the rows to drop. See .claude/agents/content-strategist.md.
Exit code 1 when there are errors.
"""

import argparse
import re
import sys
from datetime import date, timedelta

from common import load_config, next_saturdays, read_json, today_from_arg, write_json
from coverage import summary_line

COMPARISON = re.compile(r"\b(vs\.?|versus)\b", re.IGNORECASE)


def d(iso):
    return date.fromisoformat(iso)


def check(sheet, proposal, cfg, today):
    st, rot, ideas, shp = cfg["status"], cfg["rotation"], cfg["ideas"], cfg["shapes"]
    errors, warnings = [], []
    rows = {r["row"]: r for r in sheet["schedule"]}
    queued_rows = {r["row"] for r in sheet["schedule"] if r["status"] == st["queued"]}
    fixed = [r for r in sheet["schedule"] if r["status"] in (st["posted"], st["scheduled"]) and r["date"]]
    queue = proposal.get("queue", [])
    drops = proposal.get("drops", [])

    # Every queued row accounted for exactly once
    seen = [q["origin_row"] for q in queue if q.get("origin_row")] + [x["row"] for x in drops]
    for row in queued_rows:
        n = seen.count(row)
        if n == 0:
            errors.append(f"row {row} ({rows[row]['topic'][:50]}) is neither kept nor dropped")
        elif n > 1:
            errors.append(f"row {row} appears {n} times across queue and drops")
    for row in set(seen) - queued_rows:
        status = rows[row]["status"] if row in rows else "missing"
        errors.append(f"row {row} is not an editable queued row (status: {status})")

    # Names, text, dates
    fixed_dates = {r["date"] for r in fixed}
    dates = []
    for q in queue:
        label = f"{q.get('date')} '{(q.get('topic') or '')[:50]}'"
        if q.get("pillar") not in sheet["pillars"]:
            errors.append(f"{label}: unknown pillar '{q.get('pillar')}'")
        if q.get("lens") not in sheet["lenses"]:
            errors.append(f"{label}: unknown lens '{q.get('lens')}'")
        words = len((q.get("topic") or "").split())
        if words == 0 or words > ideas["topic_max_words"]:
            errors.append(f"{label}: topic has {words} words (max {ideas['topic_max_words']})")
        if ideas["require_test"] and not (q.get("test") or "").strip():
            errors.append(f"{label}: missing test")
        if not (q.get("rationale") or "").strip():
            errors.append(f"{label}: missing rationale")
        if q.get("shape") not in shp["names"]:
            errors.append(f"{label}: shape '{q.get('shape')}' is not one of {', '.join(shp['names'])}")
        try:
            qd = d(q["date"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{label}: invalid date")
            continue
        if qd.weekday() != cfg["schedule"]["weekday"]:
            errors.append(f"{label}: not a Saturday")
        if qd <= today:
            errors.append(f"{label}: date is not in the future")
        if q["date"] in fixed_dates:
            errors.append(f"{label}: date already taken by a posted/scheduled row")
        dates.append(q["date"])
    for x in sorted({x for x in dates if dates.count(x) > 1}):
        errors.append(f"{x}: more than one queued idea on this date")

    # Horizon fully covered
    taken = fixed_dates | set(dates)
    for s in next_saturdays(today, cfg["schedule"]["horizon_saturdays"], cfg["schedule"]["weekday"]):
        if s.isoformat() not in taken:
            errors.append(f"{s.isoformat()}: no post in the horizon slot")

    # Rotation over the combined timeline
    timeline = [{"date": d(r["date"]), "pillar": r["pillar"], "lens": r["lens"], "shape": r.get("shape") or None,
                 "queued": False, "topic": r["topic"]} for r in fixed]
    timeline += [{"date": d(q["date"]), "pillar": q.get("pillar"), "lens": q.get("lens"), "shape": q.get("shape"),
                  "queued": True, "topic": q.get("topic", "")} for q in queue if q.get("date")]
    timeline.sort(key=lambda e: e["date"])
    span = timedelta(weeks=rot["window_saturdays"] - 1)

    for key, on in (("pillar", rot["pillar_no_back_to_back"]), ("shape", shp["no_back_to_back"])):
        if not on:
            continue
        for a, b in zip(timeline, timeline[1:]):
            if (b["date"] - a["date"]).days == 7 and a[key] and a[key] == b[key] and (a["queued"] or b["queued"]):
                errors.append(f"{a['date']} and {b['date']}: {key} {a[key]} on back-to-back Saturdays")

    shape_span = timedelta(weeks=shp["window_saturdays"] - 1)
    for key, limit, win, weeks in (("pillar", rot["pillar_max_per_window"], span, rot["window_saturdays"]),
                                   ("lens", rot["lens_max_per_window"], span, rot["window_saturdays"]),
                                   ("shape", shp["max_per_window"], shape_span, shp["window_saturdays"])):
        flagged = set()
        for q in (e for e in timeline if e["queued"] and e[key]):
            worst = 0
            start = q["date"] - win
            while start <= q["date"]:
                n = sum(1 for e in timeline if e[key] == q[key] and start <= e["date"] <= start + win)
                worst = max(worst, n)
                start += timedelta(weeks=1)
            if worst > limit and (q[key], q["date"]) not in flagged:
                flagged.add((q[key], q["date"]))
                errors.append(f"{q['date']}: {key} '{q[key]}' appears {worst} times in a "
                              f"{weeks}-Saturday window (max {limit})")

    cooldown = timedelta(weeks=rot["pillar_lens_cooldown_weeks"])
    for q in (e for e in timeline if e["queued"]):
        for e in timeline:
            if e is q or e["pillar"] != q["pillar"] or e["lens"] != q["lens"]:
                continue
            if abs(e["date"] - q["date"]) < cooldown and (not e["queued"] or e["date"] < q["date"]):
                errors.append(f"{q['date']}: {q['pillar']} x {q['lens']} repeats {e['date']} "
                              f"(cooldown {rot['pillar_lens_cooldown_weeks']} weeks)")

    comparisons = [q for q in queue if COMPARISON.search(q.get("topic") or "")]
    if queue and len(comparisons) / len(queue) > rot["comparison_max_ratio"]:
        errors.append(f"{len(comparisons)} of {len(queue)} topics are 'X vs Y' comparisons "
                      f"(max {rot['comparison_max_ratio']:.0%})")

    # Soft: never-used pillars and lenses left out of the horizon
    horizon_end = next_saturdays(today, cfg["schedule"]["horizon_saturdays"])[-1]
    in_horizon = [e for e in timeline if today < e["date"] <= horizon_end]
    for key, plural, names in (("pillar", "pillars", sheet["pillars"]), ("lens", "lenses", sheet["lenses"])):
        missing = [n for n in names if not any(e[key] == n for e in timeline)]
        if missing:
            warnings.append(f"{plural} still never used: {', '.join(missing)}")
        absent = [n for n in names if not any(e[key] == n for e in in_horizon)]
        if absent and rot["prioritize_unused"]:
            warnings.append(f"{plural} with no post in the horizon: {', '.join(absent)}")

    return errors, warnings


def build_diff(sheet, proposal):
    rows = {r["row"]: r for r in sheet["schedule"]}
    diff = []
    for q in proposal.get("queue", []):
        src = rows.get(q.get("origin_row"))
        entry = {k: q.get(k) for k in ("date", "pillar", "lens", "topic", "shape", "rationale", "test", "origin_row")}
        if not src:
            entry.update(op="ADD", source="Agent")
        else:
            moved = src["date"] != q.get("date")
            edited = any(src[k] != q.get(k) for k in ("pillar", "lens", "topic", "shape"))
            entry["op"] = "EDIT+MOVE" if moved and edited else "MOVE" if moved else "EDIT" if edited else "KEEP"
            entry["source"] = "Agent" if src["topic"] != q.get("topic") else (src["source"] or "Me")
            entry["was"] = {k: src[k] for k in ("date", "pillar", "lens", "topic", "shape")}
        diff.append(entry)
    diff.sort(key=lambda e: e["date"] or "")
    for x in proposal.get("drops", []):
        src = rows.get(x["row"], {})
        diff.append({"op": "DROP", "origin_row": x["row"], "reason": x.get("reason", ""),
                     "was": {k: src.get(k) for k in ("date", "pillar", "lens", "topic")}})
    return diff


def render_md(diff, errors, warnings, before, after):
    def esc(s):
        return (s or "").replace("|", "/").replace("\n", " ")

    out = ["| Date | Change | Pillar | Lens | Shape | Topic | Why / test |", "|---|---|---|---|---|---|---|"]
    for e in diff:
        if e["op"] == "DROP":
            w = e["was"]
            out.append(f"| ~~{w['date']}~~ | DROP | {esc(w['pillar'])} | {esc(w['lens'])} | | "
                       f"~~{esc(w['topic'])}~~ | {esc(e['reason'])} |")
            continue
        was = ""
        if e["op"] not in ("ADD", "KEEP"):
            w = e["was"]
            changed = [f"{k}: {esc(w[k])}" for k in ("date", "pillar", "lens", "topic", "shape") if w[k] != e[k]]
            was = "<br>was " + "; ".join(changed)
        out.append(f"| {e['date']} | {e['op']} | {esc(e['pillar'])} | {esc(e['lens'])} | {esc(e['shape'])} | "
                   f"{esc(e['topic'])}{was} | {esc(e['rationale'])}<br>test: {esc(e['test'])} |")
    out += ["", f"Coverage before: {before}", f"Coverage after: {after}"]
    if errors:
        out += ["", "Rule errors:"] + [f"- {x}" for x in errors]
    if warnings:
        out += ["", "Warnings:"] + [f"- {x}" for x in warnings]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("proposal")
    ap.add_argument("out_json")
    ap.add_argument("out_md")
    ap.add_argument("--today")
    a = ap.parse_args()
    cfg = load_config()
    sheet, proposal = read_json(a.sheet), read_json(a.proposal)
    today = today_from_arg(a.today)

    errors, warnings = check(sheet, proposal, cfg, today)
    diff = build_diff(sheet, proposal)
    st = cfg["status"]
    active_before = [r for r in sheet["schedule"] if r["status"] in (st["posted"], st["scheduled"], st["queued"])]
    active_after = [r for r in sheet["schedule"] if r["status"] in (st["posted"], st["scheduled"])]
    active_after += [e for e in diff if e["op"] != "DROP"]
    before = summary_line(active_before, sheet["pillars"], sheet["lenses"])
    after = summary_line(active_after, sheet["pillars"], sheet["lenses"])

    ops = {}
    for e in diff:
        ops[e["op"]] = ops.get(e["op"], 0) + 1
    write_json(a.out_json, {"ok": not errors, "errors": errors, "warnings": warnings, "ops": ops,
                            "coverage_before": before, "coverage_after": after, "diff": diff})
    with open(a.out_md, "w", encoding="utf-8") as f:
        f.write(render_md(diff, errors, warnings, before, after))
    print(f"ok={not errors} errors={len(errors)} warnings={len(warnings)} ops={ops}")
    for x in errors:
        print(f"  ERROR {x}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
