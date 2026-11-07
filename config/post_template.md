# LinkedIn post drafting template

Paste into a new chat and fill the [INSERT] fields. Kept in line with
`config/rules.md`, which the Content Reviewer scores posts against.

```
Help me draft a LinkedIn post from my work as a Senior Data Engineer
(Microsoft Fabric, Databricks, SQL, Python, PySpark). Goal: stay active
and share technical detail. Not brand-building, not virality.

Topic: [INSERT]
Lens: [INSERT: Performance / Cost / Reliability / Data quality /
       Debugging / Migration / Trade-offs / Business translation]
Real anchor: [INSERT a decision, number, tool, or situation. If blank,
       ask me 1-2 questions first. Never invent one.]
Shape: [INSERT A-E]
Length: [INSERT ~80 / ~150 / ~220 words]
Lesson ending: [no / yes]          (default no)
Generalize past the tool: [no / yes]   (default no)

BEFORE DRAFTING: ask me what actually happened that isn't in the
technical summary. What I tried first that didn't work, what I got
wrong, what I still don't know, what made me look at this in the first
place. Wait for my answer. Use at least one of those in the post.

SHAPES (hard limit for all: at most three paragraphs):
A) Problem → what I did → what it cost me. Three paragraphs.
B) Start mid-action, no setup. Two paragraphs.
C) One paragraph, under 90 words, one number, stop.
D) Start with the result or the number, then how I got there.
   Two or three paragraphs.
E) Start with what I got wrong, then the correction.
   Two or three paragraphs.

ENDING:
- End on the last fact, or on what's still unresolved.
- Only close with a lesson or takeaway if "Lesson ending" is yes.
- Only generalize to other tools or engines if "Generalize" is yes.

NUMBERS:
- At most three numbers in the whole post (shape C: one).
- Each number must explain the decision. No highlight reel.
- Never more than two numbers in one sentence.
- Don't pair a metric with a second metric just for contrast.

STYLE:
- Active voice. No emojis. No em dashes or double hyphens. No all-caps.
- Contractions are fine. Fragments are fine. Mix 5-word sentences with
  25-word ones on purpose.
- Concrete over abstract: tool names, settings, error messages, real
  outcomes.
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
2. Number count is within the limit.
3. No BANNED phrase or near-variant, including in the last sentence.
4. The ending follows the ENDING rules.
5. Length is within 20% of the target.

Output: plain text ready to copy, then one line on what screenshot
should go with it, then a short note on where the lens shows up.
```
