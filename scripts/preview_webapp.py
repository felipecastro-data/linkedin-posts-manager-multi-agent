"""Build a local preview of the web app with data from a run folder.

Usage: python3 scripts/preview_webapp.py runs/<id> [--today YYYY-MM-DD]
Writes webapp/preview/index.html (gitignored): Index.html with its includes
inlined and google.script.run replaced by a stub that returns the same payload
shape as Code.js getData(), built from the run's sheet_raw.json and writes.json.

--pages writes cloudflare/public/index.html instead (gitignored): the same
inlined page with no stub and no data, for Cloudflare Pages (`npm run build`
in cloudflare/).
"""

import argparse
import json
import re
from pathlib import Path

from common import ROOT, read_json

WEBAPP = ROOT / "webapp"
PAGES_OUT = ROOT / "cloudflare" / "public" / "index.html"
SCHEDULE_KEYS = ["date", "pillar", "lens", "topic", "status", "rationale", "source", "url", "shape"]


def slug(h):
    return re.sub(r"^_|_$", "", re.sub(r"[^a-z0-9]+", "_", h.strip().lower()))


def payload(run, today):
    raw = read_json(run / "sheet_raw.json")["values"]

    def col_list(header):
        for r, row in enumerate(raw):
            if header in row:
                c, out = row.index(header), []
                for nxt in raw[r + 1:]:
                    if c < len(nxt) and nxt[c]:
                        out.append(nxt[c])
                    else:
                        break
                return out
        return []

    writes = read_json(run / "writes.json")["value_writes"]
    by_tab = {w["range"].split("!")[0].strip("'"): w["values"] for w in writes}
    schedule = [dict(zip(SCHEDULE_KEYS, r)) for r in by_tab["LinkedIn Posts"]]

    score_hdr = ["Run ID", "Scored At", "Post Date", "Pillar", "Lens", "Topic", "LinkedIn URL", "Senior Depth",
                 "Specificity", "Narrow Scope", "Credibility", "Voice", "Clarity", "Score", "Notes", "Reactions", "Comments",
                 "Reposts", "Impressions"]
    scores = []
    for r in by_tab.get("Post Scores", []):
        o = dict(zip(map(slug, score_hdr), [str(v) for v in r]))
        o["score"] = str(round(sum(r[7:13]) / 6, 1))
        scores.append(o)

    runs_hdr = ["Run ID", "Run At", "Summary", "Strategist Feedback", "Pillar / Lens Suggestions", "Coverage Before",
                "Coverage After", "Added", "Edited", "Dropped", "Moved", "Change Log", "Agent Stats"]
    runs = []
    for r in by_tab.get("Agent Runs", []):
        o = dict(zip(map(slug, runs_hdr), [str(v) for v in r]))
        o["change_log"] = json.loads(o["change_log"])
        o["agent_stats"] = json.loads(o["agent_stats"]) if o.get("agent_stats") else None
        runs.append(o)

    return {"pillars": col_list("Pillars"), "lenses": col_list("Lenses"), "schedule": schedule,
            "scores": scores, "runs": runs, "today": today,
            "sheet_url": "https://docs.google.com/spreadsheets/d/1zKbL54y6twj1ySJu1zjPuJwoo8frfXE1aBc82jsbMsA/edit"}


def page_html():
    """Index.html with its includes inlined and the viewport tag doGet() adds through addMetaTag."""
    html = (WEBAPP / "Index.html").read_text(encoding="utf-8")
    html = re.sub(r"<\?!= include\('(\w+)'\) \?>",
                  lambda m: (WEBAPP / f"{m.group(1)}.html").read_text(encoding="utf-8"), html)
    return html.replace("<meta charset=\"utf-8\">", "<meta charset=\"utf-8\">\n<meta name=\"viewport\" "
                        "content=\"width=device-width, initial-scale=1, viewport-fit=cover\">", 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?")
    ap.add_argument("--today", default="2026-10-25")
    ap.add_argument("--pages", action="store_true")
    a = ap.parse_args()
    if a.pages:
        PAGES_OUT.write_text(page_html(), encoding="utf-8")
        print(f"wrote {PAGES_OUT.relative_to(ROOT)}")
        return
    if not a.run:
        ap.error("run is required without --pages")
    data = json.dumps(payload(Path(a.run), a.today), ensure_ascii=False)
    html = page_html()
    stub = ("<script>window.google={script:{run:(function(){const h={};const r={withSuccessHandler(f){h.ok=f;return r},"
            "withFailureHandler(f){h.err=f;return r},getData(){setTimeout(()=>h.ok(JSON.stringify(window.__DATA__)),150)}};"
            "return r})()}};window.__DATA__=" + data.replace("</", "<\\/") + ";</script>")
    html = html.replace("<body>", "<body>\n" + stub, 1)
    out = WEBAPP / "preview" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
