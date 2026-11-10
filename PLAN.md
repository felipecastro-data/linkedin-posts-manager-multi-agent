# LinkedIn Social Media Manager (multi-agent) — Plan v0.2

Status: Phases 1-3 done. Web app v1 deployed 2026-10-25.

## Goal

A manually run skill, `/linkedin-ideas` (about monthly), that keeps the
**Posts Schedule** table stocked with post ideas for Saturdays. It reads the
pillars, lenses and schedule, scores the posts already on LinkedIn **for
content quality**, and adds, edits, drops or reorders queued ideas. It
proposes ideas (pillar, lens, one-sentence topic). It never writes or
publishes posts.

Purpose of the posts: stay active and show senior data engineering
knowledge. Not an influencer play. Likes and impressions are recorded but
never drive decisions.

## Source of truth

Spreadsheet `1zKbL54y6twj1ySJu1zjPuJwoo8frfXE1aBc82jsbMsA`, tab `LinkedIn Posts`
(sheetId 330526701). Three Sheets tables:

| Table | Range | Columns |
|---|---|---|
| Post Pillars | B5:B18 | Pillars (13) |
| Post Lenses | D5:D15 | Lenses (10) |
| Posts Schedule | B21:F49 (grows) | Date, Pillar, Lenses, Topic, Status |

Status values in use:
- `Created & Posted`: on LinkedIn. Read-only.
- `Created & Scheduled`: written and scheduled in LinkedIn. Read-only.
- `Not Created / In Queue`: the agent may add, edit, drop or move these (yours and its own).
- `Dropped` (new): replaces deletion. Date cleared, row moved to the bottom,
  reason kept, never proposed again.

## Baseline (snapshot 2026-10-25, 28 rows)

Pillars: PySpark 6, Python 6, SQL 4, Stream Analytics 3, AI Integration 3,
Data Pipelines 3, Data Warehouse 2, IaC 1. **Never used**: Data Lakehouse,
CI/CD, Data Governance, NoSQL, Graph Models.

Lenses: Performance 8, Debugging 5, Trade-offs 4, Data quality 4,
Reliability 3, Scalability 3, Common mistakes 1. **Never used**: Cost,
Migration / Modernization, Business Translation.

Overlaps the Editor should catch in the current queue:
- Python, "big data in memory": chunked reading (posted), generators (posted),
  vectorization (scheduled), *for loop at 10K vs 10M rows* (queue 01/02),
  *memory profiling* (queue 12/05), *%%time + tracemalloc* (queue 01/30).
  The last three overlap each other and the posted ones.
- Schema drift: Delta schema evolution (posted), *silent schema drift*
  (queue 12/12), *validation checkpoints with schema drift detection* (queue 12/19).
- Shuffle: salting for skew (posted), *partition sizing and shuffle* (queue
  01/23), *GROUP BY shuffle spill at 1B rows* (queue 02/06).

Topic length is inconsistent (2 words up to a full paragraph). Target: one
sentence, at most ~25 words, describing the problem or decision.

## Agents and steps

| Step | Who | Does |
|---|---|---|
| 0 Preflight | orchestrator | load tools, check Chrome is signed in to LinkedIn, create `runs/<run_id>/` |
| 1 Collect | orchestrator | Sheets connector -> `sheet.json`; Claude in Chrome -> `posts.json` (full text of every post) |
| 2 Match | `scripts/match.py` + orchestrator | link each LinkedIn post to its `Created & Posted` row |
| 3 Score content | **Content Reviewer** (subagent) | score each posted post with the rubric below -> `scores.json` |
| 4 Strategize | **Content Strategist** (subagent) | coverage + scores + queue -> `proposal.json` (add / edit / drop / move, reason for each) |
| 5 Review | **Editor** (subagent) | check every proposed idea; one revision round with the Strategist -> `review.json` |
| 6 Validate | `scripts/validate_proposal.py` | hard rules: only queued rows touched, one idea per Saturday, rotation limits, valid pillar/lens names |
| 7 Approve | you | diff table in chat; accept all, accept some, or reject |
| 8 Write | orchestrator | update Schedule rows, append `Post Scores` and `Agent Runs`, read back to confirm |
| 9 Report | orchestrator | 3-5 lines in chat |

Three LLM agents, each in its own context so the Editor and Reviewer judge
independently of the Strategist.

### Matching posts to rows
LinkedIn only shows relative dates ("21h", "2mo"). Two methods:
1. The post URL holds an activity ID whose first 41 bits are a millisecond
   timestamp, which gives the exact publish date. Match that date to the row.
