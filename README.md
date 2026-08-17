# Plain Writing

A prompt and a checker for writing that says the plain thing: status updates, proposals,
release notes, incident writeups, performance reviews, team bios, announcements, and the
pages you write under your own name.

| Artifact | What it is |
|---|---|
| `agent/PLAIN_WRITING.md` | The prompt. Self-contained, model-agnostic. Paste it anywhere. |
| `skills/plain-writing/SKILL.md` | The same rules as a skill, for Claude Code, Amp and opencode. |
| `tools/av_lint.py` | Zero-dependency checker for the mechanical rules. |
| `evals/evals.json` | Seven evals with explicit assertions. |

## The problem

Two failures produce most bad writing, and they look opposite while doing the same damage.

The first is **filler**: language that occupies space without carrying information. *"Going
forward, we are laser-focused on moving the needle for key stakeholders."* Strip the words
and nothing is left.

The second is **the confident blur**: claims pitched so broadly they cannot be checked.
*"A proven track record of delivering transformative outcomes."* It sounds like a fact and
behaves like a mood.

Language models produce both by default, because both are safe. Safe language is
indistinguishable across authors, and a sentence that could have been written by anyone
about anything tells the reader nothing.

## Quick start

**As a prompt**, paste `agent/PLAIN_WRITING.md` into any model's system prompt, custom
instructions, project or Gem. Nothing else is needed: no repository, no scripts, no
attachments. About 4,000 words.

**As a skill**, `skills/plain-writing/SKILL.md` loads automatically on requests like "cut the
fluff" or "write my status update". Mirrors for `.claude/`, `.amp/` and `.opencode/` are kept
byte-identical and verified by the test suite.

**As a check**, run the linter over any draft:

```bash
python3 tools/av_lint.py draft.md
python3 tools/av_lint.py draft.md --profile professional --quiet
python3 tools/av_lint.py --stdin < draft.md
python3 tools/av_lint.py draft.md --json
```

Exit code 0 means the mechanical checks passed. Profiles are `professional` (the default:
work writing), `strict` (short personal copy, bios, taglines), `standard` (longer prose) and
`brand` (company copy).

## What the prompt enforces

- **Lead with the conclusion.** The first sentence carries the point. Context comes after.
- **Never invent a fact.** No date, name, employer, metric or deadline the user did not
  supply. Unknowns become visible `[PLACEHOLDERS]` that get reported back.
- **Never invent a metric.** Figures stay exactly as given, unrounded, with a source named
  where one is needed.
- **Name who does what.** Passive voice is fine when the actor is genuinely irrelevant, and
  wrong when it is hiding a name the reader needs.
- **Replace categories with instances.** Not "various stakeholders" but "the two teams that
  call this API".
- **Preserve meaning under compression.** Cutting filler must never turn "we expect to ship
  in March" into "we ship in March". Any change in certainty is reported.
- **Be candid about the work, not your competence.** "The migration took three weeks longer
  than I estimated" is professional. "I am bad at estimating" is a review you wrote for
  someone else.

Ten document types carry their own register settings, from status update to incident writeup
to speaker bio.

## What the linter checks

| Check | Catches | Blocking |
|---|---|---|
| `banned-lexicon` | 76 marketing phrases: empower, leverage, seamless, transformative | yes |
| `workplace-jargon` | density of corporate filler: circle back, low-hanging fruit (47 terms) | over threshold |
| `suspect-lexicon` | density of inflated modifiers: crucial, robust, comprehensive | over threshold |
| `formulaic-structure` | "whether you're X or Y", "it's not just X, it's Y", "in a world where" | yes |
| `dash-overuse` | em and en dashes over the profile's budget | yes |
| `concrete-anchors` | copy with no real date, count, tool or name in it | yes |
| `fake-precision` | unsourced percentages and multipliers | profile-dependent |
| `rhythm-variation` | uniform sentence length, by coefficient of variation | profile-dependent |
| `unresolved-placeholders` | brackets that would ship silently | warning |
| `quirk-stacking` | more than two competing stylistic conventions | yes |
| `micro-convention` | lines that break a convention you declared | when declared |
| `uniform-openers` | most sentences starting with the same word | warning |
| `rule-of-three` | triad scaffolding | warning |

It deliberately does not judge whether the writing is *true*, whether the facts are yours, or
whether the judgement is sound. Those are the checks that matter most, and they stay human.

## Verification

```bash
python3 tools/test_av_lint.py        # 70 tests: every check, positive and negative
python3 tools/test_framework_sync.py # 29 tests: repository integrity
```

`test_av_lint.py` gives each check a fixture that must trip it and a fixture that must not,
so no check can rot into a no-op or a false-positive machine.

`test_framework_sync.py` enforces the claims this repository makes about itself:

- All three lexicon tiers in the prompt are the same sets as in the checker, and are disjoint.
- Every lexicon entry actually matches itself, so no entry can silently never fire.
- Every skill mirror is byte-identical to the canonical file.
- No document contains an em dash, since they tell other people not to use them.
- The prompt references no file, so it works pasted into a chat window alone.
- Every worked "after" example passes the linter, and every "before" example fails it.
- Every eval declares assertions and a known lint profile.
- Counts stated in this README match the code.
- No casual-social register, slang dial, or text-detection framing is present anywhere.

That last one is a regression test, not a nicety. See below.

## Two calibration decisions

**Rhythm variation does not block work writing.** Measured over fixtures kept in the test
suite, uniform machine-written business prose sits at a coefficient of variation of 0.09 to
0.19, while a terse human status update sits at 0.24. That gap is too narrow to gate on, so
the professional profile reports rhythm rather than failing it. It still blocks on personal
copy, where sentence fragments are actually available to you.

**The jargon budget tolerates an isolated term.** It started at one per 400 words, which
fired on a normal update containing a single "quick win". A checker that cries wolf gets
switched off and then catches nothing. It is now one per 200 words, which still fails
clusters.

## History

This repository previously held a personal-voice writing framework built around research on
machine-text detection, including a casual-social channel with slang and deliberately loose
grammar. That material has been removed. It was fine for a hobby homepage and wrong for
workplace writing: a bio that undercuts your own competence circulates further than you do,
deliberately loose grammar has no place in a document others plan around, and detection
framing reads badly next to a professional name.

The current prompt is a separate artifact rather than a filtered copy of the old one. Tests
assert that the removed material cannot return.

Note that deleted files remain in this repository's git history. If they need to be gone
entirely, that requires rewriting history or starting a fresh repository.

## Licence

Original work.
