# Authentic Voice

A reusable framework for writing copy that reads as one specific human being, rather than as
a language model doing its best impression of a landing page.

It ships as four things you can use independently:

| Artifact | What it is | Use it when |
|---|---|---|
| `agent/AUTHENTIC_VOICE.md` | The full master prompt. Model-agnostic, self-contained. | You want a standalone agent. Paste it as a system prompt anywhere. |
| `agent/SYSTEM_PROMPT.txt` | The enforcement core, condensed. | Your system-prompt budget is small. |
| `agent/INTAKE.md` | The fact-gathering questionnaire. | Before writing anything for a real person. |
| `skills/authentic-voice/SKILL.md` | Claude Code / Amp / opencode skill. | You want it to load automatically on relevant requests. |
| `tools/av_lint.py` | Zero-dependency checker for the mechanical rules. | Every draft, and in CI. |

## The problem

Language models optimise for inoffensiveness, and inoffensiveness converges. Ask any model
for a personal bio and it reaches for the same sentence: *"Empowering developers to build the
future."* That line is not bad because it is ugly. It is bad because it is identical across
ten thousand authors and therefore carries no information about any of them.

A human page is the residue of one person's constraints: what they actually did, what
actually broke, what they are willing to admit. This framework's whole job is to pull that
residue in and then get out of the way.

## Quick start

**As a standalone agent**, paste `agent/AUTHENTIC_VOICE.md` into any model's system prompt,
custom instructions, project or Gem. Then ask for the copy you want.

**As a skill**, the `skills/authentic-voice/SKILL.md` file loads automatically on requests
like "make this sound human" or "write my about page". Mirrors for `.claude/`, `.amp/` and
`.opencode/` are kept byte-identical and are verified by the test suite.

**As a check**, run the linter over any draft:

```bash
python3 tools/av_lint.py draft.md --profile strict
python3 tools/av_lint.py --stdin --profile discord < draft.md
python3 tools/av_lint.py draft.md --profile strict --convention '^[^A-Z]*$'
python3 tools/av_lint.py draft.md --json
```

Exit code 0 means the mechanical checks passed. Profiles are `strict` (personal site, bio,
tagline), `standard` (README, longer prose), `discord` (casual social) and `brand` (company
copy).

## What the linter checks

| Check | Catches | Blocking |
|---|---|---|
| `banned-lexicon` | 76 marketing and AI-register phrases | yes |
| `formulaic-structure` | "whether you're X or Y", "it's not just X, it's Y", "in a world where" | yes |
| `dash-overuse` | em and en dashes over the profile's budget | yes |
| `burstiness` | uniform sentence rhythm, by coefficient of variation | yes |
| `concrete-anchors` | copy with no real date, count, tool or name in it | yes |
| `fake-precision` | unsourced percentages and multipliers | profile-dependent |
| `suspect-lexicon` | density of AI-favoured modifiers | over threshold |
| `quirk-stacking` | more than two competing stylistic conventions | yes |
| `discourse-markers` | casual markers missing where the channel expects them | discord only |
| `micro-convention` | lines that break a convention you declared | when declared |
| `uniform-openers` | most sentences starting with the same word | warning |
| `rule-of-three` | triad scaffolding | warning |

It deliberately does not judge whether the copy is *true*, or whether it sounds like the
person. Those are the checks that matter most, and they stay human.

## Verification

```bash
python3 tools/test_av_lint.py        # 64 tests: every check, positive and negative
python3 tools/test_framework_sync.py # 25 tests: framework integrity, see below
```

`test_av_lint.py` gives each check a fixture that must trip it and a fixture that must not,
so no check can rot into a no-op or a false-positive machine.

`test_framework_sync.py` enforces the claims this repository makes about itself:

- The banned lexicon in the master prompt is the same set as the one in the linter. If either
  drifts, the build fails.
- Every skill mirror is byte-identical to the canonical file.
- No framework document contains an em dash, since they tell other people not to use them.
- Every worked "after" example passes the linter, and every "before" example fails it.
- Every eval declares assertions and a lint profile.
- The paper count claimed in this README equals the number of PDFs on disk.
- No file promises an outcome against an AI detector.

### Measured effect on the sample corpus

Running the linter over the six stored eval outputs in `authentic-voice-workspace/`:

| Configuration | Passing |
|---|---|
| With the skill | 3 of 3 |
| Without the skill | 0 of 3 |

The without-skill outputs fail on em dash usage (evals 1 and 3) and on having no concrete
anchor at all (eval 2). This is a mechanical measurement of mechanical properties, on three
samples. It is not a claim about how the copy reads, and the sample is far too small to
support a percentage.

## Research foundation

Built on **4 peer-reviewed research papers** on the measurable differences between human and
machine text. The craft rules map onto findings, not onto intuition:

| Paper | Finding used | Rule it supports |
|---|---|---|
| `arxiv-2306.05524.pdf` | GPABench2, 2.8M comparative samples. Polished text is hardest to separate from human. | Why light editing of model prose is not enough |
| `arxiv-2401.04120-Discord-Detection.pdf` | n=335. AI social text clusters around prompt-shaped structure, notably fixed sentence counts. | Casual-channel rules, section 6.1 |
| `arxiv-2510.05136-AIGT-Survey.pdf` | 8 domains, 11 models. Human text shows greater variability; newer models homogenise. | Burstiness, lexical variety |
| `uncovered-kdir2023.pdf` | Stylometry separates AI news text at 70.4% accuracy, weighted F1 85.6%. | Why style, not topic, is the signal |

Full index, licences and per-paper findings: `research-papers-index.md`. Every paper is used
under its own licence, and no paper text is reproduced in this repository.

**On the numbers:** the 2.8M figure is the sample count of one benchmark, not an aggregate
across all four papers. Earlier versions of this README claimed seven papers and implied the
sample counts combined. They do not, and they did not.

## Scope and limits

This framework produces copy that reads as human. It makes **no claim about the behaviour of
any AI-detection tool**, and nothing here should be presented as doing so. Detector behaviour
is unstable, varies by vendor, and is not the objective.

Do not use it for reference documentation, safety or legal or medical notices, error
messages, or anywhere a reader must certify they wrote the text themselves. The master prompt
states this as a hard constraint and refuses those requests.

The most common misuse is overcorrection: applying a lowercase, slangy register to someone
whose actual voice is nothing like that. A surgeon's bio in Discord voice is a costume, not
authenticity. The register dials in section 5 of the master prompt exist to prevent this, and
eval 5 tests for it.

## Layout

```
agent/
  AUTHENTIC_VOICE.md      master prompt, portable, self-contained
  SYSTEM_PROMPT.txt       condensed enforcement core
  INTAKE.md               fact-gathering questionnaire
skills/authentic-voice/   canonical skill
.claude/ .amp/ .opencode/ byte-identical mirrors
tools/
  av_lint.py              the checker
  test_av_lint.py         64 tests over the checker
  test_framework_sync.py  25 tests over the framework itself
evals/evals.json          6 evals with explicit assertions
research papers/          4 source PDFs
research-papers-index.md  index, licences, findings
authentic-voice-workspace/ stored eval runs and review tooling
```

## Licence and attribution

Research papers are used under their own licences (arXiv CC BY 4.0; SciTePress open access)
and are not redistributed as text. The framework, linter and tests in this repository are
original work.
