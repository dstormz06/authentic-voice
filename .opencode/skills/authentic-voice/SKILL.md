---
name: authentic-voice
description: Write copy that reads as a real human, not an LLM. Use for personal sites, homepages, about pages, portfolios, bios, taglines, READMEs, blurbs, and any request to "make this sound human", "make it less AI", "not sound generic", or "self-deprecating". Kills marketing clichés, vague confident claims, and AI tells; forces specific mundane facts, understated personality, and deliberate content choices. Ask the person for real details instead of inventing them.
---

# Authentic Voice

Everything a model writes defaults to the same smooth, confident, vaguely impressive
register: "Empowering developers to build the future." Real people do not write like that.
Real people undersell themselves, name awkward specifics, admit what they are bad at, and
have a few small habits that show up consistently. This skill makes output read as though a
specific person wrote it.

The reason the generic register is so tell-tale is a fact about language models: they
optimise for safeness, and safeness looks identical across every author. A human page is the
product of one person's constraints: what they actually did, what actually happened, what
they are actually willing to say. The more of that local, irreplaceable specificity you pull
in, the more human the result.

Use this whenever the writing is *for a person*: their page, their bio, their README, their
voice. Do not use it to impersonate anyone or to fabricate credentials, and do not bolt an
artificial persona onto brand copy without the client asking for it.

> **Full framework:** `agent/AUTHENTIC_VOICE.md` carries the complete version, including the
> Fact Ledger, the register dials, channel profiles and the portable master prompt.
> `tools/av_lint.py` checks the mechanical rules automatically.

## 0. Read the room, then ask before inventing

1. **Personal or brand?** Personal site, bio, portfolio, blog intro, about page means apply
   this fully. Brand or marketing copy means keep the register principles and skip the
   persona ones. Writing as a third party who did not ask you to is off limits entirely.
2. **What real facts exist?** Mine the brief, the repo, the chat history, their other
   writing. Every specific you recover is a gift.
3. **Ask when facts are missing. Never fabricate.** If you are writing a bio and do not know
   the year, the languages, or the projects, ask one batched set of questions or use a
   visible placeholder such as `[since 2022]`. Invented specifics presented as real are a lie
   and they embarrass the person whose name is on the page. If they want something openly
   fictional, a parody or anonymous page, that is their call, and it must read as playful.
4. **If the request is ambiguous, one question, then go.** Decide from context. Only ask when
   the voice direction genuinely branches, such as self-effacing nerd versus deadpan.

## 1. Kill the marketing register

Default AI prose is confident, positive and vague. A human "about" reads closer to
*"Hobbyist rust and elixir developer. Attempting to program."* and ends with
*"Made with pain. <3"*.

The one-sentence filter: **if this line could appear on any random company's landing page,
rewrite it.** It does not matter that it sounds nice. Sounding nice in that exact way is the
tell.

| Generic default | Human |
|---|---|
| "Empowering developers to build the future" | "Hobbyist rust and elixir developer. Attempting to program." |
| "Passionate about clean, scalable software" | "I write Rust and apologise to typecheckers a lot." |
| "I strive to craft delightful web experiences" | "I make websites. Some of them load fast." |
| "Driven by curiosity and a love of learning" | "Taken coding seriously since 2022. Still learning what that means." |

Tactics that read as a person rather than a persona:

- **Self-deprecation reads as confidence.** Someone who admits a struggle is showing they do
  not need to perform. A model that sounds flawless sounds fake.
- **Undersell the scope.** "Attempting to program" signals more capability than "leading
  transformative engineering initiatives". Claims that could be fact-checked and found true
  are the strongest ones available.
- **First person, and vary sentence length.** Humans switch lengths. A two-word sentence next
  to a longer one reads alive.
- **Be willing to be disliked.** A real voice has an opinion: mild, specific, not trying to
  offend. Perfectly inoffensive is the same thing as generic.
- **A little edge, never abuse.** The amount of snark a normal person has, matched to the
  person you are writing for.

## 2. Specific mundane facts over platitudes

This is the biggest lever and the one models resist hardest, because a model cannot know a
person's real facts and fills the gap with confident generic claims instead.

- **Reach for the concrete and ordinary:** "taken coding seriously since 2022", "a plush
  shark watches over my desk", "the blog updates every few months, optimistically". Not "a
  decade of experience across modern technology stacks".
- **Unflattering details beat smooth ones.** "I am bad at CSS" is specific and therefore
  credible. Smooth claims are the tell; ragged facts are the proof.
- **Let dates, counts and environments be real.** "Since 2022." "Three side projects, two
  abandoned." Never invent fake-precise numbers such as `92%` or `4.1x` to sound rigorous.
- **The rule that keeps this honest:** never present an invented fact as true. If you know
  there is a plush shark, describe the plush shark. If you do not know, ask or bracket it.

## 3. Adopt one small, consistent system

A real person's site has habits: `code:work`, `blog:posts`, `chat:discord`, the same colon
convention everywhere. That consistency is itself a human signal, because models randomise
and normalise instead of committing to one idiosyncrasy.

- Pick **one micro-convention** (label:value, terminal `$` prefixes, a repeated lowercase
  header, lowercase throughout) and apply it **everywhere, without exception**. Consistency
  is the signal. The specific choice barely matters.
- This covers words and structure, not just typography: a repeated sign-off, one recurring
  joke, one naming pattern. A habit, not scattered cleverness.
- Do not stack five quirks (monospace plus all-lowercase plus colon-labels plus emoji plus
  memes). One coherent habit reads as a person. Several read as "look how quirky I am", which
  is the voice equivalent of a rainbow gradient.

## 4. Deliberate artifact choices

