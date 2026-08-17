#!/usr/bin/env python3
"""
av_lint.py : deterministic checker for Authentic Voice copy.

Machine-checkable subset of the Authentic Voice framework. It cannot judge
whether copy is *true* or whether it sounds like a specific person. It CAN
catch the mechanical AI tells that humans reliably do not produce at scale:
marketing lexicon, dash overuse, uniform sentence rhythm, fake precision,
rule-of-three scaffolding, quirk stacking, and missing concrete anchors.

Zero dependencies. Python 3.8+. Single file on purpose: copy it anywhere.

Usage:
    python3 av_lint.py FILE [FILE ...] [--profile strict|standard|discord|brand]
    python3 av_lint.py --stdin --profile strict < copy.md
    python3 av_lint.py copy.md --json
    python3 av_lint.py copy.md --convention '^[a-z]'   # assert a micro-convention

Exit codes:
    0  no errors (warnings may be present)
    1  at least one error, or a warning when --strict-warnings is set
    2  usage / IO problem
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import unicodedata
from dataclasses import dataclass, asdict, field
from typing import Dict, Iterable, List, Optional, Sequence

__version__ = "2.0.0"

# --------------------------------------------------------------------------
# Lexicons. Single source of truth, mirrored in the master prompt appendix.
# --------------------------------------------------------------------------

# Tier A: hard marketing / AI-register clichés. Any hit is an error.
# Entries are matched case-insensitively on word boundaries. Multi-word
# entries tolerate any run of whitespace between tokens.
BANNED = [
    "empower", "empowers", "empowering", "empowerment",
    "unlock", "unlocks", "unlocking",
    "seamless", "seamlessly",
    "cutting-edge", "cutting edge",
    "state-of-the-art", "best-in-class", "world-class", "industry-leading",
    "leverage", "leverages", "leveraging",
    "harness", "harnesses", "harnessing",
    "delve", "delves", "delving",
    "passionate about", "driven by", "committed to", "dedicated to",
    "on a mission to", "in today's fast-paced world", "in today's world",
    "game-changer", "game-changing", "revolutionize", "revolutionizing",
    "transformative", "transform your", "elevate your", "supercharge",
    "streamline", "streamlines", "streamlining",
    "unparalleled", "unrivaled", "bespoke solution",
    "tapestry", "testament to", "at the forefront",
    "navigate the complexities", "navigating the complexities",
    "paradigm shift", "synergy", "holistic approach",
    "embark on", "embarking on",
    "the future of", "build the future", "shape the future",
    "take it to the next level", "next-level",
    "solutions that scale", "user-centric", "real-world problems",
    "let's build", "we're on a journey", "it's been a journey",
    "i'm so grateful", "i am so grateful", "humbled to", "thrilled to announce",
    "excited to share", "as a passionate", "deep dive into",
    "look no further", "in conclusion", "it's worth noting",
]

# Tier B: AI-favored adjectives/adverbs. Individually innocent, collectively a
# tell. Scored by density rather than banned outright.
SUSPECT = [
    "intricate", "invaluable", "exceptional", "pivotal", "crucial", "vital",
    "comprehensive", "innovative", "dynamic", "versatile", "profound",
    "remarkable", "noteworthy", "robust", "myriad", "plethora", "nuanced",
    "meticulous", "meticulously", "seamless",
    "primarily", "thoroughly", "subsequently", "particularly", "notably",
    "significantly", "undoubtedly", "certainly", "essentially", "ultimately",
    "arguably", "furthermore", "moreover", "additionally", "consequently",
]

# Casual discourse markers. Presence is expected in the discord profile only.
DISCOURSE = [
    "idk", "ngl", "lol", "lmao", "fr", "tbh", "imo", "kinda", "sorta",
    "anyway", "anyways", "so yeah", "honestly", "basically", "i guess",
    "or whatever", "dunno", "yeah", "nah", "eh",
]

# Formulaic scaffolding. Regex, matched case-insensitively.
FORMULAIC = [
    (r"\bwhether\s+you(?:'re|\s+are)\b.{0,80}\bor\b", "whether-you're-X-or-Y construction"),
    (r"\b(?:it'?s|this\s+is)\s+not\s+just\s+(?:\w+[\s,]+){1,5}it'?s\b",
     "'it's not just X, it's Y' construction"),
    (r"\bfrom\s+\w+\s+to\s+\w+,\s+", "'from X to Y,' opener"),
    (r"\bmore\s+than\s+just\s+a\b", "'more than just a' construction"),
    (r"\bin\s+a\s+world\s+where\b", "'in a world where' opener"),
    (r"\bwe\s+believe\s+that\b", "'we believe that' mission-statement opener"),
]

# Fake precision: unsourced percentages and multipliers.
RE_PERCENT = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%")
RE_MULTIPLIER = re.compile(r"\b\d+(?:\.\d+)?\s?[x×](?![0-9A-Za-z])")

# Concrete anchors: years, counts, proper nouns, versions, times, currency.
RE_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
RE_COUNT = re.compile(r"\b\d{1,4}\b")
RE_TIME = re.compile(r"\b\d{1,2}\s?(?:am|pm)\b", re.IGNORECASE)
# Weekdays and months are concrete anchors even when the copy is all-lowercase,
# which is exactly the register this framework encourages. Matching them
# case-sensitively (via the proper-noun rule alone) would miss every one.
RE_CALENDAR = re.compile(
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"january|february|march|april|may|june|july|august|september|"
    r"october|november|december|yesterday|tonight|midnight|noon)\b",
    re.IGNORECASE,
)
RE_PROPER = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b", re.MULTILINE)
RE_LOWER_TOOL = re.compile(
    r"\b(?:rust|elixir|python|golang|discord|github|linux|css|sqlite|"
    r"postgres|vim|emacs|docker|kubernetes|javascript|typescript|ruby|"
    r"haskell|zig|nix|arch|debian|ubuntu|firefox|neovim)\b",
    re.IGNORECASE,
)

# Short double-quoted spans are treated as mentions, not usage.
RE_QUOTED_MENTION = re.compile(r"[\"“][^\"”\n]{1,40}[\"”]")

# Visible placeholders: [NAME], [YEAR], [N], [CITY]. Upper-case content only, so
# markdown links and task checkboxes are not mistaken for them.
RE_PLACEHOLDER = re.compile(r"\[[A-Z][A-Z0-9 _/-]{0,30}\]")

EM_DASH = "—"
EN_DASH = "–"

# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Profile:
    name: str
    max_dash_per_400w: float
    # Minimum coefficient of variation (stdev / mean) of sentence lengths.
    # CV is scale-invariant, so a page of five-word fragments and a page of
    # thirty-word sentences are held to the same standard of *variety*. Raw
    # stdev is not: it punishes short-form copy for being short.
    # Observed ranges: uniform LLM prose 0.05 to 0.20; varied human copy
    # 0.35 to 0.70.
    min_burstiness_cv: float
    min_anchors: int
    min_discourse: int
    suspect_per_200w: float
    fake_precision_severity: str
    max_quirks: int


PROFILES: Dict[str, Profile] = {
    # Personal site, bio, tagline, about page. Tightest register.
    "strict": Profile("strict", 0.0, 0.32, 2, 0, 2.0, "error", 2),
    # README, project blurb, changelog, longer prose.
    "standard": Profile("standard", 1.0, 0.28, 1, 0, 3.0, "warn", 2),
    # Discord / casual social. Discourse markers expected, rhythm loosest.
    "discord": Profile("discord", 0.0, 0.35, 2, 1, 2.0, "warn", 2),
    # Company/product copy. Lexicon and rhythm still apply; no persona rules.
    "brand": Profile("brand", 1.0, 0.25, 1, 0, 3.0, "warn", 3),
}

DEFAULT_PROFILE = "standard"

# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------


@dataclass
class Finding:
    check: str
    severity: str  # "error" | "warn" | "info"
    message: str
    evidence: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Text segmentation
# --------------------------------------------------------------------------

RE_SENT_SPLIT = re.compile(r"(?<=[.!?])[\"')\]]*\s+")
RE_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’-]*")
RE_CODE_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
RE_INLINE_CODE = re.compile(r"`[^`\n]*`")
RE_URL = re.compile(r"https?://\S+")
RE_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
RE_MD_MARKER = re.compile(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+|>\s?)", re.MULTILINE)


def strip_noise(text: str) -> str:
    """Remove code blocks, URLs and markdown scaffolding before linting prose.

    Copy is judged on its prose. A URL containing 'leverage' or a fenced code
    sample is not the author's register.
    """
    # Normalise typographic apostrophes first. Copy pasted out of a word
    # processor uses U+2019, and every phrase pattern spelled with a straight
    # quote would silently miss it.
    out = text.replace("’", "'").replace("ʼ", "'")
    out = RE_CODE_FENCE.sub("\n", out)
    out = RE_INLINE_CODE.sub(" ", out)
    out = RE_URL.sub(" ", out)
    out = RE_MD_HEADING.sub("", out)
    out = RE_MD_MARKER.sub("", out)
    return out


def units(text: str) -> List[str]:
    """Split copy into rhythm units.

    Personal-site copy is line-oriented: a bare fragment on its own line is a
    unit even without terminal punctuation. So we split on hard line breaks
    first, then on sentence terminators inside each line.
    """
    result: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for piece in RE_SENT_SPLIT.split(line):
            piece = piece.strip()
            if piece and RE_WORD.search(piece):
                result.append(piece)
    return result


def words(text: str) -> List[str]:
    return RE_WORD.findall(text)


def _phrase_pattern(phrase: str) -> re.Pattern:
    """Build a whitespace-tolerant, boundary-anchored pattern for a phrase."""
    tokens = [re.escape(tok) for tok in phrase.split()]
    body = r"\s+".join(tokens)
    lead = r"(?<![\w-])" if re.match(r"[\w]", phrase) else r""
    trail = r"(?![\w-])" if re.search(r"[\w]$", phrase) else r""
    return re.compile(lead + body + trail, re.IGNORECASE)


BANNED_PATTERNS = [(p, _phrase_pattern(p)) for p in BANNED]
SUSPECT_PATTERNS = [(p, _phrase_pattern(p)) for p in SUSPECT]
DISCOURSE_PATTERNS = [(p, _phrase_pattern(p)) for p in DISCOURSE]
FORMULAIC_PATTERNS = [(re.compile(rx, re.IGNORECASE | re.DOTALL), label) for rx, label in FORMULAIC]


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------


def check_dashes(prose: str, wc: int, prof: Profile) -> List[Finding]:
    em = prose.count(EM_DASH)
    en = prose.count(EN_DASH)
    total = em + en
    if total == 0:
        return []
    allowed = prof.max_dash_per_400w * max(wc, 1) / 400.0
    # Always allow the integer floor of the budget, so a 1-per-400w profile
    # permits exactly one dash in a short piece rather than a fraction of one.
    allowed_int = max(int(allowed), 1 if prof.max_dash_per_400w > 0 else 0)
    if total <= allowed_int:
        return []
    return [
        Finding(
            "dash-overuse",
            "error",
            "%d em/en dash(es) in %d words; profile '%s' allows %d."
            % (total, wc, prof.name, allowed_int),
            evidence=["em-dash x%d" % em, "en-dash x%d" % en],
        )
    ]


def mask_quoted_mentions(prose: str) -> str:
    """Blank out short quoted spans before lexicon checks.

    Use versus mention: copy that says  no "empower", no "unlock"  is rejecting
    the register, not writing in it. Only short spans are masked, so a long
    quoted testimonial full of marketing language is still caught.
    """
    return RE_QUOTED_MENTION.sub(" ", prose)


def check_banned(prose: str) -> List[Finding]:
    prose = mask_quoted_mentions(prose)
    hits: List[str] = []
    for phrase, pat in BANNED_PATTERNS:
        found = pat.findall(prose)
        if found:
            hits.append("%s (x%d)" % (phrase, len(found)))
    if not hits:
        return []
    return [
        Finding(
            "banned-lexicon",
            "error",
            "%d marketing/AI-register phrase(s) present. Rewrite each." % len(hits),
            evidence=sorted(hits),
        )
    ]


def check_suspect(prose: str, wc: int, prof: Profile) -> List[Finding]:
    prose = mask_quoted_mentions(prose)
    hits: List[str] = []
    count = 0
    for phrase, pat in SUSPECT_PATTERNS:
        n = len(pat.findall(prose))
        if n:
            count += n
            hits.append("%s (x%d)" % (phrase, n))
    if not hits:
        return []
    density = count * 200.0 / max(wc, 1)
    if density <= prof.suspect_per_200w:
        return [
            Finding(
                "suspect-lexicon",
                "info",
                "%d AI-favored modifier(s), density %.1f per 200 words (limit %.1f)."
                % (count, density, prof.suspect_per_200w),
                evidence=sorted(hits),
            )
        ]
    return [
        Finding(
            "suspect-lexicon",
            "error",
            "AI-favored modifier density %.1f per 200 words exceeds limit %.1f."
            % (density, prof.suspect_per_200w),
            evidence=sorted(hits),
        )
    ]


def check_formulaic(prose: str) -> List[Finding]:
    out: List[Finding] = []
    for pat, label in FORMULAIC_PATTERNS:
        m = pat.search(prose)
        if m:
            out.append(
                Finding(
                    "formulaic-structure",
                    "error",
                    "Formulaic scaffolding: %s." % label,
                    evidence=[" ".join(m.group(0).split())[:90]],
                )
            )
    return out


def check_fake_precision(prose: str, prof: Profile) -> List[Finding]:
    hits = RE_PERCENT.findall(prose) + RE_MULTIPLIER.findall(prose)
    if not hits:
        return []
    return [
        Finding(
            "fake-precision",
            prof.fake_precision_severity,
            "%d unsourced numeric claim(s). Cite the source or cut it." % len(hits),
            evidence=[h.strip() for h in hits][:10],
        )
    ]


def check_burstiness(unit_list: Sequence[str], prof: Profile) -> List[Finding]:
    lengths = [len(words(u)) for u in unit_list]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 5:
        return [
            Finding(
                "burstiness",
                "info",
                "Only %d rhythm unit(s); variance not scored (needs 5)." % len(lengths),
            )
        ]
    mean = statistics.fmean(lengths)
    cv = statistics.pstdev(lengths) / mean if mean else 0.0
    if cv >= prof.min_burstiness_cv:
        return [
            Finding(
                "burstiness",
                "info",
                "Rhythm CV %.2f over %d units (min %.2f)."
                % (cv, len(lengths), prof.min_burstiness_cv),
            )
        ]
    return [
        Finding(
            "burstiness",
            "error",
            "Uniform rhythm: sentence-length CV %.2f over %d units, below %.2f. "
            "Mix in a fragment and a long one." % (cv, len(lengths), prof.min_burstiness_cv),
            evidence=["lengths=%s" % lengths[:20]],
        )
    ]


def check_anchors(prose: str, prof: Profile) -> List[Finding]:
    found: List[str] = []
    found += ["year:%s" % y for y in RE_YEAR.findall(prose)]
    found += ["time:%s" % t for t in RE_TIME.findall(prose)]
    found += ["date:%s" % d.lower() for d in RE_CALENDAR.findall(prose)]
    found += ["tool:%s" % t.lower() for t in RE_LOWER_TOOL.findall(prose)]
    found += ["name:%s" % p for p in RE_PROPER.findall(prose)]
    plain_counts = [c for c in RE_COUNT.findall(prose) if not RE_YEAR.fullmatch(c)]
    found += ["count:%s" % c for c in plain_counts]
    # A visible placeholder is an anchor the author has deliberately deferred:
    # the slot is marked, the fact is simply not known yet. It counts here so a
    # correctly-bracketed draft is not told to "add a real date", and it is
    # reported separately by check_placeholders so it cannot ship silently.
    found += ["pending:%s" % p for p in RE_PLACEHOLDER.findall(prose)]
    unique = sorted(set(found))
    if len(unique) >= prof.min_anchors:
        return [
            Finding(
                "concrete-anchors",
                "info",
                "%d distinct concrete anchor(s) (min %d)." % (len(unique), prof.min_anchors),
                evidence=unique[:12],
            )
        ]
    return [
        Finding(
            "concrete-anchors",
            "error",
            "Only %d concrete anchor(s); profile '%s' needs %d. Add a real date, "
            "count, tool or name." % (len(unique), prof.name, prof.min_anchors),
            evidence=unique,
        )
    ]


def check_placeholders(prose: str) -> List[Finding]:
    """Brackets must never ship silently. The output contract requires them
    reported back, so the checker surfaces them rather than staying quiet."""
    hits = RE_PLACEHOLDER.findall(prose)
    if not hits:
        return []
    unique = sorted(set(hits))
    return [
        Finding(
            "unresolved-placeholders",
            "warn",
            "%d unresolved placeholder(s). Fill them or report every one to the author."
            % len(unique),
            evidence=unique[:12],
        )
    ]


def check_discourse(prose: str, prof: Profile) -> List[Finding]:
    if prof.min_discourse <= 0:
        return []
    hits = [p for p, pat in DISCOURSE_PATTERNS if pat.search(prose)]
    if len(hits) >= prof.min_discourse:
        return [
            Finding("discourse-markers", "info", "%d casual marker(s) present." % len(hits),
                    evidence=sorted(hits)[:10])
        ]
    return [
        Finding(
            "discourse-markers",
            "error",
            "Profile '%s' expects at least %d casual discourse marker(s); found %d."
            % (prof.name, prof.min_discourse, len(hits)),
        )
    ]


def check_uniform_openers(unit_list: Sequence[str]) -> List[Finding]:
    if len(unit_list) < 4:
        return []
    firsts: Dict[str, int] = {}
    for u in unit_list:
        w = words(u)
        if not w:
            continue
        key = w[0].lower()
        firsts[key] = firsts.get(key, 0) + 1
    if not firsts:
        return []
    top, n = max(firsts.items(), key=lambda kv: kv[1])
    ratio = n / float(len(unit_list))
    if ratio >= 0.6 and n >= 3:
        return [
            Finding(
                "uniform-openers",
                "warn",
                "%d of %d units open with '%s' (%.0f%%). Vary the openers."
                % (n, len(unit_list), top, ratio * 100),
            )
        ]
    return []


def check_tricolon(prose: str) -> List[Finding]:
    pat = re.compile(r"\b[\w'-]+,\s+[\w'-]+,?\s+and\s+[\w'-]+\b", re.IGNORECASE)
    hits = pat.findall(prose)
    if len(hits) >= 3:
        return [
            Finding(
                "rule-of-three",
                "warn",
                "%d 'A, B and C' triads. Break at least one into a different shape."
                % len(hits),
            )
        ]
    return []


def _has_emoji(text: str) -> bool:
    for ch in text:
        if ord(ch) < 0x2190:
            continue
        cat = unicodedata.category(ch)
        if cat in ("So", "Sk") or 0x1F000 <= ord(ch) <= 0x1FAFF:
            return True
    return False


def check_quirk_stacking(raw: str, prof: Profile) -> List[Finding]:
    """One coherent habit reads as a person. Several read as a costume."""
    present: List[str] = []
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return []

    alpha_lines = [ln for ln in lines if re.search(r"[A-Za-z]", ln)]
    if alpha_lines:
        lower_start = sum(1 for ln in alpha_lines if re.match(r"^[^A-Za-z]*[a-z]", ln))
        if lower_start / float(len(alpha_lines)) >= 0.8:
            present.append("all-lowercase")

    if sum(1 for ln in lines if re.match(r"^\s*[\w.]+:\s*\S", ln)) >= 2:
        present.append("label:value")
    if sum(1 for ln in lines if re.match(r"^\s*[$>]\s+\S", ln)) >= 2:
        present.append("terminal-prompt")
    if _has_emoji(raw):
        present.append("emoji")
    if sum(1 for ln in lines if re.match(r"^[^a-z]{6,}$", ln.strip())) >= 2:
        present.append("ALL-CAPS-headers")
    if raw.count("...") + raw.count("…") >= 3:
        present.append("ellipses")
    if len(re.findall(r"\([^)]{1,40}\)", raw)) >= 4:
        present.append("parenthetical-asides")

    if len(present) > prof.max_quirks:
        return [
            Finding(
                "quirk-stacking",
                "error",
                "%d competing stylistic conventions; keep at most %d."
                % (len(present), prof.max_quirks),
                evidence=present,
            )
        ]
    return [
        Finding(
            "quirk-stacking",
            "info",
            "%d stylistic convention(s) detected (limit %d)." % (len(present), prof.max_quirks),
            evidence=present,
        )
    ]


def check_convention(raw: str, pattern: Optional[str]) -> List[Finding]:
    """Assert a declared micro-convention holds on every content line."""
    if not pattern:
        return []
    try:
        pat = re.compile(pattern)
    except re.error as exc:
        return [Finding("micro-convention", "error", "Bad --convention regex: %s" % exc)]
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    lines = [ln for ln in lines if RE_WORD.search(ln)]
    if not lines:
        return []
    offenders = [ln for ln in lines if not pat.search(ln)]
    if offenders:
        return [
            Finding(
                "micro-convention",
                "error",
                "%d of %d line(s) break the declared convention %r."
                % (len(offenders), len(lines), pattern),
                evidence=[ln[:80] for ln in offenders[:8]],
            )
        ]
    return [
        Finding(
            "micro-convention",
            "info",
            "Convention %r holds on all %d line(s)." % (pattern, len(lines)),
        )
    ]


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def lint(raw: str, profile: str = DEFAULT_PROFILE, convention: Optional[str] = None) -> Dict:
    if profile not in PROFILES:
        raise ValueError("unknown profile %r (choose from %s)" % (profile, ", ".join(sorted(PROFILES))))
    prof = PROFILES[profile]
    prose = strip_noise(raw)
    unit_list = units(prose)
    wc = len(words(prose))

    findings: List[Finding] = []
    findings += check_banned(prose)
    findings += check_formulaic(prose)
    findings += check_dashes(prose, wc, prof)
    findings += check_fake_precision(prose, prof)
    findings += check_suspect(prose, wc, prof)
    findings += check_burstiness(unit_list, prof)
    findings += check_anchors(prose, prof)
    findings += check_placeholders(prose)
    findings += check_discourse(prose, prof)
    findings += check_uniform_openers(unit_list)
    findings += check_tricolon(prose)
    findings += check_quirk_stacking(raw, prof)
    findings += check_convention(raw, convention)

    errors = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]
    return {
        "version": __version__,
        "profile": prof.name,
        "words": wc,
        "units": len(unit_list),
        "passed": not errors,
        "error_count": len(errors),
        "warning_count": len(warns),
        "findings": [asdict(f) for f in findings],
    }


SEV_ORDER = {"error": 0, "warn": 1, "info": 2}
SEV_LABEL = {"error": "FAIL", "warn": "WARN", "info": "info"}


def render(report: Dict, label: str, quiet: bool = False) -> str:
    lines = []
    status = "PASS" if report["passed"] else "FAIL"
    lines.append(
        "%s  %s  [profile=%s words=%d units=%d errors=%d warnings=%d]"
        % (status, label, report["profile"], report["words"], report["units"],
           report["error_count"], report["warning_count"])
    )
    findings = sorted(report["findings"], key=lambda f: SEV_ORDER.get(f["severity"], 3))
    for f in findings:
        if quiet and f["severity"] == "info":
            continue
        lines.append("  %-5s %-20s %s" % (SEV_LABEL.get(f["severity"], "?"), f["check"], f["message"]))
        for ev in f.get("evidence", [])[:8]:
            lines.append("        - %s" % ev)
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="av_lint.py",
        description="Deterministic Authentic Voice checker.",
    )
    ap.add_argument("files", nargs="*", help="files to lint")
    ap.add_argument("--stdin", action="store_true", help="read copy from stdin")
    ap.add_argument("--profile", default=DEFAULT_PROFILE, choices=sorted(PROFILES),
                    help="ruleset to apply (default: %s)" % DEFAULT_PROFILE)
    ap.add_argument("--convention", default=None,
                    help="regex every content line must match (declared micro-convention)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--quiet", action="store_true", help="hide info-level findings")
    ap.add_argument("--strict-warnings", action="store_true", help="treat warnings as failures")
    ap.add_argument("--version", action="version", version="av_lint %s" % __version__)
    args = ap.parse_args(argv)

    sources: List[tuple] = []
    if args.stdin:
        sources.append(("<stdin>", sys.stdin.read()))
    for path in args.files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                sources.append((path, fh.read()))
        except OSError as exc:
            print("av_lint: cannot read %s: %s" % (path, exc), file=sys.stderr)
            return 2
    if not sources:
        ap.print_usage(sys.stderr)
        print("av_lint: no input; pass files or --stdin", file=sys.stderr)
        return 2

    reports = []
    failed = False
    for label, raw in sources:
        report = lint(raw, profile=args.profile, convention=args.convention)
        report["source"] = label
        reports.append(report)
        if not report["passed"]:
            failed = True
        if args.strict_warnings and report["warning_count"]:
            failed = True

    if args.json:
        print(json.dumps(reports if len(reports) > 1 else reports[0], indent=2))
    else:
        print("\n\n".join(render(r, r["source"], quiet=args.quiet) for r in reports))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
