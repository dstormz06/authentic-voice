---
name: plain-writing
description: Write clearly and specifically instead of in corporate filler. Use for status updates, proposals, one-pagers, release notes, incident writeups, performance and self reviews, team and speaker bios, internal announcements, emails that ask for something, and personal profiles. Also use for any request to "cut the fluff", "make this clearer", "make it less corporate", "tighten this up", or "make this sound less like AI wrote it". Leads with the conclusion, names who does what, replaces categories with instances, keeps every number sourced, and never invents a fact.
---

# Plain Writing

Two failures produce most bad writing, and they look opposite while doing the same damage.

The first is **filler**: language that occupies space without carrying information. *"Going
forward, we are laser-focused on moving the needle for key stakeholders."* Strip the words and
nothing is left. The reader cannot tell what happened, who did it, or what to do next.

The second is **the confident blur**: claims pitched so broadly they cannot be checked. *"A
proven track record of delivering transformative outcomes."* It sounds like a fact and
behaves like a mood.

Language models produce both by default, because both are safe. Safe language is
indistinguishable across authors, and a sentence that could have been written by anyone about
anything tells the reader nothing.

> **Full framework:** `agent/PLAIN_WRITING.md` carries the complete version, including the
> Fact Ledger, register dials, document types, audit gate and worked examples.
> `tools/av_lint.py` checks the mechanical rules automatically.

## 1. Never invent a fact

This overrides everything else here.

- **No invented specifics.** Dates, numbers, names, employers, metrics, deadlines, ticket
  references. If you do not have it, ask or write a visible `[PLACEHOLDER]`. In work writing a
  fabricated detail does not merely embarrass; it propagates into decisions other people make.
- **No invented metrics.** No percentage, revenue figure, latency number, headcount or
  timeline unless the user supplied it. If they supplied it, keep it exactly as given. Do not
  round for effect.
- **No fabricated credentials.** Degrees, certifications, titles, employment dates,
  responsibilities held.
- **Inference is not fact.** "They mentioned the Q3 migration, so the deadline is probably
  end of September" is a guess wearing a fact's clothes. Ask, or bracket it.
- **Report every placeholder** back to the user. A bracket must never ship silently.

## 2. Lead with the point

Put the conclusion in the first sentence. Context, reasoning and caveats come after.

Most people write in the order they thought: background, analysis, conclusion. That is the
order of discovery, not the order of use. Your reader is deciding whether this needs their
attention at all, and they decide in one sentence.

*Buried:* "Following the migration work in Q2 and subsequent load testing, and after
reviewing capacity across regions, we have concluded that the launch date should move."

*Led:* "The launch should move to [DATE]. Load testing found the [REGION] cluster cannot take
the traffic, and adding capacity takes six weeks."

Does not apply to narrative writing, or where a conclusion needs its evidence first to land
honestly.

## 3. Cut the filler

**The test: delete the sentence. If nothing is lost, it was filler.** Then check what remains,
because filler hides inside real sentences as much as between them.

- **Throat-clearing openers.** "It is worth noting that", "I wanted to reach out to", "As you
  may be aware", "In order to". Delete and start at the verb.
- **Abstraction stacking.** "Alignment on strategic initiatives across workstreams." Every
  noun is a category rather than a thing. Name the actual thing.
- **Hedged non-statements.** "There may be some potential considerations around timing."
  Either there is a timing problem or there is not. Say which, then hedge only the genuinely
  uncertain part.

## 4. Name who does what

Passive and agentless constructions are how accountability disappears from a document.

| Agentless | Named |
|---|---|
| Mistakes were made | I approved the config change that caused it |
| It was decided to postpone | [NAME] postponed it after the security review |
| The deployment failed | The deploy failed because I skipped the staging run |

Passive voice is correct when the actor is genuinely unknown or irrelevant. It is wrong when
it is doing the work of avoiding a name the reader needs. In incident writeups, name systems
and decisions rather than people: "the deploy skipped staging" is blameless and specific at
once.

## 5. Specific beats abstract

Replace a category with an instance.

- Not "various stakeholders" but "the two teams that call this API".
- Not "performance improvements" but "the report page loads in under a second now".
- Not "extensive experience" but "six years, four of them on billing".

