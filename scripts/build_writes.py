"""Build the exact sheet writes for an approved run. Sends nothing.

Usage: python3 scripts/build_writes.py --run runs/<id> --run-id <id> --run-date YYYY-MM-DD \
           --scores-next-row N --runs-next-row N [--approved runs/<id>/approved.json]

Reads sheet.json, validation.json (diff), matches.json, scores.json and
proposal.json from the run folder and writes writes.json:
  table_updates: updateTable requests that grow the tables first
  value_writes:  update_values calls ({range, values})
`--approved` limits the schedule changes to the diff entries you accepted
(a JSON list of origin_row numbers and/or new-idea dates).
"""

import argparse
import json
from pathlib import Path

from common import load_config, read_json, sheet_date, write_json, parse_date


def table_range(sheet_id, start_row0, end_row0, start_col0, end_col0, table_id):
    return {"updateTable": {"table": {"tableId": table_id, "range": {
        "sheetId": sheet_id, "startRowIndex": start_row0, "endRowIndex": end_row0,
        "startColumnIndex": start_col0, "endColumnIndex": end_col0}}, "fields": "range"}}


def schedule_rows(sheet, diff, matches, cfg, run_date):
    st = cfg["status"]
    urls = {m["row"]: m["url"] for m in matches.get("matched", [])}
    active, dropped = [], []
    for r in sheet["schedule"]:
        if r["status"] in (st["posted"], st["scheduled"]):
            url = r["url"] or urls.get(r["row"], "")
            active.append((r["date"], [sheet_date(parse_date(r["date"])), r["pillar"], r["lens"], r["topic"],
                                       r["status"], r["rationale"], r["source"] or "Me", url]))
        elif r["status"] == st["dropped"]:
            dropped.append(["", r["pillar"], r["lens"], r["topic"], r["status"], r["rationale"], r["source"], r["url"]])
    for e in diff:
        if e["op"] == "DROP":
            w = e["was"]
            src = next(r for r in sheet["schedule"] if r["row"] == e["origin_row"])
            dropped.append(["", w["pillar"], w["lens"], w["topic"], st["dropped"],
                            f"Dropped {run_date}: {e['reason']}", src["source"] or "Me", ""])
        else:
            active.append((e["date"], [sheet_date(parse_date(e["date"])), e["pillar"], e["lens"], e["topic"],
                                       st["queued"], e.get("rationale") or "", e["source"], ""]))
    active.sort(key=lambda x: x[0] or "9999")
    return [v for _, v in active] + dropped


def apply_approval(sheet, diff, approved, cfg):
    """Keep rejected entries as they are in the sheet."""
    if approved is None:
        return diff
    rows = {r["row"]: r for r in sheet["schedule"]}
    out = []
    for e in diff:
        key_ok = e.get("origin_row") in approved or (e["op"] == "ADD" and e["date"] in approved)
        if key_ok or e["op"] == "KEEP":
            out.append(e)
        elif e["op"] != "ADD":
            r = rows[e["origin_row"]]
            out.append({"op": "KEEP", "origin_row": r["row"], "date": r["date"], "pillar": r["pillar"],
                        "lens": r["lens"], "topic": r["topic"], "rationale": r["rationale"],
                        "source": r["source"] or "Me"})
    return out


