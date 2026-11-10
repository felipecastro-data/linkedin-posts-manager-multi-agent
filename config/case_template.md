# LinkedIn case building template

Use it before `config/post_template.md`. Open a Databricks or Fabric tab,
open Claude in Chrome on it, paste the prompt and fill the [INSERT] fields.
The case it produces becomes the "Real anchor" of the post.

```
You are pairing with me, a Senior Data Engineer, inside my browser on
Databricks or Microsoft Fabric. Together we build one small but
production-grade case that proves or disproves a single LinkedIn post
idea, on real public data, inside a time box. What it produces is
measured evidence and screenshots that I will turn into a post with my
drafting template. I delete everything after the post is scheduled.

Idea: [INSERT the topic sentence from the Posts Schedule]
Pillar: [INSERT]
Lens: [INSERT: Performance / Cost / Reliability / Data quality /
       Debugging / Migration / Trade-offs / Business translation]
Platform: [INSERT Databricks / Fabric / you pick]
Time box: [INSERT minutes, default 45, hard max 60]

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
- Keep a running FIELD LOG from step 1: everything that failed, surprised
  us, or that I got wrong, with the exact error text. This log is the
  most valuable output. Don't tidy it.
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

STEP 9. Evidence pack (final output)
Plain text, ready to paste into my drafting template:
- Topic: the idea, rewritten to match what we actually found.
- Lens:
- Plain version: one sentence, under 30 words, no product terms or
  error codes: what happened, why, what fixed it.
- Real anchor: the decision and at most three numbers. Each with its
  source (cell, screen) and method (runs, warm/cold, compute size).
- What actually happened: 3-5 lines from the FIELD LOG (what I tried
  first, what broke, what I got wrong, what's still unresolved).
- Suggested shape (A-E from the drafting template) and why.
- Screenshots: file name and one-line caption for each.
- Data credit line, if the licence asks for one.
- Claims check: list every number in the pack next to where we saw it.
  Remove any number that has no source.

STEP 10. Cleanup list
List every item we created in step 3 onwards and how to delete each one.
Don't delete anything. I'll do it after the post is scheduled.
```
