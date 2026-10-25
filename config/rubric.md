# Content scoring rubric

Scores reflect content quality for a senior data engineering audience.
Reactions, comments, reposts and impressions are recorded for context and
carry no weight.

Each dimension is scored 1-5 with a one-line note. Score = average of the
dimensions used, rounded to one decimal.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Senior depth** | Restates docs or a beginner tutorial. | Correct and useful, but a senior DE would mostly know it. | A senior DE learns something past the first page of the docs: a failure mode, a limit, a non-obvious setting or interaction. |
| **Specificity** | Abstract; no tool, setting or number. | Names the tool and the technique, few concrete details. | Concrete numbers, configs, tool and version names, a real observed outcome. |
| **Narrow scope** | Topic overview or listicle. | One topic with a few sub-points. | One decision, one bug or one setting, followed through. |
| **Credibility** | Numbers or scenario look invented, or relies on employer/client material. | Plausible but not clearly reproducible. | Grounded in something reproducible in a personal setup; numbers trace to a test. |
| **Voice** | Several banned patterns, hype or bait (see `rules.md`). | One or two slips. | Fully follows `rules.md`; problem-first, no hype. |

## Where each dimension applies

| Used by | On | Dimensions | Threshold |
|---|---|---|---|
| Content Reviewer | posted posts (full text) | all 5 | none; feedback only |
| Editor | proposed ideas (topic + test) | depth, specificity, scope, credibility, as *potential* | average >= 3.5, no dimension below 3 |

For ideas, "specificity" asks whether the topic names a concrete tool,
setting or failure, and whether its `test` can produce a real number.