2. Fallback: the orchestrator matches by topic (12 posts, so this is easy).
The matched URL is written to the new `LinkedIn URL` column, so later runs
match by URL directly.

## Content scoring (replaces engagement scoring)

The Content Reviewer scores each posted post 1-5 on:

| Dimension | 5 looks like |
|---|---|
| Senior depth | A senior DE learns something not in the first page of the docs: a failure mode, a limit, a non-obvious setting. |
| Specificity | Concrete numbers, configs, tool and version names, a real outcome. |
| Narrow scope | One decision, one bug, one setting. Not a topic overview. |
| Credibility | Grounded in something reproducible; no fabricated numbers; no employer or client material. |
| Voice | Follows `config/rules.md`: no hype, no banned patterns, no emojis or em dashes, problem-first framing. |
| Clarity | A data engineer who never used the tool gets the problem, cause and fix on one read. |

Post score = average of the six, plus a one-line note per dimension. The
Strategist uses the scores to see which pillars and lenses produced his
strongest senior content. Reactions, comments and impressions are still
saved in `Post Scores` for context, with no weight in any decision.

The Editor applies the first four dimensions (minus Voice and Clarity) to
proposed ideas as a *potential* score. Ideas under 3.5 go back for revision.
For clarity it only checks that each idea's core fits in one plain sentence.

## Strategy rules (defaults in `config/strategy.toml`)

Horizon: always keep the next 13 Saturdays covered (one idea each, every
Saturday, holidays included). Queued ideas dated beyond that are backlog and
can also be reworked. As of today the queue already reaches 2027-02-13.

Rotation (even, per your answer):
- Each pillar used about equally. Over any 13 Saturdays, no pillar more than
  twice; never-used pillars get priority until they catch up.
- Same pillar never on two Saturdays in a row.
- Same pillar + lens not within 12 weeks.
- No lens more than twice in 13 Saturdays; unused lenses get priority.
- Max 1 in 4 topics framed as "X vs Y" (comparisons drift toward the banned
  "The trade-off is..." closer).

Pillar + lens pairs must make sense together (Graph Models x Cost might not).
The Strategist skips weak pairs instead of forcing coverage.

Novelty: compare against every row (any status) and the full text of posted
posts. Same underlying technique counts as a duplicate even when worded
differently.

Reproducible: every idea must be testable in a personal setup so the post
can use real numbers. Each proposal includes a one-line `test` field (what
to run, on what, measuring what). Shown in the diff, stored in `Agent Runs`,
not in the Schedule table.

Pillar and lens suggestions: the Strategist may suggest new pillars or lenses
as feedback only. It never edits the Pillars or Lenses tables.

## Sheet changes (done 2026-10-25)

Posts Schedule table now spans B21:I49: Date, Pillar, Lenses, Topic,
Status, `Rationale` (G), `Source` (H, dropdown Me / Agent; existing rows set
to Me), `LinkedIn URL` (I). Status is a dropdown with the four values above.

