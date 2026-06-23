# Balatro Knowledge Base — Navigation

This folder is a comprehensive, research-backed reference for the game **Balatro**: rules,
mechanics, scoring, and every item (jokers, consumables, vouchers, packs, blinds, decks,
stakes). It exists to serve as ground-truth game knowledge for the Balatro ML project —
observation-space design, action validity, reward shaping, and strategy analysis should all
trace back to the facts documented here.

> **Game version covered:** Balatro v1.0 base game (patch ~1.0.1n / 1.0.1o, 2024–2025),
> PC/console, no mods. Each file restates its version in a `> As of:` note.
>
> **Primary source:** community wiki [balatrowiki.org](https://balatrowiki.org). The Fandom
> wiki (balatro.fandom.com) blocks automated fetches (HTTP 403), so it was used only via search
> corroboration. Values were cross-checked across sources; see [Known gaps](#known-gaps--lowest-confidence-data) below.

---

## Where to find specific information

| If you need…                                                         | Go to                                                          |
| -------------------------------------------------------------------- | -------------------------------------------------------------- |
| What the game is, the goal, win/loss, core glossary                  | [`00-overview.md`](00-overview.md)                             |
| Per-round loop, hands/discards, shop, money, interest, **Skip Tags** | [`01-game-loop-and-economy.md`](01-game-loop-and-economy.md)   |
| The score formula, evaluation **order**, +Mult vs Xmult              | [`02-scoring-system.md`](02-scoring-system.md)                 |
| All poker hands, base Chips/Mult, per-level scaling                  | [`03-poker-hands.md`](03-poker-hands.md)                       |
| Card ranks/suits, **Enhancements, Editions, Seals**, retriggers      | [`04-playing-cards.md`](04-playing-cards.md)                   |
| Every joker (rarity, cost, effect, unlock)                           | [`05-jokers.md`](05-jokers.md)                                 |
| Tarot cards (22)                                                     | [`06-tarot-cards.md`](06-tarot-cards.md)                       |
| Planet cards (12) and which hand each levels                         | [`07-planet-cards.md`](07-planet-cards.md)                     |
| Spectral cards (18), incl. The Soul / Black Hole                     | [`08-spectral-cards.md`](08-spectral-cards.md)                 |
| Vouchers (16 base→upgrade pairs)                                     | [`09-vouchers.md`](09-vouchers.md)                             |
| Booster packs (types, sizes, costs)                                  | [`10-booster-packs.md`](10-booster-packs.md)                   |
| Ante/blind progression, chip requirements, **all boss blinds**       | [`11-blinds-and-antes.md`](11-blinds-and-antes.md)             |
| The 15 decks and their modifiers                                     | [`12-decks.md`](12-decks.md)                                   |
| The 8 stakes (cumulative difficulty)                                 | [`13-stakes.md`](13-stakes.md)                                 |
| Build archetypes, synergies, score-maximization meta                 | [`14-strategy-and-synergies.md`](14-strategy-and-synergies.md) |

---

## File-by-file summary

- **`00-overview.md`** — Roguelike-deckbuilder premise; the goal (beat blinds, survive to and beat
  Ante 8's boss; Endless mode beyond); run structure (Antes → Small/Big/Boss → shop); the four
  collectible card types; win/loss conditions; 17-term glossary.

- **`01-game-loop-and-economy.md`** — Play/Discard loop (hand size 8, 4 hands, 3 discards, ≤5 cards
  per play); cash-out and shop (2 card + 2 pack + 1 voucher slots; reroll $5 +$1 each); the full
  money economy (blind rewards, interest $1/$5 capped $5, Gold cards, selling); 5 joker / 2
  consumable default slots; **24 Skip Tags** table; boss-blind reroll.

- **`02-scoring-system.md`** — `score = Chips × Mult`; the 5-phase evaluation order (base hand →
  scored cards → held-in-hand → jokers left-to-right → final multiply); rank chip values; scored vs
  held effects; hand-level additive scaling; **the +Mult vs ×Mult ordering rule** (the single most
  important scoring mechanic); rounding; the ~1.7977e308 score cap.

- **`03-poker-hands.md`** — Full ranked table of all 12 hands (9 standard + Five of a Kind, Flush
  House, Flush Five) with base Chips/Mult and per-level increments; requirements for the special
  hands; associated planet per hand; worked scaling math.

- **`04-playing-cards.md`** — 13 ranks / 4 suits with chip values; **8 Enhancements**, **4 Editions**
  (note: Negative does NOT apply to playing cards), **4 Seals**; stacking rules (one of each per
  card); retrigger sources.

- **`05-jokers.md`** — All **150 jokers** (Common 61 / Uncommon 64 / Rare 20 / Legendary 5), grouped
  by rarity with Name | Cost | Effect | Unlock. Tags scaling vs static jokers; explains rarity
  rates, slot limit, editions on jokers, and that joker **order** matters. (Largest file.)

- **`06-tarot-cards.md`** — 22 Tarot cards with exact effects and targeting caps.
- **`07-planet-cards.md`** — 12 Planet cards (9 standard + Planet X / Ceres / Eris) and the hand each levels.
- **`08-spectral-cards.md`** — 18 Spectral cards with effects and risks (The Soul → Legendary joker; Black Hole → level all hands).
- **`09-vouchers.md`** — 32 vouchers as 16 base→upgrade pairs ($10 each, one per ante, permanent).
- **`10-booster-packs.md`** — 5 pack types × Normal/Jumbo/Mega (15 variants) with cost / shown / pick counts.

- **`11-blinds-and-antes.md`** — 8-ante structure; blind multipliers (Small 1× / Big 1.5× / Boss 2×,
  plus exceptions); White-Stake ante base-chip curve; blind rewards; **28 boss blinds** (23 regular +
  5 finisher/Showdown) with effects; boss selection rules; reroll vouchers.

- **`12-decks.md`** — All 15 decks with modifier and unlock.
- **`13-stakes.md`** — All 8 stakes (White→Gold), cumulative; Eternal/Perishable/Rental joker stickers.

- **`14-strategy-and-synergies.md`** — The scaling principle (why Xmult dominates); 9 build
  archetypes with concrete joker names; synergy table; economy discipline; boss-blind counterplay;
  deck/stake notes; Endless score-max thesis. Synthesizes the rest of the KB toward the project goal
  of **maximizing score**. (Contains some flagged opinion/meta claims — see below.)

---

## Cross-cutting topic index

- **+Mult vs ×Mult (additive vs multiplicative):** core idea in [`02`](02-scoring-system.md); applied
  per-joker in [`05`](05-jokers.md); strategic consequences in [`14`](14-strategy-and-synergies.md).
- **Retriggers:** mechanic & sources in [`04`](04-playing-cards.md); joker sources in [`05`](05-jokers.md); builds in [`14`](14-strategy-and-synergies.md).
- **Hand leveling:** scaling math in [`02`](02-scoring-system.md)/[`03`](03-poker-hands.md); the cards that do it in [`07`](07-planet-cards.md) (and Black Hole in [`08`](08-spectral-cards.md)).
- **Money / interest:** rules in [`01`](01-game-loop-and-economy.md); Gold cards/seals in [`04`](04-playing-cards.md); economy vouchers in [`09`](09-vouchers.md); economy builds in [`14`](14-strategy-and-synergies.md).
- **Slots (joker/consumable/shop):** defaults in [`01`](01-game-loop-and-economy.md); modified by vouchers ([`09`](09-vouchers.md)), decks ([`12`](12-decks.md)), and editions ([`04`](04-playing-cards.md)).
- **Joker stickers (Eternal/Perishable/Rental):** introduced by stakes in [`13`](13-stakes.md); referenced in [`05`](05-jokers.md)/[`14`](14-strategy-and-synergies.md).
- **The Soul / Legendary jokers:** spectral source in [`08`](08-spectral-cards.md); the 5 legendaries in [`05`](05-jokers.md).

---

## Known gaps / lowest-confidence data

Carry these caveats into any downstream use. None are invented values — they rest on a single
source or are version-sensitive:

- **Ante chip-requirement curve:** the White-Stake base curve is well-attested, but **antes 6–7 exact
  values and the steeper per-stake curves (Green/Purple onward) are not fully pinned down**, and the
  Endless-mode scaling formula is not reproduced. See [`11-blinds-and-antes.md`](11-blinds-and-antes.md).
- **Special-hand per-level values** (Five of a Kind / Flush House / Flush Five, esp. Eris) rest mainly
  on one fetchable source — spot-check against the in-game Run Info screen if exact certainty matters. See [`03`](03-poker-hands.md).
- **Joker edge values** — e.g. Misprint's +0..+23 Mult upper bound, a few suit/economy phrasings — match community consensus but weren't triple-checked. See [`05`](05-jokers.md).
- **Stake sticker rates (~30%)** and exact in-game tooltip wording are community figures and may vary by patch. See [`13`](13-stakes.md).
- **Strategy file opinion:** per-deck "best for score" rankings and the Endless "two Xmult engines"
  thesis in [`14`](14-strategy-and-synergies.md) are synthesized guidance/community consensus, not wiki-stated rules.

To refresh or close a gap, re-run a research pass against balatrowiki.org for the specific page, or
verify against the live game's Run Info / collection screens.
