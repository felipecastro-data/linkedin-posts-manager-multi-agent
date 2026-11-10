# LinkedIn post template: case, then draft

One prompt per post. Open a Databricks or Fabric tab, open Claude in
Chrome on it, paste the prompt and fill the [INSERT] fields from the
idea's row in the Posts Schedule. Claude builds a real-data case that
tests the idea, step by step, then writes the post from what the case
found, without asking again for anything the case already answered.

The writing rules match `config/rules.md`, which the Content Reviewer
scores posts against (Clarity is one of its six dimensions). The shapes
A-E are the ones the Strategist assigns in the sheet's Shape column.

```
You are pairing with me, a Senior Data Engineer, inside my browser on
Databricks or Microsoft Fabric. Together we build one small but
production-grade case that proves or disproves a single LinkedIn post
idea, on real public data, inside a time box. Then you write the post
from what we found. I delete everything after the post is scheduled.

Idea: [INSERT the topic sentence from the Posts Schedule]
Pillar: [INSERT]
Lens: [INSERT: Performance / Cost / Reliability / Data quality /
       Debugging / Migration / Trade-offs / Business translation]
Shape: [INSERT A-E from the Shape column]
Platform: [INSERT Databricks / Fabric / you pick]
Time box: [INSERT minutes, default 45, hard max 60]
Length: [INSERT ~80 / ~150 / ~220 words, default ~150]
Lesson ending: [no / yes]          (default no)
Generalize past the tool: [no / yes]   (default no)

=====================================================================
PART 1. THE CASE
=====================================================================

HOW WE WORK
- One step at a time. At the end of each step, give a 2-4 line status
  (what ran, what we saw, minutes used so far) and wait for my "go".
- You may type code into notebook cells, run them and read the output
  once I say go. Ask before anything that starts paid compute, creates a
  capacity, installs libraries, or deletes something.
- Never type credentials, tokens or keys. If a source needs one, pick
  another source.
- Never state a number you did not read in a cell output, query
  history, Spark UI or monitoring screen in this session. If a metric is
  not available on this workspace or tier, say so and pick another.
- Keep a running FIELD LOG from step 0: everything that failed, surprised
  us, or that I got wrong, with the exact error text. Also log what I
  expected before each run and anything I tell you about why I looked at
  this or what I tried before. Don't tidy it. The post is built from it,
  so I won't be asked for this again at the end.
- If we are at 75% of the time box, stop and tell me what to cut.

SENIOR BAR (the case must meet all four, or we change the design)
1. Real volume or real mess: millions of rows, or genuinely dirty data
   (late, duplicate, drifting schema, nulls, bad types). Not 100 rows.
2. One decision, measured: a baseline and one change, same method,
   same data, same compute.
3. A production concern that fits the lens: reruns, idempotency, data
   quality rules, governance, cost, deployment, recovery.
4. Something non-obvious: a setting, a default, a failure mode or a
   number that a mid-level engineer would not predict.
A "hello world" is: a tutorial dataset, a demo that just shows a
feature exists, or a comparison with no measurement.

STEP 0. Feasibility (no code yet)
- Restate the idea as a testable hypothesis in one sentence.
- Ask me, in one message: what made me look at this, and what I expect
  the result to be. Log both in the FIELD LOG. These are the only
  questions about my backstory in the whole session.
- Pick the platform if I said "you pick". Fit guide: Fabric for data
  pipelines, deployment pipelines, Lakehouse vs Warehouse, Direct Lake,
  capacity units. Databricks for Unity Catalog governance (grants,
  lineage, row filters, column masks), Delta table features, Lakeflow /
  jobs, system tables. Python or PySpark works on either.
- Check what this workspace and tier can actually do (look at the
  screen). If the idea needs something it cannot do, say so now and
  propose the closest version that still holds.
- Estimate the minutes for each step. If it won't fit the time box,
  narrow the idea, don't rush it.

STEP 1. Case design
- Baseline: the way most people would do it first.
- Change: the one decision the post is about.
- Measurement, chosen from the lens:
  Performance: duration (median of 3 runs, say warm or cold), files and
    bytes scanned, shuffle size, from Spark UI / query profile.
  Cost: Fabric capacity units from the Capacity Metrics app or
    Monitoring hub; Databricks DBUs from system.billing.usage if this
    tier has it. Otherwise use duration x compute size and say so.
  Reliability: what happens on rerun, partial failure and recovery
    (row counts before and after, duplicates found).
  Data quality: rows caught per rule, what slipped through, where
    the rejected rows go.
  Debugging: the exact error, the first wrong guess, the evidence that
    pointed to the root cause.
  Migration: parity checks (counts, sums, checksums per partition)
    and what didn't match.
  Trade-offs: both options measured on the same two or three metrics.
  Business translation: one technical number turned into the number
    a stakeholder reads, with the arithmetic shown.
- Success / failure criterion, written before we run anything.
- Show the design and check it against the SENIOR BAR.

STEP 2. Data source
Pick a free public source that fits the idea and has enough volume or
mess. Never NYC taxi data. Prefer sources a notebook can download over
plain HTTP or a public bucket with no sign-up. Candidates (check that
the current URL works before using it):
- Energy: Open Power System Data time series (load, wind, solar by
  country, 15-60 min), Our World in Data energy dataset (GitHub CSV),
  Ember electricity data.
- Weather / climate: NOAA GHCN daily (public cloud bucket), Open-Meteo
  historical archive API.
- Events at volume: GH Archive hourly JSON (data.gharchive.org),
  Wikimedia pageview dumps (dumps.wikimedia.org).
- City open data via Socrata APIs (e.g. Chicago, Seattle), bike share
  trip files (Citi Bike, Divvy), USGS earthquake feeds, OpenAQ air
  quality (public bucket).
- Built-in samples only if they are real data and fit better than the
  above, and not the taxi samples.
Tell me: source, why it fits, rows and size we'll load, known mess in
it, and the licence line I should credit in the post if needed.

STEP 3. Setup
- Create one isolated place named case_<short_slug>: a schema in Unity
  Catalog, or a Lakehouse / Warehouse in a Fabric workspace. Smallest
  compute that gives a fair measurement.
- Write down every item you create, for cleanup at the end.

STEP 4. Ingest
- Land raw data as-is, with source file and ingest timestamp columns.
- Report row count, size on disk, schema, and the mess we found.
  Add surprises to the FIELD LOG.

STEP 5. Baseline
- Build the baseline exactly as designed. Measure it with the method
  from step 1. Show the cell or screen each number came from.

STEP 6. Change
- Apply the one change. Nothing else changes. Measure the same way.
- If the result contradicts the hypothesis, keep it. A disproved idea
  is a better post than a forced one. Tell me and suggest a new angle.

STEP 7. Production check
- Stress the concern from the SENIOR BAR: rerun the job, inject late or
  duplicate rows, break a schema, revoke a grant, promote through a
  deployment pipeline, whatever fits the lens. Record what happened.

STEP 8. Screenshots
- Name 1-3 screenshots worth posting (a query profile, a before/after
  cell output, a lineage graph, a pipeline run, a monitoring chart).
  For each: what's on it and why it supports the post.
- Before I take them: tell me what to hide or crop (workspace and tenant
  names, emails, user names, IDs, URLs with tenant info).

STEP 9. Evidence pack
Plain text. The draft in step 10 uses this pack and the FIELD LOG, and
nothing else.
- Topic: the idea, rewritten to match what we actually found.
- Plain version: one sentence, under 30 words, no product terms or
  error codes: what happened, why, what fixed it. Example: "Shrinking a
  Spark pool failed because one of its two machines always
  coordinates, so only one can do work, and my config asked for two."
- Real anchor: the decision and at most three numbers. Each with its
  source (cell, screen) and method (runs, warm/cold, compute size).
- What actually happened: 3-5 lines from the FIELD LOG (why I looked,
  what I expected, what I tried first, what broke, what I got wrong,
  what's still unresolved).
- Shape check: does the evidence fit the Shape input? (D needs a
  headline result or number, E a wrong first assumption, C one number
  that carries the point, B a moment worth opening on, A a plain
  problem, fix and cost.) If it fits, say so in one line and go
  straight to step 10. If it doesn't, name the better shape and why,
  and wait for my answer. This is the only stop between here and the
  draft. If I switch, remind me to update the Shape column in the sheet.
- Screenshots: file name and one-line caption for each.
- Data credit line, if the licence asks for one.
- Claims check: list every number in the pack next to where we saw it.
  Remove any number that has no source.

STEP 10. Draft (no new questions)
Write the post from the evidence pack and the FIELD LOG, following
PART 2. Don't ask me anything the case already answered: the topic,
plain version, anchor, story and shape all come from step 9. Don't add
any fact or number that isn't in the pack or the log. If something the
post would need is missing, leave it out and list it in output item 5.

STEP 11. Cleanup list
List every item we created in step 3 onwards and how to delete each one.
Don't delete anything. I'll do it after the post is scheduled.

=====================================================================
PART 2. WRITING RULES (for step 10)
=====================================================================

Goal: stay active and share technical detail. Not brand-building, not
virality.

Reader: a data engineer who knows Spark and SQL but has never used this
exact tool. Senior topic, simple words. If they need two reads, the
draft failed. The post expands the PLAIN VERSION and nothing else.
Use at least one line from "What actually happened".

SHAPES (hard limit for all: at most three paragraphs):
A) Problem → what I did → what it cost me. Three paragraphs.
B) Start mid-action, but the first two sentences say what I was
   trying to do. Two paragraphs.
C) One paragraph, under 90 words, one number, stop.
D) Start with the result or the number, then how I got there.
   Two or three paragraphs.
E) Start with what I got wrong, then the correction.
   Two or three paragraphs.

CLARITY (as important as the BANNED list):
- Setup in the first paragraph: what I was trying to do, in plain
  words. Shapes D and E open with their result or mistake, then give
  the setup in the next sentence.
- Then in order: what broke, what I found, the fix. One job per
  paragraph.
- One idea. A wrong guess or detour gets one sentence, not a paragraph.
- Explain every tool-specific term the first time, in a few plain words.
- At most one raw identifier (error code, API name, setting name). Say
  the others in words ("the API said the executor count was invalid").
- Paragraphs of at most ~70 words. Most sentences under 20 words.
- One plain "so" sentence that says what a fact means is allowed. It is
  not a lesson ending.

ENDING:
- End on the last fact, or on what's still unresolved.
- Only close with a lesson or takeaway if "Lesson ending" is yes.
- Only generalize to other tools or engines if "Generalize" is yes.

NUMBERS:
- At most three numbers in the whole post (shape C: one), all from the
  Claims check.
- Each number must explain the decision. No highlight reel.
- Never more than two numbers in one sentence.
- Don't pair a metric with a second metric just for contrast.

STYLE:
- Active voice. No emojis. No em dashes or double hyphens. No all-caps.
- Contractions are fine. Fragments are fine. Mostly short sentences,
  with an occasional longer one (up to ~25 words) for rhythm.
- Concrete over abstract: tool names, settings, real outcomes. Quote
  at most one error message; describe the rest in words.
- Grounded and senior. Not hype, not motivational.
- Narrow scope: one decision, not a topic overview.

BANNED (these make my posts read as generated):
- Opening with "I built / I tested / I reviewed / I needed to", or any
  opener that announces what I made instead of what happened.
- "The trade-off is..." / "The decision comes down to..." /
  "comes down to" anywhere.
- The "X is not Y, it is Z" negation-reversal, in any form, including
  "the fix isn't X", "the real cost isn't X", "not just X".
- Near-variants that announce a conclusion: "what matters here is",
  "the takeaway", "the part worth keeping", "the lesson".
- Influencer hooks, engagement bait, questions to farm comments,
  bragging about credentials.
- Fabricated numbers or scenarios.
- Employer data, client names, internal tooling. Personal projects or
  safely generalized patterns only.

BEFORE OUTPUT, check the draft and rewrite any hit:
1. Paragraph count is within the shape's limit (never more than three).
2. Number count is within the limit, and every number is in the Claims
   check.
3. No BANNED phrase or near-variant, including in the last sentence.
4. The ending follows the ENDING rules.
5. Length is within 20% of the target.
6. Clarity: reread as the Reader. Every term explained or removed, at
   most one raw identifier, no paragraph over ~70 words, and the first
   paragraph says what I was trying to do.
7. Could the Reader retell the PLAIN VERSION after one read? If not,
   cut detail until they could.

Step 10 output, in this order:
1. The post, as plain text ready to copy.
2. The screenshot to post with it (from step 8).
3. A short note on where the lens shows up.
4. Any term you explained, and any you cut, so I can check them.
5. Anything the post would have used but the case didn't establish.
```
