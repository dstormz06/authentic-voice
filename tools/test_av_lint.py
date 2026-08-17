#!/usr/bin/env python3
"""
test_av_lint.py : verification suite for av_lint.py.

Two jobs:

1. Unit-test every check in isolation. Each check gets a fixture that MUST
   trip it and a fixture that MUST NOT, so a check cannot silently rot into a
   no-op or a false-positive machine.
2. Regression-test the framework's own published examples. The generic "before"
   samples must fail; the authentic "after" samples must pass. If someone edits
   the master prompt's examples into something the linter rejects, this breaks.

Run:  python3 tools/test_av_lint.py          (or: python3 -m unittest discover tools)
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import av_lint  # noqa: E402
from av_lint import lint  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LINT_PY = os.path.join(HERE, "av_lint.py")


def checks_firing(report, severity=("error",)):
    return {f["check"] for f in report["findings"] if f["severity"] in severity}


# A clean baseline: passes every check in every profile. Fixtures below mutate
# this so each test isolates exactly one variable.
CLEAN = """i make small tools in rust. started in 2022.

most of them work. the pasta timer is the one people actually use, which
surprises me every single time someone mentions it.

i am bad at css. genuinely bad.

there is a plush shark on my desk. it has been there since the beginning and
i have never once considered moving it somewhere more sensible.

