---
name: linkedin-ideas
description: Run Felipe's LinkedIn ideas multi-agent (collect posts and sheet, score content, Strategist, Editor) and update the Posts Schedule queue in Google Sheets after his approval. Use for /linkedin-ideas or "run my LinkedIn ideas". Pass "dry-run" to skip all sheet writes.
---

# /linkedin-ideas — orchestrator

One run = read the sheet and every LinkedIn post → score published posts for
content quality → Strategist proposes the idea queue → Editor reviews → one
revision → rule check → Felipe approves → write to the sheet.

The agents propose ideas only (pillar, lens, one-sentence topic). Nothing
here writes or publishes posts.

Project root: this repository. All paths below are relative to it.
Config: `config/strategy.toml` (IDs, statuses, rotation limits),
`config/rules.md`, `config/rubric.md`. Agent prompts: `.claude/agents/`.

**Dry run**: if the arguments contain `dry-run`, do steps 0-7 and stop
before step 8. Say clearly that nothing was written.

Tell Felipe in one line that the run started. Keep a task list with the
steps below. Ask questions only when a step is blocked.

## Step 0 — Preflight

1. Load in ONE ToolSearch call: the Google Sheets tools `get_values`,
   `update_values`, `update_spreadsheet`, and the Claude in Chrome tools
   `tabs_context_mcp`, `tabs_close_mcp`, `navigate`, `javascript_tool`,
   `computer`, `get_page_text`.
2. `RUN_ID = r<YYYYMMDD>-<HHMM>` in America/Bogota time
   (`TZ=America/Bogota date +%Y%m%d-%H%M`). `TODAY` = the local date.
   Create `runs/<RUN_ID>/`.

## Step 1 — Collect

**Sheet.** `get_values` on `'LinkedIn Posts'!A1:I300` (spreadsheet ID in
config). Save the JSON response as `runs/<RUN_ID>/sheet_raw.json`, then:
`python3 scripts/parse_sheet.py runs/<RUN_ID>/sheet_raw.json runs/<RUN_ID>/sheet.json`

**LinkedIn (Claude in Chrome).** Felipe's Chrome is signed in. Never sign
in for him; on a login wall, stop and ask him to sign in.
1. `tabs_context_mcp` with `createIfEmpty: true`; use the tab it gives you.
2. Navigate to `https://www.linkedin.com/in/felipecastro-data/recent-activity/all/`.
3. Count posts expected: the number of `Created & Posted` rows in
   `sheet.json`. Each post card links to `urn:li:activity:<id>`.
   If fewer distinct activity IDs are on the page than expected, scroll
   with the `computer` scroll action (mouse-wheel ticks, 10 at a time;
   `window.scrollBy` does not trigger lazy loading), wait 2 s, recount.
   Stop when the count stops growing.
4. Extract with `javascript_tool` (this worked on 2026-10-25):

```js
const re = /urn:li:activity:(\d{15,})/;
const ids = [...new Set([...document.querySelectorAll('a[href*="urn:li:activity"]')].map(a => a.href.match(re)?.[1]).filter(Boolean))];
const num = s => s ? parseInt(s.replace(/[,.]/g, ''), 10) : 0;
const posts = ids.map(id => {
  let el = document.querySelector(`a[href*="urn:li:activity:${id}"]`), best = el;
  while (el && el !== document.body) {
    const found = new Set([...el.querySelectorAll('a[href*="urn:li:activity"]')].map(a => a.href.match(re)?.[1]));
    if (found.size > 1) break;
    best = el; el = el.parentElement;
  }
  const text = best.innerText;
  const lines = text.split('\n').map(l => l.replace(/​/g, '').trim());
  const ti = lines.findIndex(l => /^\d+(h|d|w|mo|yr|m)( •.*)?$/.test(l));
  let end = lines.findIndex((l, i) => i > ti && /^…\s*more$/.test(l));
  if (end < 0) end = lines.findIndex((l, i) => i > ti && /impressions$/.test(l));
  const after = lines.slice(end + 1).filter(Boolean);
  const m = r => { const x = text.match(r); return x ? num(x[1]) : 0; };
  const imp = text.match(/([\d,]+) impressions/);
  return {urn: `urn:li:activity:${id}`, relative_date: lines[ti],
    text: lines.slice(ti + 1, end).join('\n').replace(/\n{3,}/g, '\n\n').trim(),
    reactions: /^\d[\d,]*$/.test(after[0] || '') ? num(after[0]) : 0,
    comments: m(/(\d[\d,]*) comments?/), reposts: m(/(\d[\d,]*) reposts?/),
    impressions: imp ? num(imp[1]) : null};
});
window.__json = JSON.stringify(posts);
const parts = []; for (let i = 0; i < window.__json.length; i += 900) parts.push(window.__json.slice(i, i + 900));
parts
```

   The tool truncates any single string past ~1,000 characters, so the
   JSON comes back as an array of 900-character chunks. Concatenate them in
   order and save as `runs/<RUN_ID>/posts.json`; check it parses.
   The full post text is in the DOM even when the card shows "… more".
