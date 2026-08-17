#!/usr/bin/env python3
"""
test_framework_sync.py : integrity tests for the Plain Writing framework.

test_av_lint.py proves the checker works. This suite proves the *framework* is
internally consistent and stays fit to circulate at work.

Every claim these tests enforce is a claim made in prose somewhere in the repo.
If a claim cannot be tested, it should not be made.

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

PROMPT = os.path.join(ROOT, "agent", "PLAIN_WRITING.md")
CANONICAL_SKILL = os.path.join(ROOT, "skills", "plain-writing", "SKILL.md")
SKILL_MIRRORS = [
    os.path.join(ROOT, ".claude", "skills", "plain-writing", "SKILL.md"),
    os.path.join(ROOT, ".amp", "skills", "plain-writing", "SKILL.md"),
    os.path.join(ROOT, ".opencode", "skills", "plain-writing", "SKILL.md"),
]
EVALS = os.path.join(ROOT, "evals", "evals.json")
README = os.path.join(ROOT, "README.md")

PROSE_FILES = [PROMPT, CANONICAL_SKILL, README]

EM_DASH = "—"
EN_DASH = "–"


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def parse_lexicon_block(text: str, header: str):
    """Pull one '# header' group out of the fenced lexicon block in section 9."""
    fence = re.search(r"```text\n(.*?)\n```", text, re.DOTALL)
    if not fence:
        raise AssertionError("no fenced lexicon block found in the prompt")
    groups, current = {}, None
    for line in fence.group(1).splitlines():
        line = line.strip()
        if line.startswith("#"):
            current = line.lstrip("#").strip()
            groups[current] = []
        elif line and current is not None:
            groups[current].append(line)
    for name, lines in groups.items():
        if name.startswith(header):
            return [t.strip() for t in " ".join(lines).split(",") if t.strip()]
    raise AssertionError("lexicon group %r not found; saw %s" % (header, list(groups)))


def quoted_blocks(text: str, marker: str):
    out, cap, cur = [], False, []
    for line in text.splitlines():
        if line.startswith(marker):
            cap, cur = True, []
            continue
        if cap:
            if line.startswith(">"):
                cur.append(line.lstrip("> ").rstrip())
            elif cur:
                out.append("\n".join(cur))
                cap, cur = False, []
    if cur:
        out.append("\n".join(cur))
    return out


class TestLexiconSync(unittest.TestCase):
    """Section 9 claims to be the same set as the checker. Prove it."""

    def setUp(self):
        self.text = read(PROMPT)

    def test_all_three_tiers_match_the_checker_exactly(self):
        for header, expected in (("tier 1", av_lint.BANNED),
                                 ("tier 2", av_lint.SUSPECT),
                                 ("tier 3", av_lint.JARGON)):
            with self.subTest(tier=header):
                self.assertEqual(sorted(parse_lexicon_block(self.text, header)),
                                 sorted(expected))

    def test_tiers_are_disjoint(self):
        # An entry in two tiers is counted twice and reported twice.
        b, s, j = set(av_lint.BANNED), set(av_lint.SUSPECT), set(av_lint.JARGON)
        self.assertEqual(b & s, set(), "BANNED and SUSPECT overlap")
        self.assertEqual(b & j, set(), "BANNED and JARGON overlap")
        self.assertEqual(s & j, set(), "SUSPECT and JARGON overlap")

    def test_no_duplicates_within_a_tier(self):
        for name, tier in (("BANNED", av_lint.BANNED), ("SUSPECT", av_lint.SUSPECT),
                           ("JARGON", av_lint.JARGON)):
            with self.subTest(tier=name):
                self.assertEqual(len(tier), len(set(tier)))

    def test_every_entry_matches_itself(self):
        # A malformed entry (stray punctuation, double space) would silently
        # never fire. Each pattern must at minimum match its own text.
        for label, pairs in (("BANNED", av_lint.BANNED_PATTERNS),
                             ("SUSPECT", av_lint.SUSPECT_PATTERNS),
                             ("JARGON", av_lint.JARGON_PATTERNS)):
            for phrase, pattern in pairs:
                with self.subTest(tier=label, phrase=phrase):
                    self.assertTrue(pattern.search(phrase), "never matches: %r" % phrase)


class TestWorkSafety(unittest.TestCase):
    """The reason this repo was stripped down. These are regression tests
    against the casual-social register and detection framing coming back."""

    def setUp(self):
        self.text = read(PROMPT)

    def test_no_casual_social_register_anywhere(self):
        # Word-boundary matching, not substring: "ngl" lives inside "single".
        tokens = ("discord", "ngl", "tbh", "idk", "lol", "fr", "dead ass", "no cap",
                  "imperfect grammar", "misspelling", "burstiness")
        for path in PROSE_FILES:
            for token in tokens:
                with self.subTest(path=os.path.relpath(path, ROOT), token=token):
                    self.assertIsNone(
                        re.search(r"\b%s\b" % re.escape(token), read(path), re.IGNORECASE),
                        "casual-social or detection register leaked in: %r" % token,
                    )

    def test_no_slang_or_profanity_dial(self):
        table = re.search(r"## 5\. REGISTER DIALS(.*?)^## 6\.", self.text,
                          re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(table, "register dial section not found")
        rows = [ln for ln in table.group(1).splitlines() if ln.startswith("| **")]
        self.assertTrue(rows, "no dial rows found")
        for row in rows:
            for dial in ("profanity", "slang", "self-deprecation", "snark"):
                with self.subTest(row=row[:36], dial=dial):
                    self.assertNotIn(dial, row.lower())

    def test_no_detection_or_evasion_framing(self):
        forbidden = re.compile(
            r"(?:ai[- ]?detect|detector|detectability|humaniz|stylometr)", re.IGNORECASE)
        for path in PROSE_FILES:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertIsNone(forbidden.search(read(path)),
                                  "detection framing present")

    def test_checker_has_no_casual_social_profile(self):
        self.assertNotIn("discord", av_lint.PROFILES)
        self.assertFalse(hasattr(av_lint, "DISCOURSE"))
        self.assertFalse(hasattr(av_lint, "check_discourse"))

    def test_forbids_inventing_facts_and_metrics(self):
        self.assertRegex(self.text, r"(?i)never\s+invent\s+a\s+metric")
        self.assertRegex(self.text, r"(?i)never\s+present\s+an\s+invented\s+specific")

    def test_refuses_authorship_deception(self):
        self.assertRegex(self.text, r"(?i)certif(?:y|ies)\s+as\s+their\s+own|"
                                    r"must\s+certify\s+they\s+wrote")


class TestPracticeWhatYouPreach(unittest.TestCase):
    def test_no_em_or_en_dashes(self):
        for path in PROSE_FILES:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                text = read(path)
                self.assertEqual(text.count(EM_DASH), 0, "em dash present")
                self.assertEqual(text.count(EN_DASH), 0, "en dash present")

    def test_no_unexpanded_placeholders(self):
        patterns = [r"\$\(date", r"<model-name>", r"<path/to/skill>", r"update complete"]
        for path in PROSE_FILES:
            for pat in patterns:
                with self.subTest(path=os.path.relpath(path, ROOT), pattern=pat):
                    self.assertIsNone(re.search(pat, read(path)))

    def test_prompt_is_self_contained(self):
        # It has to work pasted into a chat window with nothing else.
        for token in ("tools/", ".py", "av_lint", "research-papers"):
            with self.subTest(token=token):
                self.assertNotIn(token, read(PROMPT).lower())


class TestSkillMirrors(unittest.TestCase):
    def test_all_mirrors_exist(self):
        for path in SKILL_MIRRORS:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertTrue(os.path.isfile(path), "missing mirror")

    def test_all_mirrors_are_byte_identical(self):
        canonical = read(CANONICAL_SKILL)
        for path in SKILL_MIRRORS:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertEqual(read(path), canonical, "mirror has drifted")

    def test_frontmatter_is_wellformed(self):
        text = read(CANONICAL_SKILL)
        self.assertTrue(text.startswith("---\n"), "must open with YAML frontmatter")
        block = text[4:text.index("\n---\n", 4)]
        self.assertRegex(block, r"(?m)^name:\s*plain-writing\s*$")
        self.assertRegex(block, r"(?m)^description:\s*\S")

    def test_files_end_with_newline(self):
        for path in [CANONICAL_SKILL] + SKILL_MIRRORS + [PROMPT]:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertTrue(read(path).endswith("\n"), "no trailing newline")

    def test_no_stale_authentic_voice_skill_remains(self):
        for base in (ROOT, os.path.join(ROOT, ".claude"), os.path.join(ROOT, ".amp"),
                     os.path.join(ROOT, ".opencode")):
            stale = os.path.join(base, "skills", "authentic-voice")
            with self.subTest(path=os.path.relpath(stale, ROOT)):
                self.assertFalse(os.path.exists(stale), "old skill still present")


class TestWorkedExamples(unittest.TestCase):
    def setUp(self):
        self.text = read(PROMPT)

    def test_four_pairs_are_present(self):
        self.assertEqual(len(quoted_blocks(self.text, "*Before:*")), 4)
        self.assertEqual(len(quoted_blocks(self.text, "*After:*")), 4)

    def test_after_examples_pass(self):
        for i, block in enumerate(quoted_blocks(self.text, "*After:*"), start=1):
            with self.subTest(example=i):
                report = lint(block, profile="professional")
                failing = {f["check"] for f in report["findings"] if f["severity"] == "error"}
                self.assertTrue(report["passed"], "after-example %d fails: %s" % (i, failing))

    def test_before_examples_fail(self):
        for i, block in enumerate(quoted_blocks(self.text, "*Before:*"), start=1):
            with self.subTest(example=i):
                self.assertFalse(lint(block, profile="professional")["passed"],
                                 "before-example %d unexpectedly passes" % i)


class TestEvals(unittest.TestCase):
    def setUp(self):
        with open(EVALS, "r", encoding="utf-8") as fh:
            self.data = json.load(fh)

    def test_schema(self):
        self.assertEqual(self.data["skill_name"], "plain-writing")
        self.assertGreaterEqual(len(self.data["evals"]), 5)

    def test_every_eval_has_assertions(self):
        for ev in self.data["evals"]:
            with self.subTest(eval_id=ev.get("id")):
                self.assertTrue(ev.get("assertions"), "eval has no assertions")

    def test_every_eval_declares_a_known_profile(self):
        for ev in self.data["evals"]:
            with self.subTest(eval_id=ev.get("id")):
                self.assertIn(ev.get("lint_profile"), av_lint.PROFILES)

    def test_ids_and_names_are_unique(self):
        ids = [ev["id"] for ev in self.data["evals"]]
        names = [ev["name"] for ev in self.data["evals"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(names), len(set(names)))

    def test_fabrication_is_covered(self):
        # The failure mode that costs most at work must have an eval.
        blob = json.dumps(self.data).lower()
        self.assertIn("invent", blob)


class TestNumericClaims(unittest.TestCase):
    """Counts stated in prose must match the code."""

    def test_lexicon_size_claims(self):
        readme = read(README)
        for pattern, actual in (
            (r"\|\s*`banned-lexicon`\s*\|\s*(\d+)\s+", len(av_lint.BANNED)),
            (r"(\d+)\s+terms\)", len(av_lint.JARGON)),
        ):
            found = re.search(pattern, readme)
            with self.subTest(pattern=pattern):
                self.assertIsNotNone(found, "README states no count for %r" % pattern)
                self.assertEqual(int(found.group(1)), actual)

    def test_declared_test_counts_match_reality(self):
        readme = read(README)
        for filename in ("test_av_lint.py", "test_framework_sync.py"):
            claimed = re.search(re.escape(filename) + r"\s+#?\s*(\d+) tests", readme)
            with self.subTest(suite=filename):
                self.assertIsNotNone(claimed, "README states no test count for %s" % filename)
                loader = unittest.defaultTestLoader.discover(
                    os.path.join(ROOT, "tools"), pattern=filename,
                    top_level_dir=os.path.join(ROOT, "tools"))
                self.assertEqual(int(claimed.group(1)), loader.countTestCases(),
                                 "README test count for %s is stale" % filename)

    def test_every_profile_is_documented(self):
        readme = read(README)
        for name in av_lint.PROFILES:
            with self.subTest(profile=name):
                self.assertIn("`%s`" % name, readme, "profile %r undocumented" % name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