no framework here. just html.
"""


class TestSegmentation(unittest.TestCase):
    def test_bare_lines_count_as_units(self):
        # Personal-site copy is line-oriented; a fragment without terminal
        # punctuation is still a rhythm unit.
        self.assertEqual(len(av_lint.units("one two\nthree four five\nsix")), 3)

    def test_sentences_split_within_a_line(self):
        self.assertEqual(len(av_lint.units("First one. Second one! Third one?")), 3)

    def test_blank_lines_are_not_units(self):
        self.assertEqual(len(av_lint.units("alpha\n\n\nbeta")), 2)

    def test_code_fences_are_stripped(self):
        raw = "real prose here\n\n```\nwe leverage synergy to empower users\n```\n"
        self.assertNotIn("leverage", av_lint.strip_noise(raw))

    def test_inline_code_and_urls_are_stripped(self):
        raw = "install with `brew install empower` see https://example.com/leverage"
        cleaned = av_lint.strip_noise(raw)
        self.assertNotIn("empower", cleaned)
        self.assertNotIn("leverage", cleaned)


class TestBaseline(unittest.TestCase):
    def test_clean_copy_passes_every_profile(self):
        for profile in ("strict", "standard", "brand"):
            with self.subTest(profile=profile):
                report = lint(CLEAN, profile=profile)
                self.assertTrue(
                    report["passed"],
                    "baseline failed under %s: %s" % (profile, checks_firing(report)),
                )


class TestBannedLexicon(unittest.TestCase):
    def test_marketing_phrase_is_an_error(self):
        report = lint(CLEAN + "\nwe empower developers to build the future.\n")
        self.assertIn("banned-lexicon", checks_firing(report))

    def test_clean_copy_has_no_banned_hits(self):
        self.assertNotIn("banned-lexicon", checks_firing(lint(CLEAN)))

    def test_matching_is_case_insensitive(self):
        self.assertIn("banned-lexicon", checks_firing(lint(CLEAN + "\nSEAMLESS integration.\n")))

    def test_listed_inflections_fire(self):
        # Inflections are listed explicitly, not stemmed. Each listed form
        # must actually match.
        for form in ("empowerment", "unlocking", "leveraging", "seamlessly"):
            with self.subTest(form=form):
                report = lint(CLEAN + "\n%s aside, i mostly nap.\n" % form)
                self.assertIn("banned-lexicon", checks_firing(report))

    def test_unlisted_word_sharing_a_stem_is_ignored(self):
        # "power" and "lock" share stems with banned entries but are ordinary
        # words. Boundary anchoring must not let them through as hits.
        report = lint(CLEAN + "\ni lock the door and cut the power.\n")
        self.assertNotIn("banned-lexicon", checks_firing(report))

    def test_hyphenated_compound_is_not_a_hit(self):
        # "leverage-free" is a joke about not using the word, not the tell.
        # The trailing boundary deliberately excludes hyphen continuations.
        report = lint(CLEAN + "\nthis is a leverage-free zone.\n")
        self.assertNotIn("banned-lexicon", checks_firing(report))

    def test_listed_hyphenated_phrase_still_fires(self):
        report = lint(CLEAN + "\nour cutting-edge approach to napping.\n")
        self.assertIn("banned-lexicon", checks_firing(report))

    def test_quoted_mention_is_not_usage(self):
        # Rejecting the register by naming it is not writing in it.
        report = lint(CLEAN + '\nno "empower," no "unlock." just a timer.\n')
        self.assertNotIn("banned-lexicon", checks_firing(report))

    def test_curly_quoted_mention_is_not_usage(self):
        report = lint(CLEAN + "\nnobody says “seamless” out loud.\n")
        self.assertNotIn("banned-lexicon", checks_firing(report))

    def test_long_quoted_span_is_still_checked(self):
        # A whole quoted testimonial is usage, not a mention.
        long_quote = ('\n"our cutting-edge platform empowers teams to unlock '
                      'their full potential every single day" is what they wrote.\n')
        self.assertIn("banned-lexicon", checks_firing(lint(CLEAN + long_quote)))

    def test_curly_apostrophe_does_not_evade_matching(self):
        report = lint(CLEAN + "\nin today’s fast-paced world, i nap.\n")
        self.assertIn("banned-lexicon", checks_firing(report))


class TestFormulaic(unittest.TestCase):
    def test_whether_youre_construction(self):
        bad = CLEAN + "\nwhether you're a beginner or a seasoned pro, this helps.\n"
        self.assertIn("formulaic-structure", checks_firing(lint(bad)))

    def test_not_just_x_its_y(self):
        bad = CLEAN + "\nit's not just a timer, it's a lifestyle.\n"
        self.assertIn("formulaic-structure", checks_firing(lint(bad)))

    def test_in_a_world_where(self):
        bad = CLEAN + "\nin a world where everything is loud, this is quiet.\n"
        self.assertIn("formulaic-structure", checks_firing(lint(bad)))

    def test_clean_copy_is_not_formulaic(self):
        self.assertNotIn("formulaic-structure", checks_firing(lint(CLEAN)))


class TestDashes(unittest.TestCase):
    def test_strict_profile_forbids_any_em_dash(self):
        bad = CLEAN + "\ni build things — mostly badly.\n"
        self.assertIn("dash-overuse", checks_firing(lint(bad, profile="strict")))

    def test_standard_profile_allows_exactly_one(self):
        one = CLEAN + "\ni build things — mostly badly.\n"
        self.assertNotIn("dash-overuse", checks_firing(lint(one, profile="standard")))

    def test_standard_profile_rejects_two_in_short_copy(self):
        two = CLEAN + "\ni build things — mostly badly — and slowly.\n"
        self.assertIn("dash-overuse", checks_firing(lint(two, profile="standard")))

    def test_en_dash_counts_too(self):
        bad = CLEAN + "\nopen 9–17 – sometimes – never on sundays.\n"
        self.assertIn("dash-overuse", checks_firing(lint(bad, profile="strict")))


class TestFakePrecision(unittest.TestCase):
    def test_percentage_is_an_error_in_strict(self):
        bad = CLEAN + "\nit is 92% faster now.\n"
        self.assertIn("fake-precision", checks_firing(lint(bad, profile="strict")))

    def test_multiplier_is_flagged(self):
        bad = CLEAN + "\nruns 4.1x quicker.\n"
        self.assertIn("fake-precision", checks_firing(lint(bad, profile="strict")))

    def test_old_web_button_size_is_not_fake_precision(self):
        # 88x31 is the classic web button dimension, not a fabricated metric.
        ok = CLEAN + "\ni collect 88×31 buttons.\n"
        self.assertNotIn("fake-precision", checks_firing(lint(ok, profile="strict")))

    def test_year_is_not_fake_precision(self):
        self.assertNotIn("fake-precision", checks_firing(lint(CLEAN, profile="strict")))

    def test_standard_profile_downgrades_to_warning(self):
        bad = CLEAN + "\nit is 92% faster now.\n"
        report = lint(bad, profile="standard")
        self.assertIn("fake-precision", checks_firing(report, severity=("warn",)))
        self.assertNotIn("fake-precision", checks_firing(report))


class TestRhythm(unittest.TestCase):
    UNIFORM = "\n".join(["i wrote a tool that counts the seconds for you"] * 8)

    def test_uniform_rhythm_fails(self):
        report = lint(self.UNIFORM + "\nrust 2022 postgres\n", profile="strict")
        self.assertIn("rhythm-variation", checks_firing(report))

    def test_varied_rhythm_passes(self):
        self.assertNotIn("rhythm-variation", checks_firing(lint(CLEAN, profile="strict")))

    def test_short_copy_is_not_scored(self):
        report = lint("i make things. rust, 2022.", profile="strict")
        burst = [f for f in report["findings"] if f["check"] == "rhythm-variation"]
        self.assertEqual(burst[0]["severity"], "info")


class TestProfessionalProfile(unittest.TestCase):
    """Workplace writing. Jargon is the dominant failure mode; rhythm is a
    weaker signal here than on personal copy and must not block."""

    # Measured CVs that set the professional threshold. Kept as fixtures so a
    # future threshold change has to confront the evidence it was chosen from.
    LLM_BUSINESS = (
        "We have made considerable progress on the initiative this quarter. The team has "
        "been working closely with stakeholders to ensure alignment. We anticipate that the "
        "remaining work will be completed on schedule. Additional updates will be shared as "
        "they become available. Please let us know if you have any questions."
    )
    HUMAN_STATUS = (
        "The launch moves to March 3. Load testing found the eu-west cluster cannot take the "
        "traffic.\nAdding capacity takes six weeks.\nNothing needs a decision from you "
        "today.\nI will send the revised plan on Friday."
    )

    def test_jargon_cluster_is_an_error(self):
        copy = ("Going forward we will circle back on the low-hanging fruit in 2026.\n"
                "We should socialize the north star and drill down on stakeholder buy-in.\n")
        self.assertIn("workplace-jargon", checks_firing(lint(copy, profile="professional")))

    def test_single_jargon_term_in_long_copy_is_tolerated(self):
        copy = (self.HUMAN_STATUS + "\n" + " ".join(["The report covers the quarter."] * 40)
                + "\nOne quick win landed on Friday.\n")
        self.assertNotIn("workplace-jargon", checks_firing(lint(copy, profile="professional")))

    def test_terse_human_status_update_is_not_blocked(self):
        report = lint(self.HUMAN_STATUS, profile="professional")
        self.assertTrue(report["passed"], checks_firing(report))

    def test_uniform_llm_prose_is_still_reported(self):
        # Reported, not blocking: the signal is real but too weak to gate on.
        report = lint(self.LLM_BUSINESS, profile="professional")
        self.assertIn("rhythm-variation", checks_firing(report, severity=("warn",)))
        self.assertNotIn("rhythm-variation", checks_firing(report))

    def test_rhythm_still_blocks_on_personal_copy(self):
        uniform = "\n".join(["i wrote a tool that counts the seconds for you"] * 8)
        self.assertIn("rhythm-variation", checks_firing(lint(uniform + "\nrust 2022\n",
                                                       profile="strict")))

    def test_banned_lexicon_still_blocks_at_work(self):
        copy = self.HUMAN_STATUS + "\nThis will empower the team going forward.\n"
        self.assertIn("banned-lexicon", checks_firing(lint(copy, profile="professional")))

    def test_professional_has_the_tightest_jargon_budget(self):
        prof = av_lint.PROFILES["professional"]
        for name, other in av_lint.PROFILES.items():
            if name != "professional":
                with self.subTest(other=name):
                    self.assertLessEqual(prof.jargon_per_200w, other.jargon_per_200w)

    def test_jargon_quoted_mention_is_not_usage(self):
        copy = self.HUMAN_STATUS + '\nPlease stop writing "circle back" in updates.\n'
        self.assertNotIn("workplace-jargon", checks_firing(lint(copy, profile="professional")))


class TestAnchors(unittest.TestCase):
    def test_vague_copy_lacks_anchors(self):
        vague = ("i do things and care about doing them well.\n"
                 "sometimes it goes fine and sometimes it does not.\n"
                 "there is no way to say more than that.\n"
                 "the work continues, more or less, forever.\n"
                 "that is really all of it.\n")
        self.assertIn("concrete-anchors", checks_firing(lint(vague, profile="strict")))

    def test_specific_copy_has_anchors(self):
        self.assertNotIn("concrete-anchors", checks_firing(lint(CLEAN, profile="strict")))


class TestPlaceholders(unittest.TestCase):
    def test_placeholders_are_reported_as_warnings(self):
        copy = CLEAN + "\ni have worked at [EMPLOYER] since [YEAR].\n"
        report = lint(copy, profile="strict")
        self.assertIn("unresolved-placeholders", checks_firing(report, severity=("warn",)))

    def test_placeholder_counts_as_a_deferred_anchor(self):
        # A bracketed slot is a marked-but-unknown fact, not a missing one.
        vague = ("i do things and care about doing them well.\n"
                 "sometimes it goes fine and sometimes it does not.\n"
                 "i have been at [EMPLOYER] since [YEAR], more or less.\n"
                 "the work continues, forever.\n"
                 "that is really all of it.\n")
        self.assertNotIn("concrete-anchors", checks_firing(lint(vague, profile="strict")))

    def test_markdown_link_is_not_a_placeholder(self):
        report = lint(CLEAN + "\nthe [source code](x) is online.\n")
        self.assertNotIn("unresolved-placeholders", checks_firing(report, severity=("warn",)))

    def test_task_checkbox_is_not_a_placeholder(self):
        report = lint(CLEAN + "\nthings to do:\n[ ] sleep\n")
        self.assertNotIn("unresolved-placeholders", checks_firing(report, severity=("warn",)))

    def test_clean_copy_reports_no_placeholders(self):
        self.assertNotIn("unresolved-placeholders", checks_firing(lint(CLEAN), severity=("warn",)))


class TestQuirkStacking(unittest.TestCase):
    def test_stacked_conventions_fail(self):
        costume = ("code:work\n"
                   "blog:posts\n"
                   "$ whoami\n"
                   "$ cat about.txt\n"
                   "i am here \U0001F984 since 2022\n"
                   "rust... elixir... css...\n"
                   "SHOUTING HEADER\n"
                   "ANOTHER SHOUTING HEADER\n")
        self.assertIn("quirk-stacking", checks_firing(lint(costume, profile="strict")))

    def test_single_convention_passes(self):
        self.assertNotIn("quirk-stacking", checks_firing(lint(CLEAN, profile="strict")))


class TestDeclaredConvention(unittest.TestCase):
    def test_violating_declared_convention_fails(self):
        copy = "everything is lowercase here\nExcept This Line\nand this one is fine\n"
        self.assertIn("micro-convention", checks_firing(lint(copy, convention=r"^[^A-Z]*$")))

    def test_holding_convention_passes(self):
        copy = "everything is lowercase here\nand this one is fine\n"
        self.assertNotIn("micro-convention", checks_firing(lint(copy, convention=r"^[^A-Z]*$")))

    def test_bad_regex_reports_cleanly(self):
        report = lint(CLEAN, convention="([unclosed")
        self.assertIn("micro-convention", checks_firing(report))


class TestSoftChecks(unittest.TestCase):
    def test_uniform_openers_warn(self):
        copy = ("i make tools in rust since 2022.\n"
                "i am bad at css and always have been.\n"
                "i keep a plush shark on the desk.\n"
                "i do not know why.\n")
        self.assertIn("uniform-openers", checks_firing(lint(copy), severity=("warn",)))

    def test_tricolon_density_warns(self):
        copy = ("i write rust, elixir, and css badly since 2022.\n"
                "the tools are small, slow, and mostly fine.\n"
                "i read, sleep, and complain about the borrow checker.\n"
                "that is it.\n")
        self.assertIn("rule-of-three", checks_firing(lint(copy), severity=("warn",)))


class TestPublishedExamples(unittest.TestCase):
    """The framework's own before/after pairs must behave as documented."""

    GENERIC_HERO = (
        "Hi, I'm Sarah, a passionate web developer empowering teams to build "
        "delightful digital experiences. Driven by curiosity and a love of "
        "learning, I specialize in crafting scalable, user-centric applications "
        "that solve real-world problems. Let's build the future together."
    )

    GENERIC_README = (
        "This project empowers developers to streamline their workflow with a "
        "cutting-edge, robust solution. Contribute today to help shape the "
        "future of development!"
    )

    AUTHENTIC_HERO = (
        "sert is my name, sarah\n"
        "frontend developer, taken seriously since 2022\n"
        "favorite feature: the delete key\n"
        "this site has zero frameworks and one (1) opinion\n"
        "i broke the css again on tuesday and left it that way\n"
    )

    AUTHENTIC_README = (
        "toggl is a tiny timer for people who forget to stop timers.\n"
        "i built it because i kept burning my dinner while timing pasta.\n"
        "works on desktop. probably. tested until tuesday.\n"
        "install it with the one command in the makefile, or do not.\n"
        "it does not do rice.\n"
    )

    def test_generic_hero_fails(self):
        self.assertFalse(lint(self.GENERIC_HERO, profile="strict")["passed"])

    def test_generic_readme_fails(self):
        self.assertFalse(lint(self.GENERIC_README, profile="standard")["passed"])

    def test_authentic_hero_passes(self):
        report = lint(self.AUTHENTIC_HERO, profile="strict")
        self.assertTrue(report["passed"], checks_firing(report))

    def test_authentic_readme_passes(self):
        report = lint(self.AUTHENTIC_README, profile="standard")
        self.assertTrue(report["passed"], checks_firing(report))