Be candid about the work, not about your competence. "The migration took three weeks longer
than I estimated" is professional. "I am bad at estimating" is a performance review you wrote
for someone else.

## 6. Every number carries its source

A number without provenance invites decisions it cannot support.

- Keep the user's figures exactly as given. Do not round or convert for rhetorical effect.
- Name the source inline where one is needed: "12% (from the [DASHBOARD] weekly export)".
- Keep a range a range, and an estimate an estimate.
- If you do not have the number, write `[FIGURE]` and report it. Never supply a plausible one.

## 7. Vary the length, then be consistent

Uniform sentence length is tiring to read and is the most measurable signature of machine
text. Mix short and long deliberately. Read it aloud; if it drones, break something.

Then hold your terms steady. If it is "the import job" in paragraph one, it is not "the
ingestion pipeline" in paragraph four. Same for date format, product capitalisation and
heading style. Every synonym makes the reader stop and ask whether you meant something else.

## 8. Preserve meaning under compression

Cutting filler must never quietly change a hedge into a commitment. "We expect to ship in
March" and "We ship in March" are different promises. When in doubt, keep the hedge and cut
elsewhere. If a draft changes how confident a claim sounds, say so when you deliver it. The
user is the one who has to stand behind it.

## 9. Words to cut

Blocking, cut every occurrence: empower, unlock, seamless, cutting-edge, state-of-the-art,
best-in-class, world-class, leverage, harness, delve, passionate about, driven by, committed
to, dedicated to, streamline, revolutionize, transformative, supercharge, unparalleled,
tapestry, testament to, at the forefront, paradigm shift, synergy, holistic approach, embark
on, the future of, user-centric, thrilled to announce, excited to share, humbled to, deep
dive into, look no further, in conclusion, it's worth noting.

Density limits, fine once and a signature in bulk: intricate, invaluable, exceptional,
pivotal, crucial, vital, comprehensive, innovative, dynamic, versatile, robust, myriad,
nuanced, meticulously, particularly, notably, significantly, undoubtedly, essentially,
ultimately, furthermore, moreover, additionally.

Workplace filler, the tier that accumulates unnoticed: circle back, touch base, move the
needle, low-hanging fruit, at the end of the day, going forward, socialize the, double-click
on, learnings, ideate, operationalize, actionable insights, north star, table stakes, drill
down, level set, loop in, thought leadership, mission-critical, frictionless, granular,
cadence, stakeholder buy-in, quick win, pain point, value proposition, strategic initiative,
wheelhouse, in the weeds, laser-focused, win-win, moving parts, at scale.

The complete lists live in section 9 of `agent/PLAIN_WRITING.md` and are enforced by
`tools/av_lint.py`.

Also cut: "Whether you're X or Y", "It's not just X, it's Y", "In a world where", openers that
define a common word, everything arriving in threes, and em dashes beyond one per document.

## 10. Delivery checklist

- [ ] Does sentence one carry the conclusion?
- [ ] Delete each sentence in turn. Does anything survive that should not?
- [ ] Does every specific trace to something the user gave you?
- [ ] Does every figure come from the user, unrounded, with a source where needed?
- [ ] For each passive construction, does the reader need the missing actor named?
- [ ] At least one concrete, checkable detail?
- [ ] Zero blocking words from section 9, and sparse use of the other two tiers?
- [ ] Do sentence lengths vary when read aloud?
- [ ] One term per thing, one date format, one heading style?
- [ ] Did compression turn any hedge into a commitment?
- [ ] Would you be comfortable if this were forwarded, unedited, to the most senior person on
      the list?

Optional machine check: `python3 tools/av_lint.py draft.md --profile professional`

Deliver the draft first, clean and uninterrupted, with no commentary inside it. Then, below a
rule: the facts you used and where each came from, every placeholder still open, and anything
you made sound more or less certain than the brief did.

## 11. When not to use this

Reference and API documentation, where predictable structure beats voice. Legal, medical,
regulatory and safety text, where standard phrasing has been tested. Error messages and UI
microcopy. Anything a reader must certify as their own work, including coursework, exams,
professional certification and peer review. Condolences and difficult personal news, where
leading with the point is wrong. And wherever a house style guide already governs: that wins.
