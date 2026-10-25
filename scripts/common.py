"""Shared helpers for the /linkedin-ideas scripts."""

import json
import tomllib
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "strategy.toml"


def load_config():
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_date(value):
    """Accept ISO (2026-11-14) or sheet display format (11/14/2026)."""
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def sheet_date(d):
    return d.strftime("%m/%d/%Y") if d else ""


def next_saturdays(today, count, weekday=5):
    """The next `count` posting days strictly after `today`."""
    d = today + timedelta(days=1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return [d + timedelta(weeks=i) for i in range(count)]


def today_from_arg(value):
    return parse_date(value) if value else date.today()