class TestCli(unittest.TestCase):
    def _run(self, args, stdin=""):
        return subprocess.run(
            [sys.executable, LINT_PY] + args,
            input=stdin, capture_output=True, text=True,
        )

    def test_exit_zero_on_clean_stdin(self):
        proc = self._run(["--stdin", "--profile", "strict"], stdin=CLEAN)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_exit_one_on_dirty_stdin(self):
        proc = self._run(["--stdin"], stdin="we empower developers to unlock synergy.")
        self.assertEqual(proc.returncode, 1)

    def test_json_output_is_valid(self):
        import json
        proc = self._run(["--stdin", "--json"], stdin=CLEAN)
        payload = json.loads(proc.stdout)
        self.assertIn("passed", payload)
        self.assertEqual(payload["profile"], av_lint.DEFAULT_PROFILE)

    def test_default_profile_is_the_work_one(self):
        # Most drafts run through this tool are work drafts. The default should
        # not be a personal-site ruleset.
        self.assertEqual(av_lint.DEFAULT_PROFILE, "professional")

    def test_no_input_is_usage_error(self):
        self.assertEqual(self._run([]).returncode, 2)

    def test_missing_file_is_io_error(self):
        self.assertEqual(self._run(["/nonexistent/nope.md"]).returncode, 2)

    def test_strict_warnings_promotes_warnings(self):
        copy = ("i make tools in rust since 2022.\n"
                "i am bad at css and always have been.\n"
                "i keep a plush shark on the desk.\n"
                "i do not know why.\n")
        self.assertEqual(self._run(["--stdin"], stdin=copy).returncode, 0)
        self.assertEqual(self._run(["--stdin", "--strict-warnings"], stdin=copy).returncode, 1)

    def test_unknown_profile_rejected(self):
        self.assertEqual(self._run(["--stdin", "--profile", "nope"], stdin=CLEAN).returncode, 2)


class TestApi(unittest.TestCase):
    def test_unknown_profile_raises(self):
        with self.assertRaises(ValueError):
            lint(CLEAN, profile="does-not-exist")

    def test_report_shape_is_stable(self):
        report = lint(CLEAN)
        for key in ("version", "profile", "words", "units", "passed",
                    "error_count", "warning_count", "findings"):
            self.assertIn(key, report)

    def test_empty_input_does_not_crash(self):
        report = lint("")
        self.assertIsInstance(report["passed"], bool)


if __name__ == "__main__":
    unittest.main(verbosity=2)
