#!/usr/bin/env python3
"""
make_portable.py : derive the portable edition of the master prompt.

agent/AUTHENTIC_VOICE.md is the single source of truth. The portable edition is
generated from it by applying the transforms declared below, so the two cannot
drift apart: `--check` regenerates and compares, and the framework test suite
fails the build on any mismatch.

The portable edition exists for one situation: somebody has the prompt and
nothing else. Pasted into a chat window, the standard edition tells the reader
to run `python3 tools/av_lint.py`, which they do not have. That instruction is
load-bearing in exactly one place (the guidance for small local models, which
cannot audit themselves reliably), so it is replaced with a manual procedure
rather than deleted.

Every rule, constraint, dial, profile, lexicon entry and example is identical
between the two editions. Only the verification mechanics differ.

Usage:
    python3 tools/make_portable.py            # write the portable edition
    python3 tools/make_portable.py --check    # verify it is up to date
    python3 tools/make_portable.py --diff     # show what would change

Exit codes:
    0  written, or already up to date
    1  --check found the committed file stale
    2  a transform anchor did not match exactly once
"""

from __future__ import annotations

import argparse
import difflib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "agent", "AUTHENTIC_VOICE.md")
TARGET = os.path.join(ROOT, "agent", "AUTHENTIC_VOICE_PORTABLE.md")

# Each transform is (label, exact_anchor, replacement). Anchors must appear
# exactly once in the source; anything else is a build error rather than a
# silent partial rewrite.
TRANSFORMS = [
    (
        "header",
        """# AUTHENTIC VOICE : Master Agent Prompt

**Version 2.0.0** | Portable across Claude, GPT, Gemini, Llama, Mistral and local models.
Paste this whole file as a system prompt, a custom instruction, a project file, or the first
message of a chat. It is self-contained: no tools, no network, no attachments required.
""",
        """# AUTHENTIC VOICE : Master Agent Prompt (Portable Edition)

**Version 2.0.0-portable** | Works on Claude, GPT, Gemini, Llama, Mistral and local models.
Paste this whole file as a system prompt, a custom instruction, a project file, or the first
message of a chat. It is self-contained: no tools, no network, no attachments, no repository.

Every rule, constraint, dial, channel profile, lexicon entry and worked example here is
identical to the standard edition. The only difference is that this one assumes you have this
file and nothing else, so it never asks you to run a script you do not have. If you do have
the full repository, use the standard edition and run the automated checker instead.
""",
    ),
    (
        "section-7.2",
        """### 7.2 Machine verification (optional, recommended)

The repository ships `tools/av_lint.py`, a zero-dependency checker for the mechanical subset
of the rules above: banned lexicon, dash budget, rhythm variation, fake precision, formulaic
scaffolding, quirk stacking and concrete anchors.

```
python3 tools/av_lint.py draft.md --profile strict
python3 tools/av_lint.py --stdin --profile discord < draft.md
python3 tools/av_lint.py draft.md --profile strict --convention '^[^A-Z]*$'
```

Exit code 0 means the mechanical checks passed. It cannot tell you whether the copy is
*true*, whether it sounds like the person, or whether the facts are theirs. Those stay human
judgements, and they are the ones that matter most.
""",
        """### 7.2 Verifying by hand

Here you are the checker. Work section 7.1 as a literal pass over the draft, one check at a
time, rather than reading the whole thing once and declaring it fine. An impression-based
read is precisely what lets the safe register through.

Three checks are mechanical enough to do by counting, and they are the three a model is most
likely to skip when grading its own work:

- **Count the dashes.** Search the draft for the em dash and the en dash specifically.
  Personal copy allows zero. Other copy allows one per page. Do not estimate; search.
- **Count the sentence lengths.** Write down the word count of each sentence in a paragraph.
  If they cluster within a few words of each other, the rhythm is machine-flat. Cut one
  sentence in half and let another run long.
- **Check section 9.1 term by term.** Read the banned list literally rather than scanning the
  draft for the general feeling of marketing language. The entries you would not have noticed
  on a normal read are exactly the ones that survive one.

None of this tells you whether the copy is *true*, whether it sounds like the person, or
whether the facts are theirs. Those stay human judgements, and they are the ones that matter
most.
""",
    ),
    (
        "section-9.1-preamble",
        """The block below is the single source of truth for banned wording. It is byte-for-byte the
same set as the `BANNED` and `SUSPECT` lexicons in `tools/av_lint.py`, and
`tools/test_framework_sync.py` fails the build if the two ever drift apart. Matching is
case-insensitive and anchored on word boundaries.""",
        """The block below is the single source of truth for banned wording. Matching is
case-insensitive and anchored on word boundaries.""",
    ),
    (
        "local-model-guidance",
        """- **Open and local models (Llama, Mistral, Qwen):** smaller models drift back to the safe
  register after a few turns. Two mitigations: keep Sections 3.1 and 9 in-context, and run
  `tools/av_lint.py` on every draft, since a small model will not audit itself reliably.""",
        """- **Open and local models (Llama, Mistral, Qwen):** smaller models drift back to the safe
  register after a few turns, and they will not reliably audit their own output. Two
  mitigations: keep Sections 3.1 and 9 in-context, and run section 7.2 over every draft
  yourself rather than accepting the model's own verdict that it passed.""",
    ),
    (
        "footer",
        """prompt-shaped structural regularities found in AI-generated social text. Sources are indexed
in `research-papers-index.md`; every paper is cited under its own licence and no paper text
is reproduced here.*""",
        """prompt-shaped structural regularities found in AI-generated social text. Every source is
cited under its own licence and no paper text is reproduced here.*""",
    ),
]