def build_change_log(diff, run):
    """Every queue entry (KEEP included, so the web app has each idea's test)
    plus drops, with the Editor's final verdict per idea. Must stay valid JSON
    under the 50,000-character cell limit, so trim fields rather than text."""
    review_path = run / "review.json"
    review = read_json(review_path) if review_path.exists() else {"items": []}
    by_date = {i["date"]: i for i in review.get("items", [])}
    entries = []
    for e in diff:
        e = dict(e)
        item = by_date.get(e.get("date")) if e["op"] != "DROP" else None
        if item:
            e["editor"] = {k: item.get(k) for k in ("avg", "potential", "issues", "duplicate_of")}
        entries.append(e)
    text = json.dumps(entries, ensure_ascii=False)
    for field in ("rationale", "was"):
        if len(text) <= 45000:
            break
        for e in entries:
            e.pop(field, None)
        text = json.dumps(entries, ensure_ascii=False)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--run-date", required=True)
    ap.add_argument("--scores-next-row", type=int, required=True)
    ap.add_argument("--runs-next-row", type=int, required=True)
    ap.add_argument("--approved")
    a = ap.parse_args()
    cfg, run = load_config(), Path(a.run)
    sh = cfg["sheet"]
    sheet = read_json(run / "sheet.json")
    validation = read_json(run / "validation.json")
    matches = read_json(run / "matches.json")
    scores = read_json(run / "scores.json")
    proposal = read_json(run / "proposal.json")
    approved = read_json(a.approved) if a.approved else None
    run_date = sheet_date(parse_date(a.run_date))

    diff = apply_approval(sheet, validation["diff"], approved, cfg)
    sched = schedule_rows(sheet, diff, matches, cfg, a.run_date)
    header = sh["schedule_header_row"]
    last = header + len(sched)
    value_writes = [{"range": f"'{sh['tab']}'!{sh['schedule_first_col']}{header + 1}:{sh['schedule_last_col']}{last}",
                     "values": sched}]
    table_updates = []
    if len(sched) > len(sheet["schedule"]):
        table_updates.append(table_range(sh["schedule_sheet_id"], header - 1, last, 1, 9, sh["schedule_table_id"]))

    # Post Scores
    metrics = {p["url"]: p for p in matches.get("matched", []) + matches.get("unmatched_posts", [])}
    score_rows = []
    for i, p in enumerate(scores.get("posts", [])):
        n = a.scores_next_row + i
        m = metrics.get(p["url"], {})
        s = p["scores"]
        score_rows.append([
            a.run_id, run_date, sheet_date(parse_date(p.get("post_date"))), p.get("pillar") or "",
            p.get("lens") or "", p.get("topic") or "", p["url"],
            s["senior_depth"], s["specificity"], s["narrow_scope"], s["credibility"], s["voice"],
            f"=ROUND(AVERAGE(H{n}:L{n}),1)", p.get("note", ""),
            *[m.get(k) if m.get(k) is not None else "" for k in ("reactions", "comments", "reposts", "impressions")],
        ])
    if score_rows:
        end = a.scores_next_row + len(score_rows) - 1
        value_writes.append({"range": f"'{sh['score_tab']}'!A{a.scores_next_row}:R{end}", "values": score_rows})
        table_updates.append(table_range(sh["score_sheet_id"], 0, max(end, 2), 0, 18, sh["score_table_id"]))

    # Agent Runs
    ops = {}
    for e in diff:
        ops[e["op"]] = ops.get(e["op"], 0) + 1
    suggestions = "; ".join(f"{x['type']}: {x['name']} ({x['why']})" for x in proposal.get("suggestions", []))
    change_log = build_change_log(diff, run)
    n = a.runs_next_row
    stats_path = run / "agent_stats.json"
    agent_stats = json.dumps(read_json(stats_path), ensure_ascii=False) if stats_path.exists() else ""
    value_writes.append({"range": f"'{sh['runs_tab']}'!A{n}:M{n}", "values": [[
        a.run_id, run_date, proposal.get("summary", ""), proposal.get("feedback", ""), suggestions,
        validation["coverage_before"], validation["coverage_after"],
        ops.get("ADD", 0), ops.get("EDIT", 0) + ops.get("EDIT+MOVE", 0), ops.get("DROP", 0),
        ops.get("MOVE", 0) + ops.get("EDIT+MOVE", 0), change_log, agent_stats,
    ]]})
    table_updates.append(table_range(sh["runs_sheet_id"], 0, max(n, 2), 0, 13, sh["runs_table_id"]))

    write_json(run / "writes.json", {"table_updates": table_updates, "value_writes": value_writes})
    print(f"schedule_rows={len(sched)} score_rows={len(score_rows)} table_updates={len(table_updates)} "
          f"value_writes={len(value_writes)}")


if __name__ == "__main__":
    main()