New tabs (also the web app's data), each a Sheets table starting at A1:
- `Post Scores` (A:S): Run ID, Scored At, Post Date, Pillar, Lens, Topic,
  LinkedIn URL, Senior Depth, Specificity, Narrow Scope, Credibility, Voice,
  Clarity, Score, Notes, Reactions, Comments, Reposts, Impressions. Score is
  written as a formula, `=ROUND(AVERAGE(Hn:Mn),1)`, not a typed number.
  Rows from before 2026-11-10 have no Clarity and average five dimensions.
- `Agent Runs` (A:L): Run ID, Run At, Summary, Strategist Feedback,
  Pillar / Lens Suggestions, Coverage Before, Coverage After, Added, Edited,
  Dropped, Moved, Change Log (JSON).

## Project layout

```
.claude/
  skills/linkedin-ideas/SKILL.md      orchestrator (steps 0-9)
  agents/content-reviewer.md
  agents/content-strategist.md
  agents/editor.md
config/
  rules.md                            writing rules + banned patterns (single source)
  rubric.md                           scoring rubric
  strategy.toml                       IDs, horizon, rotation limits, thresholds (TOML: no extra Python packages)
scripts/
  parse_sheet.py                      raw get_values -> sheet.json
  match.py                            activity-ID date decode + row matching
  coverage.py                         pillar/lens counts and gaps
  validate_proposal.py                hard-rule checks + diff
  build_writes.py                     exact sheet writes for an approved run (sends nothing)
runs/<run_id>/                        json files per run (gitignored)
webapp/                               Apps Script project (Phase 3, clasp)
cloudflare/                           Cloudflare Pages host of the same web app (home-screen icon)
```

## Phases

1. **Foundations** (done): write `rules.md`, `rubric.md`, `strategy.toml`; add the
   new columns, status value and tabs to the sheet.
2. **Pipeline**: build the skill, agents and scripts. Run in dry-run mode
   (proposal and diff, no writes) until the proposals look right, then turn
   on writing.
3. **Web app** (done, v1): standalone Apps Script project "LinkedIn Posts"
   (script `1UbQiX5-a9SMul4dZFPtgB_avAlfKGp-bniPTEFx7D0mBAQa4vxObDoEO`), read-only,
   deployed as Execute as me / Only myself:
   https://script.google.com/macros/s/AKfycbz_iGxfRoWtolsp-7y5cDG6IalsLCMKu2mYG-gjVKL3MxvRlUlMWf4Kq1suYsSMFwou/exec
   - Source in `webapp/` (Code.js reads the three tabs; Styles.html reuses the LinkedIn
     Review design system; App.html holds the five tabs: Overview, Queue, Posts,
     Coverage, Runs).
   - Local preview: `python3 scripts/preview_webapp.py runs/<id>`, then the
     `webapp-preview` server in `.claude/launch.json`.
   - Ship changes: `clasp push -f`, then
     `clasp update-deployment AKfycbz_iGxfRoWtolsp-7y5cDG6IalsLCMKu2mYG-gjVKL3MxvRlUlMWf4Kq1suYsSMFwou`
     so the URL stays the same.
   - Editor verdicts (avg, potential, issues) are stored per idea in the Agent Runs
     Change Log, which now lists every queue entry, KEEP included.
   - **Cloudflare Pages (primary on the phone)**: Apps Script serves the page inside a
     Google iframe, so iOS never sees an app icon. Pages project `linkedin-posts`
     (https://linkedin-posts-86b.pages.dev, branch `main`; preview
     https://preview.linkedin-posts-86b.pages.dev, branch `preview`) serves the same
     `webapp/` page behind Cloudflare Access (team `odd-paper-fda0.cloudflareaccess.com`,
     application "LinkedIn Posts Manager" on `linkedin-posts-86b.pages.dev` and
     `*.linkedin-posts-86b.pages.dev`, policy "Only me"). The Apps Script app stays live
     as a fallback.
     - `cloudflare/functions/api/[fn].js`: `POST /api/getData`, a port of Code.js
       `getData()` on the Sheets API, same JSON string. **A change to `getData()` in
       Code.js must be made there too.** Verifies the `Cf-Access-Jwt-Assertion` token
       (fails closed) and reads as the service account
       `expenses-reader@expenses-tracker-513017.iam.gserviceaccount.com` (shared with the
       other Pages apps; needs Viewer on the LinkedIn Posts sheet).
     - `App.html` `getData()` uses `google.script.run` when present, else the fetch.
     - Pages secret (production + preview): `GOOGLE_SA_KEY`. `cloudflare/wrangler.toml`
       vars: `SPREADSHEET_ID`, `ACCESS_TEAM_DOMAIN`, `ACCESS_AUD`.
     - `cloudflare/public/`: icons (`apple-touch-icon.png` 180, `icon-192/512.png`,
       `favicon-32.png`) and `manifest.webmanifest`; `index.html` there is built by
       `python3 scripts/preview_webapp.py --pages` (gitignored). Home-screen `<head>`
       tags live in `Index.html`.
     - `cloudflare/.dev.vars` (gitignored): `DEV_NO_ACCESS=1`, `GOOGLE_SA_KEY`; the
       `pages-dev` launch entry runs it at http://localhost:8791 with live sheet data.
     - Ship: `cd cloudflare && npm run deploy:preview`, check on the iPhone, then
       `npm run deploy:prod`. Also `clasp push` for the fallback. iOS caches home-screen
       icons: after an icon change, delete the home-screen app and add it again.
4. **Office** (done, v2 deployment): a 3D tab in the same web app (`webapp/Office.html`,
   three.js r147 from jsDelivr, loaded only when the tab opens). Isometric cut-away
   room after the reference render; six androids built in code from the three
   reference figures; the run plays on a loop (hand-off packets between laptops,
   status chip over the active agent, TV dashboard). Every agent and the TV, window,
   notebook, phone, plants and table open a frosted card. Seating: Coordinator and
   Content Strategist on the window side; Collector, Content Reviewer, Editor and
   Sheet Writer in front. Night mode lights the city.
   - Per-agent usage lives in the Agent Runs `Agent Stats` column (M), written from
     `runs/<id>/agent_stats.json` (see the Usage log section of the skill).