5. Close your tab with `tabs_close_mcp`.

## Step 2 — Match and coverage

```
python3 scripts/match.py runs/<RUN_ID>/sheet.json runs/<RUN_ID>/posts.json runs/<RUN_ID>/matches.json
python3 scripts/coverage.py runs/<RUN_ID>/sheet.json runs/<RUN_ID>/coverage.json --today <TODAY>
```
`match.py` decodes the publish date from each activity ID. Unmatched rows
or posts are reported; carry them on, do not stop.

## Step 3 — Content Reviewer (subagent)

Launch one general-purpose subagent: "Read `.claude/agents/content-reviewer.md`
and follow it. Inputs: `runs/<RUN_ID>/matches.json`, `config/rubric.md`,
`config/rules.md`. Output: `runs/<RUN_ID>/scores.json`. Today is <TODAY>.
No browser, no web search, do not modify other files."

## Step 4 — Content Strategist (subagent)

Launch one general-purpose subagent: "Read `.claude/agents/content-strategist.md`
and follow it. Inputs: `sheet.json`, `coverage.json`, `scores.json`,
`matches.json` in `runs/<RUN_ID>/`, and `config/rules.md`,
`config/rubric.md`, `config/strategy.toml`. Today is <TODAY>. Output:
`runs/<RUN_ID>/proposal_v1.json`. Before finishing, run
`python3 scripts/validate_proposal.py runs/<RUN_ID>/sheet.json runs/<RUN_ID>/proposal_v1.json runs/<RUN_ID>/validation_v1.json runs/<RUN_ID>/diff_v1.md --today <TODAY>`
and fix every error it reports (re-run until it exits 0, max 4 attempts)."

## Step 5 — Editor, then one revision

1. Run the validator on `proposal_v1.json` yourself (same command) so
   `validation_v1.json` is current.
2. Launch the Editor (general-purpose subagent): "Read `.claude/agents/editor.md`
   and follow it. Inputs: `proposal_v1.json`, `validation_v1.json`,
   `sheet.json`, `matches.json` in `runs/<RUN_ID>/`, `config/rules.md`,
   `config/rubric.md`. Output: `runs/<RUN_ID>/review_v1.json`."
3. If the verdict is `revise` or validation has errors, launch the
   Strategist again in revision mode with `proposal_v1.json`,
   `review_v1.json`, `validation_v1.json`; output `proposal_v2.json`, with
   the same validator loop (files `_v2`).
4. Launch the Editor once more in **final mode** on `proposal_v2.json`
   (output `review_v2.json`). No further revision.

The last proposal is `proposal.json` (copy v2, or v1 if no revision was
needed), with its `validation.json`, `diff.md` and `review.json`.

## Step 6 — Validate

`python3 scripts/validate_proposal.py runs/<RUN_ID>/sheet.json runs/<RUN_ID>/proposal.json runs/<RUN_ID>/validation.json runs/<RUN_ID>/diff.md --today <TODAY>`

If errors remain, do not hide them: they go into the approval view.

## Step 7 — Approval view

Show Felipe, in chat:
1. Two lines: the Strategist `summary` and the average content score of
   his published posts.
2. The diff table from `diff.md`, with the Editor's flags (issues,
   duplicate_of, avg below 3.5) appended to the ideas they concern.
   Leave KEEP rows out of the table and give their count in one line.
3. Remaining rule errors and warnings, if any.
4. Strategist `feedback` and `suggestions` in at most 5 lines.

In a dry run, stop here and say nothing was written to the sheet.

Otherwise ask: accept all, accept some (he names dates or rows), or
reject. Record accepted entries in `runs/<RUN_ID>/approved.json` as a list
of `origin_row` numbers and new-idea dates. If he rejects everything, skip
the Schedule write but still log the run (steps 8.3-8.5).

## Step 8 — Write (skipped in dry run)

1. Find the next free rows: `get_values` on `'Post Scores'!A1:A` and
   `'Agent Runs'!A1:A`; next row = number of non-empty rows + 1 (the header
   counts; a table with only a header has next row 2).
2. Build the writes (sends nothing):
   `python3 scripts/build_writes.py --run runs/<RUN_ID> --run-id <RUN_ID> --run-date <TODAY> --scores-next-row N --runs-next-row M [--approved runs/<RUN_ID>/approved.json]`
3. Send `table_updates` from `writes.json` in ONE `update_spreadsheet`
   call (it grows the tables first).
4. Send each `value_writes` entry with `update_values`.
5. Read back `'LinkedIn Posts'!B21:I` and the new Post Scores and Agent
   Runs rows. Check the queue matches the approved diff, Posted and
   Scheduled rows are unchanged, and Score cells show numbers.

## Step 9 — Report

Three to five lines: what changed in the queue (counts), the next three
Saturdays, average content score and the weakest dimension, any rule
errors or Editor flags left, and the sheet link. No recap of the steps.
