"""Turn a raw get_values response for the LinkedIn Posts tab into sheet.json.

Usage: python3 scripts/parse_sheet.py runs/<id>/sheet_raw.json runs/<id>/sheet.json

Finds the three tables by their header cells ("Pillars", "Lenses", "Date"),
so it keeps working if the tables move.
"""

import sys

from common import parse_date, read_json, write_json

SCHEDULE_COLUMNS = ["Date", "Pillar", "Lenses", "Topic", "Status", "Rationale", "Source", "LinkedIn URL", "Shape"]
KEYS = ["date", "pillar", "lens", "topic", "status", "rationale", "source", "url", "shape"]


def cell(rows, r, c):
    if r < len(rows) and c < len(rows[r]):
        return (rows[r][c] or "").strip()
    return ""


def find_header(rows, text):
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if (value or "").strip() == text:
                return r, c
    raise SystemExit(f"Header '{text}' not found in sheet")


def read_list(rows, header):
    r, c = find_header(rows, header)
    items = []
    r += 1
    while cell(rows, r, c):
        items.append(cell(rows, r, c))
        r += 1
    return items


def read_schedule(rows):
    r, c = find_header(rows, "Date")
    header = [cell(rows, r, c + i) for i in range(len(SCHEDULE_COLUMNS))]
    if header != SCHEDULE_COLUMNS:
        raise SystemExit(f"Unexpected schedule header: {header}")
    out = []
    r += 1
    while any(cell(rows, r, c + i) for i in range(len(SCHEDULE_COLUMNS))):
        rec = {k: cell(rows, r, c + i) for i, k in enumerate(KEYS)}
        d = parse_date(rec["date"])
        rec["date"] = d.isoformat() if d else None
        rec["row"] = r + 1  # 1-based sheet row
        out.append(rec)
        r += 1
    return out


def main(raw_path, out_path):
    raw = read_json(raw_path)
    rows = raw.get("values", [])
    sheet = {
        "pillars": read_list(rows, "Pillars"),
        "lenses": read_list(rows, "Lenses"),
        "schedule": read_schedule(rows),
    }
    write_json(out_path, sheet)
    by_status = {}
    for rec in sheet["schedule"]:
        by_status[rec["status"]] = by_status.get(rec["status"], 0) + 1
    print(f"pillars={len(sheet['pillars'])} lenses={len(sheet['lenses'])} "
          f"schedule_rows={len(sheet['schedule'])} by_status={by_status}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