# The portable edition must not reference anything outside itself.
FORBIDDEN_SUBSTRINGS = ["tools/", ".py", "research-papers-index", "the repository ships"]


def build(source_text: str) -> str:
    out = source_text
    for label, anchor, replacement in TRANSFORMS:
        count = out.count(anchor)
        if count != 1:
            raise SystemExit(
                "make_portable: transform %r matched %d times, expected exactly 1.\n"
                "The master prompt changed under it. Update TRANSFORMS." % (label, count)
            )
        out = out.replace(anchor, replacement)
    return out


def audit(text: str):
    """Return the list of self-containment violations in the generated file."""
    problems = []
    lowered = text.lower()
    for bad in FORBIDDEN_SUBSTRINGS:
        if bad.lower() in lowered:
            problems.append("references %r, which a standalone reader does not have" % bad)
    for dash, name in (("—", "em dash"), ("–", "en dash")):
        if dash in text:
            problems.append("contains a %s, which the framework itself bans" % name)
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="make_portable.py")
    ap.add_argument("--check", action="store_true", help="verify the committed file is current")
    ap.add_argument("--diff", action="store_true", help="print a unified diff of pending changes")
    args = ap.parse_args(argv)

    with open(SOURCE, "r", encoding="utf-8") as fh:
        generated = build(fh.read())

    problems = audit(generated)
    if problems:
        for p in problems:
            print("make_portable: self-containment failure: %s" % p, file=sys.stderr)
        return 2

    existing = None
    if os.path.exists(TARGET):
        with open(TARGET, "r", encoding="utf-8") as fh:
            existing = fh.read()

    if args.diff:
        diff = difflib.unified_diff(
            (existing or "").splitlines(True), generated.splitlines(True),
            fromfile="committed", tofile="generated",
        )
        sys.stdout.writelines(diff)
        return 0

    if args.check:
        if existing == generated:
            print("make_portable: %s is up to date" % os.path.relpath(TARGET, ROOT))
            return 0
        print("make_portable: %s is STALE; run tools/make_portable.py"
              % os.path.relpath(TARGET, ROOT), file=sys.stderr)
        return 1

    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(generated)
    print("make_portable: wrote %s (%d lines)"
          % (os.path.relpath(TARGET, ROOT), generated.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
