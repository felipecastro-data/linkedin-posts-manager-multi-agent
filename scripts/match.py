"""Link scraped LinkedIn posts to 'Created & Posted' schedule rows.

Usage: python3 scripts/match.py runs/<id>/sheet.json runs/<id>/posts.json runs/<id>/matches.json

The activity ID in a post URN holds a millisecond timestamp in its first 41
bits, which gives the exact publish date. Match order: URL already stored in
the row, then publish date within the configured tolerance.
"""

import re
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from common import load_config, read_json, write_json

LOCAL_TZ = ZoneInfo("America/Bogota")


def activity_id(text):
    m = re.search(r"activity[:%3A]+(\d{15,})", text or "")
    return m.group(1) if m else None


def publish_date(act_id):
    bits = bin(int(act_id))[2:]
    ms = int(bits[:41], 2)
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone(LOCAL_TZ).date()


def main(sheet_path, posts_path, out_path):
    cfg = load_config()
    posted = cfg["status"]["posted"]
    tolerance = cfg["linkedin"]["match_tolerance_days"]
    sheet = read_json(sheet_path)
    posts = read_json(posts_path)

    rows = [r for r in sheet["schedule"] if r["status"] == posted]
    for p in posts:
        act = activity_id(p.get("urn") or p.get("url"))
        p["activity_id"] = act
        p["post_date"] = publish_date(act).isoformat() if act else None
        p["url"] = f"https://www.linkedin.com/feed/update/urn:li:activity:{act}/" if act else p.get("url")

    taken = {}
    # 1. URL already stored in the sheet
    for r in rows:
        act = activity_id(r.get("url"))
        if act:
            for p in posts:
                if p["activity_id"] == act:
                    taken[r["row"]] = (p, "url")
    # 2. Closest publish date within tolerance
    used = {id(v[0]) for v in taken.values()}
    candidates = []
    for r in rows:
        if r["row"] in taken or not r["date"]:
            continue
        rd = datetime.fromisoformat(r["date"]).date()
        for p in posts:
            if id(p) in used or not p["post_date"]:
                continue
            gap = abs((datetime.fromisoformat(p["post_date"]).date() - rd).days)
            if gap <= tolerance:
                candidates.append((gap, r["row"], p))
    for gap, row, p in sorted(candidates, key=lambda x: (x[0], x[1])):
        if row in taken or id(p) in used:
            continue
        taken[row] = (p, f"date±{gap}")
        used.add(id(p))

    by_row = {r["row"]: r for r in rows}
    matched = []
    for row, (p, method) in sorted(taken.items()):
        r = by_row[row]
        matched.append({
            "row": row, "method": method,
            "sheet_date": r["date"], "pillar": r["pillar"], "lens": r["lens"], "topic": r["topic"],
            **p,
        })
    out = {
        "matched": matched,
        "unmatched_posts": [p for p in posts if id(p) not in used],
        "unmatched_rows": [r for r in rows if r["row"] not in taken],
    }
    write_json(out_path, out)
    print(f"matched={len(matched)} unmatched_posts={len(out['unmatched_posts'])} "
          f"unmatched_rows={len(out['unmatched_rows'])}")
    for r in out["unmatched_rows"]:
        print(f"  row {r['row']} {r['date']} not found on LinkedIn: {r['topic'][:60]}")
    for p in out["unmatched_posts"]:
        print(f"  post {p['post_date']} not in sheet: {(p.get('text') or '')[:60]}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
