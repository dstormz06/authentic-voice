#!/usr/bin/env python3
"""
test_framework_sync.py : integrity tests for the Authentic Voice framework.

av_lint's own suite proves the checker works. This suite proves the *framework*
is internally consistent, which is the failure mode that actually bit the
previous version of this repo: four copies of the skill drifted apart, the
README claimed sources that were not on disk, and the document that bans em
dashes was itself written with twenty-five of them.

Every claim these tests enforce is a claim the framework makes in prose
somewhere. If a claim cannot be tested, it should not be made.

Run:  python3 tools/test_framework_sync.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import av_lint  # noqa: E402
from av_lint import lint  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MASTER_PROMPT = os.path.join(ROOT, "agent", "AUTHENTIC_VOICE.md")
SYSTEM_PROMPT = os.path.join(ROOT, "agent", "SYSTEM_PROMPT.txt")
INTAKE = os.path.join(ROOT, "agent", "INTAKE.md")
CANONICAL_SKILL = os.path.join(ROOT, "skills", "authentic-voice", "SKILL.md")
SKILL_MIRRORS = [
    os.path.join(ROOT, ".claude", "skills", "authentic-voice", "SKILL.md"),
    os.path.join(ROOT, ".amp", "skills", "authentic-voice", "SKILL.md"),
    os.path.join(ROOT, ".opencode", "skills", "authentic-voice", "SKILL.md"),
]
EVALS = os.path.join(ROOT, "evals", "evals.json")
README = os.path.join(ROOT, "README.md")
PAPERS_DIR = os.path.join(ROOT, "research papers")
PAPERS_INDEX = os.path.join(ROOT, "research-papers-index.md")

EM_DASH = "—"
EN_DASH = "–"


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def parse_lexicon_block(text: str, header: str):
    """Pull one '# header' group out of the fenced lexicon block in section 9.1."""
    fence = re.search(r"```text\n(.*?)\n```", text, re.DOTALL)
    if not fence:
        raise AssertionError("no fenced lexicon block found in the master prompt")
    body = fence.group(1)
    groups = {}
    current = None
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("#"):
            current = line.lstrip("#").strip()
            groups[current] = []
        elif line and current is not None:
            groups[current].append(line)
    for name, lines in groups.items():
        if name.startswith(header):
            joined = " ".join(lines)
            return [t.strip() for t in joined.split(",") if t.strip()]
    raise AssertionError("lexicon group %r not found; saw %s" % (header, list(groups)))


class TestLexiconSync(unittest.TestCase):
    """Section 9.1 claims to be the same set as the linter. Prove it."""

    def setUp(self):
        self.text = read(MASTER_PROMPT)

    def test_banned_lexicon_matches_exactly(self):
        doc = parse_lexicon_block(self.text, "banned lexicon")
        self.assertEqual(
            sorted(doc), sorted(av_lint.BANNED),
            "master prompt banned list has drifted from av_lint.BANNED",
        )

    def test_suspect_lexicon_matches_exactly(self):
        doc = parse_lexicon_block(self.text, "density tells")
        self.assertEqual(
            sorted(doc), sorted(av_lint.SUSPECT),
            "master prompt density list has drifted from av_lint.SUSPECT",
        )

    def test_no_duplicate_entries_in_lexicons(self):
        self.assertEqual(len(av_lint.BANNED), len(set(av_lint.BANNED)))
        self.assertEqual(len(av_lint.SUSPECT), len(set(av_lint.SUSPECT)))

    def test_every_banned_entry_actually_matches_itself(self):
        # A malformed entry (stray punctuation, double space) would silently
        # never fire. Each pattern must at minimum match its own text.
        for phrase, pattern in av_lint.BANNED_PATTERNS:
            with self.subTest(phrase=phrase):
                self.assertTrue(pattern.search(phrase), "pattern never matches: %r" % phrase)

    def test_every_suspect_entry_actually_matches_itself(self):
        for phrase, pattern in av_lint.SUSPECT_PATTERNS:
            with self.subTest(phrase=phrase):
                self.assertTrue(pattern.search(phrase), "pattern never matches: %r" % phrase)


class TestPracticeWhatYouPreach(unittest.TestCase):
    """The framework bans em dashes in copy. Its own files must comply."""

    FILES = [MASTER_PROMPT, SYSTEM_PROMPT, INTAKE, CANONICAL_SKILL, README]

    def test_no_em_or_en_dashes_in_framework_documents(self):
        for path in self.FILES:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                text = read(path)
                self.assertEqual(text.count(EM_DASH), 0, "em dash present")
                self.assertEqual(text.count(EN_DASH), 0, "en dash present")

    def test_no_unexpanded_shell_or_placeholders(self):
        # The old repo shipped a literal "$(date +%Y-%m-%d)" and a
        # "Last updated: update complete" placeholder.
        patterns = [r"\$\(date", r"<model-name>", r"<path/to/skill>", r"update complete"]
        for path in self.FILES + [PAPERS_INDEX]:
            text = read(path)
            for pat in patterns:
                with self.subTest(path=os.path.relpath(path, ROOT), pattern=pat):
                    self.assertIsNone(re.search(pat, text), "unexpanded placeholder %r" % pat)


class TestSkillMirrors(unittest.TestCase):
    """Four copies of the skill previously drifted. They must stay identical."""

    def test_all_mirrors_exist(self):
        for path in SKILL_MIRRORS:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertTrue(os.path.isfile(path), "missing mirror")

    def test_all_mirrors_are_byte_identical_to_canonical(self):
        canonical = read(CANONICAL_SKILL)
        for path in SKILL_MIRRORS:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertEqual(read(path), canonical, "mirror has drifted from canonical")

    def test_frontmatter_is_wellformed(self):
        text = read(CANONICAL_SKILL)
        self.assertTrue(text.startswith("---\n"), "skill must open with YAML frontmatter")
        end = text.index("\n---\n", 4)
        block = text[4:end]
        self.assertRegex(block, r"(?m)^name:\s*authentic-voice\s*$")
        self.assertRegex(block, r"(?m)^description:\s*\S")

    def test_file_ends_with_newline(self):
        # The old canonical file had no trailing newline, which is why three
        # mirrors showed a spurious final-line diff.
        for path in [CANONICAL_SKILL] + SKILL_MIRRORS:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertTrue(read(path).endswith("\n"), "no trailing newline")


class TestWorkedExamples(unittest.TestCase):
    """Every 'After' example in the master prompt must pass its own linter."""

    def _after_blocks(self):
        """Return (profile, copy) for each worked example.

        Each example heading declares the channel profile its output targets,
        because a README blurb and a personal bio are not held to the same
        anchor count or dash budget.
        """
        text = read(MASTER_PROMPT)
        heading = re.compile(r"^###\s+[A-Z]\..*\(profile:\s*(\w+)\)\s*$")
        marker = re.compile(r"^\*After\b")
        blocks, capture, current, profile = [], False, [], None
        for line in text.splitlines():
            found = heading.match(line)
            if found:
                profile = found.group(1)
                continue
            if marker.match(line):
                capture, current = True, []
                continue
            if capture:
                if line.startswith(">"):
                    current.append(line.lstrip("> ").rstrip())
                elif current:
                    blocks.append((profile, "\n".join(current)))
                    capture, current = False, []
        if current:
            blocks.append((profile, "\n".join(current)))
        return blocks

    def test_examples_are_discoverable(self):
        self.assertGreaterEqual(len(self._after_blocks()), 3, "expected 3 worked examples")

    def test_every_example_declares_a_known_profile(self):
        for i, (profile, _) in enumerate(self._after_blocks(), start=1):
            with self.subTest(example=i):
                self.assertIn(profile, av_lint.PROFILES, "example %d has no profile" % i)

    def test_every_after_example_passes_its_profile(self):
        for i, (profile, block) in enumerate(self._after_blocks(), start=1):
            with self.subTest(example=i, profile=profile):
                report = lint(block, profile=profile)
                failing = {f["check"] for f in report["findings"] if f["severity"] == "error"}
                self.assertTrue(report["passed"], "example %d fails: %s" % (i, failing))

    def test_before_examples_would_fail(self):
        # The contrast is the whole point of the section.
        text = read(MASTER_PROMPT)
        befores, capture, current = [], False, []
        for line in text.splitlines():
            if line.startswith("*Before:*"):
                capture, current = True, []
                continue
            if capture:
                if line.startswith(">"):
                    current.append(line.lstrip("> ").rstrip())
                elif current:
                    befores.append(" ".join(current))
                    capture, current = False, []
        self.assertGreaterEqual(len(befores), 3)
        for i, block in enumerate(befores, start=1):
            with self.subTest(example=i):
                self.assertFalse(lint(block, profile="strict")["passed"],
                                 "'before' example %d unexpectedly passes" % i)


class TestEvals(unittest.TestCase):
    def setUp(self):
        with open(EVALS, "r", encoding="utf-8") as fh:
            self.data = json.load(fh)

    def test_schema(self):
        self.assertEqual(self.data["skill_name"], "authentic-voice")
        self.assertIn("evals", self.data)
        self.assertGreaterEqual(len(self.data["evals"]), 3)

    def test_every_eval_has_assertions(self):
        # The old evals.json shipped "assertions": [] on every case, so the
        # grading reports had no source of truth behind them.
        for ev in self.data["evals"]:
            with self.subTest(eval_id=ev.get("id")):
                self.assertTrue(ev.get("assertions"), "eval has no assertions")

    def test_every_eval_declares_a_profile(self):
        for ev in self.data["evals"]:
            with self.subTest(eval_id=ev.get("id")):
                self.assertIn(ev.get("lint_profile"), av_lint.PROFILES)

    def test_ids_are_unique(self):
        ids = [ev["id"] for ev in self.data["evals"]]
        self.assertEqual(len(ids), len(set(ids)))


class TestNumericClaims(unittest.TestCase):
    """Counts stated in prose must match the code. v1 shipped a README that
    claimed seven papers over four files; this is that bug class, fenced off."""

    def test_banned_phrase_count_claim(self):
        claimed = re.search(r"\|\s*`banned-lexicon`\s*\|\s*(\d+)\s+marketing", read(README))
        self.assertIsNotNone(claimed, "README must state the banned phrase count")
        self.assertEqual(int(claimed.group(1)), len(av_lint.BANNED))

    def test_declared_test_counts_match_reality(self):
        readme = read(README)
        for path, label in ((os.path.join(ROOT, "tools", "test_av_lint.py"), "test_av_lint.py"),
                            (os.path.join(ROOT, "tools", "test_framework_sync.py"),
                             "test_framework_sync.py")):
            claimed = re.search(re.escape(label) + r"\s+#?\s*(\d+) tests", readme)
            self.assertIsNotNone(claimed, "README states no test count for %s" % label)
            loader = unittest.defaultTestLoader.discover(
                os.path.dirname(path), pattern=os.path.basename(path), top_level_dir=os.path.dirname(path)
            )
            with self.subTest(suite=label):
                self.assertEqual(int(claimed.group(1)), loader.countTestCases(),
                                 "README test count for %s is stale" % label)

    def test_profile_names_documented_in_readme(self):
        readme = read(README)
        for name in av_lint.PROFILES:
            with self.subTest(profile=name):
                self.assertIn("`%s`" % name, readme, "profile %r undocumented" % name)


class TestSourceClaims(unittest.TestCase):
    """The README previously claimed seven papers while shipping four."""

    def test_paper_count_claim_matches_disk(self):
        on_disk = sorted(f for f in os.listdir(PAPERS_DIR) if f.lower().endswith(".pdf"))
        readme = read(README)
        claimed = re.search(r"\*\*(\d+)\s+peer-reviewed research papers?\*\*", readme)
        self.assertIsNotNone(claimed, "README must state its paper count explicitly")
        self.assertEqual(int(claimed.group(1)), len(on_disk),
                         "README paper count does not match %s" % on_disk)

    def test_every_indexed_paper_exists_on_disk(self):
        index = read(PAPERS_INDEX)
        on_disk = {f for f in os.listdir(PAPERS_DIR) if f.lower().endswith(".pdf")}
        for name in re.findall(r"\b([\w.\-]+\.pdf)\b", index):
            with self.subTest(paper=name):
                self.assertIn(name, on_disk, "indexed paper missing from disk")

    def test_no_detector_evasion_promises(self):
        # Hard Constraint 5. The old README asserted the output "would likely
        # not trigger AI detectors", which is a claim nobody can stand behind.
        forbidden = re.compile(r"(?:not\s+trigger|bypass|evade|defeat|beat)\s+"
                               r"(?:the\s+)?ai[- ]?detect", re.IGNORECASE)
        for path in [README, MASTER_PROMPT, CANONICAL_SKILL, SYSTEM_PROMPT]:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertIsNone(forbidden.search(read(path)),
                                  "file promises a detector outcome")


if __name__ == "__main__":
    unittest.main(verbosity=2)
