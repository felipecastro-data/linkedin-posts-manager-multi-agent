# LinkedIn post drafting template

Paste into a new chat and fill the [INSERT] fields. Build the case
first with `config/case_template.md`; its evidence pack fills Topic,
Lens, Plain version and Real anchor, and answers the BEFORE DRAFTING
question. Kept in line with `config/rules.md`, which the Content
Reviewer scores posts against (Clarity is one of its six dimensions).

```
Help me draft a LinkedIn post from my work as a Senior Data Engineer
(Microsoft Fabric, Databricks, SQL, Python, PySpark). Goal: stay active
and share technical detail. Not brand-building, not virality.

Reader: a data engineer who knows Spark and SQL but has never used this
exact tool. Senior topic, simple words. If they need two reads, the
draft failed.

Topic: [INSERT]
Lens: [INSERT: Performance / Cost / Reliability / Data quality /
       Debugging / Migration / Trade-offs / Business translation]
Plain version: [INSERT from the evidence pack, or leave blank and
       write one below]
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

THEN, still before drafting, write or tighten the PLAIN VERSION and
show it to me:
one sentence, under 30 words, no product terms or error codes, that says
what happened, why, and what fixed it. Example: "Shrinking a Spark pool
failed because one of its two machines always coordinates, so only one
can do work, and my config asked for two." Wait for my OK. The post
expands this sentence and nothing else.

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
- At most three numbers in the whole post (shape C: one).
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
2. Number count is within the limit.
3. No BANNED phrase or near-variant, including in the last sentence.
4. The ending follows the ENDING rules.
5. Length is within 20% of the target.
6. Clarity: reread as the Reader. Every term explained or removed, at
   most one raw identifier, no paragraph over ~70 words, and the first
   paragraph says what I was trying to do.
7. Could the Reader retell the PLAIN VERSION after one read? If not,
   cut detail until they could.

Output, in this order:
1. The PLAIN VERSION.
2. The post, as plain text ready to copy.
3. One line on what screenshot should go with it.
4. A short note on where the lens shows up.
5. Any term you explained, and any you cut, so I can check them.
```