Defaults dodge anything that could look bad: safe stock photos, safe gradients, safe icons. A
person's real page reaches for what is *theirs*: an anime avatar, a photo of a plush shark,
an old-web `88x31` button row. Nostalgia and old-web references are strong signals precisely
because no default generator reaches for them.

For content this means: when choosing examples, metaphors, references and accents, reach for
the specific, personal or deliberately old-fashioned rather than the smooth current default.
Reference things a real person would actually have: a webring button, a `.dotfiles` page, a
"now" page, a guestbook. If the person has a real artifact, use the real one with genuine
provenance. Never describe something as live unless it will actually be live.

## 5. Restraint: near-black and one accent

The default AI palette is a rainbow gradient. The human default is near-black with **one**
accent. The same instinct applies to voice and claims.

- **One accent in every dimension.** One personality accent, one stylistic accent, one colour
  accent. Restraint reads as taste. The accent applied everywhere reads as template.
- **Undersell to the point of risk.** "Made with pain. <3" works because it is humble *and*
  specific. If your draft would impress a stranger, it probably overpromises.
- If you can count the clever moments, cut half of them. One memorable thing beats six cute
  things.

## 6. AI tells to strip before revealing output

Scan for these and replace every one:

- **Confident-vague word clusters:** "empower", "unlock", "seamless", "cutting-edge",
  "robust", "leverage", "passionate about", "driven by", "committed to", "dedicated to",
  "harness", "delve", "in today's fast-paced world", "on a mission to". The complete list
  lives in section 9.1 of `agent/AUTHENTIC_VOICE.md` and is enforced by `tools/av_lint.py`.
- **Fake-precise numbers:** `92%`, `4.1x`, `5.8mm` with no real source. If it is not a real
  fact, remove it or mark it clearly as an example.
- **Formulaic structure:** every list of three, every "Whether you're ... or ...", every
  paragraph that opens with a definition as filler.
- **Uniform rhythm:** if every sentence is roughly the same length, vary several on purpose.
- **The humility you cannot mean:** "I'm so grateful to share", "it's been a journey", "as a
  passionate developer". These fake-humble phrases are as tell-tale as the confident ones.
- **Excessive dashes and an aside on every line.** Personal copy uses zero em dashes and zero
  en dashes. One per page elsewhere, not one per paragraph.

## 7. Examples

**Example A, personal homepage hero.**

*Generic:*
> Hi, I'm Sarah, a passionate web developer empowering teams to build delightful digital
> experiences. Driven by curiosity and a love of learning, I specialize in crafting scalable,
> user-centric applications that solve real-world problems. Let's build the future together.

*With this skill* (facts gathered from the person):
> sert is my name, sarah
> frontend developer, taken seriously since 2022
> favorite feature: the delete key
> code:github . blog:thoughts . chat:discord
> this site has zero frameworks and one (1) opinion

One convention throughout (lowercase plus `label:value`), scope undersold, one opinion, no
marketing claims.

**Example B, README blurb.**

*Generic:*
> This project empowers developers to streamline their workflow with a cutting-edge, robust
> solution. Contribute today to help shape the future of development!

*With this skill:*
> toggl is a tiny timer for people who forget to stop timers.
> i built it because i kept burning my dinner while timing pasta.
> works on desktop. probably. tested until tuesday.
> install it with the one command in the makefile, or do not.
> it does not do rice.

## 8. Delivery checklist

Before calling content done:

- [ ] Could any line appear on a random company's landing page? Rewrite it.
- [ ] Does it name at least one specific, ideally unflattering, mundane fact?
- [ ] Is every specific fact real, provided, or clearly fictional with permission?
- [ ] One consistent micro-convention, applied everywhere without exception?
- [ ] One accent in voice, one in style, and no more than that?
- [ ] Does the register undersell overall?
- [ ] Zero AI tells from section 6, zero em dashes, zero unsourced numbers?
- [ ] Would this person actually say these words out loud?

Optional machine check: `python3 tools/av_lint.py draft.md --profile strict`

## 9. Casual social channels only

Research on AI-generated Discord text found two robust markers: descriptions cluster around a
prompt-shaped structure, most visibly a fixed sentence count, and they carry far fewer casual
discourse markers than human text. The countermeasures below apply **only** to casual social
copy. Do not let them leak into bios, READMEs or brand copy, where they read as costume.

1. **No fixed sentence count.** Never write exactly three sentences describing a server or a
   hobby. Humans write one line, or eleven, or a bullet list, or a fragment.
2. **Casual discourse markers belong here:** "idk", "ngl", "lol", "fr", "tbh", "so yeah".
   Integrated naturally, not sprinkled as decoration.
3. **Specific anchors, not broad statements.** Not "random chat" but "someone argues about
   linux distros at 3am roughly weekly".
4. **Mix casual and specific vocabulary.** Casual register with real references in it.
5. **Loose grammar is permitted here only:** fragments, comma splices, a trailing thought.
   This is register, not error. Never misspellings, never invented facts.
6. **Uneven rhythm.** Two-word fragments next to thirty-word run-ons.
7. **Personal references only if real.** A memory you were given, not one you imagined.

## 10. Scope limits

Do not use this for reference documentation, safety, legal, medical or financial notices,
error messages, or anywhere a reader must certify they wrote the text themselves. Clarity and
standard phrasing exist for good reasons in those places.

This skill produces copy that reads as human. It makes no claim about the behaviour of any
AI-detection tool, and you must not promise one.

---

*Craft rules derived from published work on linguistic differences between human and machine
text: sentence-length variability, lexical diversity, discourse-marker frequency, hedging
versus boosting, and prompt-shaped structural regularities in AI-generated social text.
Sources indexed in `research-papers-index.md`, each cited under its own licence, with no
paper text reproduced.*
