# Authentic Voice

A reusable framework for writing copy that reads as one specific human being, rather than as
a language model doing its best impression of a landing page.

It ships as four things you can use independently:

| Artifact | What it is | Use it when |
|---|---|---|
| `agent/PLAIN_WRITING.md` | **Work-safe prompt.** Plain-language writing for status updates, proposals, release notes, reviews, bios. No slang, no casual-social register, no AI-detection framing. | Writing at work, or under your own name. Start here. |
| `agent/AUTHENTIC_VOICE.md` | The personal-voice master prompt. Informal register, casual-social rules. | Personal sites and hobby projects only. See the scope warning below. |
| `agent/AUTHENTIC_VOICE_PORTABLE.md` | The same prompt, generated, with no repository references. | You are handing the prompt to someone who has only that file. |
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

**Handing it to someone else**, send `agent/AUTHENTIC_VOICE_PORTABLE.md` instead. It is
generated from the master by `tools/make_portable.py` and is identical in every rule,
constraint, dial, channel profile, lexicon entry and worked example. The only difference is
that it never instructs the reader to run a script from a repository they may not have: the
optional linter section becomes a manual counting procedure, and the guidance for small local
models points at that procedure rather than at a file. The test suite proves the two editions
differ in exactly three section bodies and two headings, and nowhere else.

```bash
python3 tools/make_portable.py          # regenerate after editing the master
python3 tools/make_portable.py --check  # fail if the committed copy is stale
python3 tools/make_portable.py --diff   # show pending changes
```

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

Exit code 0 means the mechanical checks passed. Profiles are `professional` (work writing:
status updates, proposals, release notes, reviews, bios), `strict` (personal site, bio,
tagline), `standard` (README, longer prose), `brand` (company copy) and `discord` (casual
social).

## What the linter checks

| Check | Catches | Blocking |
|---|---|---|
| `banned-lexicon` | 76 marketing and AI-register phrases | yes |
| `formulaic-structure` | "whether you're X or Y", "it's not just X, it's Y", "in a world where" | yes |
| `dash-overuse` | em and en dashes over the profile's budget | yes |
| `burstiness` | uniform sentence rhythm, by coefficient of variation | profile-dependent |
| `concrete-anchors` | copy with no real date, count, tool or name in it | yes |
| `fake-precision` | unsourced percentages and multipliers | profile-dependent |
| `suspect-lexicon` | density of inflated modifiers | over threshold |
| `workplace-jargon` | density of corporate filler (`circle back`, `low-hanging fruit`, 47 terms) | over threshold |
| `quirk-stacking` | more than two competing stylistic conventions | yes |
| `discourse-markers` | casual markers missing where the channel expects them | discord only |
| `micro-convention` | lines that break a convention you declared | when declared |
| `uniform-openers` | most sentences starting with the same word | warning |
| `rule-of-three` | triad scaffolding | warning |

It deliberately does not judge whether the copy is *true*, or whether it sounds like the
person. Those are the checks that matter most, and they stay human.

## Verification

```bash
python3 tools/test_av_lint.py        # 72 tests: every check, positive and negative
python3 tools/test_framework_sync.py # 48 tests: framework integrity, see below
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
- The portable edition is current, contains no repository references, and differs
  from the master only in the three section bodies and two headings declared in
  `tools/make_portable.py`.

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

## Which prompt to use

**Use `agent/PLAIN_WRITING.md` for work, and for anything under your own name.** It covers
status updates, proposals, release notes, incident writeups, performance reviews, team bios,
announcements and personal profiles. Its rules are ordinary craft: lead with the conclusion,
name the actor, prefer the concrete noun, keep numbers honest, cut filler.

**`agent/AUTHENTIC_VOICE.md` is the personal-voice prompt, and it is not work-safe.** It
carries a casual-social channel with slang and deliberately loose grammar, defaults toward
self-deprecation, and is framed around research on AI-text detection. That framing is fine
for a hobby homepage and wrong for a workplace: a bio that undercuts your own competence
circulates, and a tool that reads as detector evasion is not something to have near your
name professionally. Its register dials and eval 5 limit the damage, but the safer answer at
work is to use the other file.

The two do not share text. `PLAIN_WRITING.md` is a separate artifact with its own rules,
examples and audit gate, not a filtered copy.

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
  PLAIN_WRITING.md        work-safe prompt, self-contained
  AUTHENTIC_VOICE.md      personal-voice prompt, self-contained
  AUTHENTIC_VOICE_PORTABLE.md  generated, zero repository references
  SYSTEM_PROMPT.txt       condensed enforcement core
  INTAKE.md               fact-gathering questionnaire
skills/authentic-voice/   canonical skill
.claude/ .amp/ .opencode/ byte-identical mirrors
tools/
  av_lint.py              the checker
  make_portable.py        derives the portable edition from the master
  test_av_lint.py         72 tests over the checker
  test_framework_sync.py  48 tests over the framework itself
evals/evals.json          6 evals with explicit assertions
research papers/          4 source PDFs
research-papers-index.md  index, licences, findings
authentic-voice-workspace/ stored eval runs and review tooling
```

## Licence and attribution

Research papers are used under their own licences (arXiv CC BY 4.0; SciTePress open access)
and are not redistributed as text. The framework, linter and tests in this repository are
original work.
