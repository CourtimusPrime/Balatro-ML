# Balatro Overview

High-level description of Balatro: what the game is, its goal, run structure, the cards you collect, win/loss conditions, run modifiers, and a glossary of core terms.

> As of: Balatro v1.0 base game (patch ~1.0.1n/1.0.1o, 2024–2025). PC/console base game, no mods.

## What Balatro Is

Balatro is a roguelike deckbuilder built around **poker hands**. You start each run with a 52-card standard playing-card deck. Each round you are dealt cards, select up to 5, and **play** them as a poker hand (Pair, Flush, Straight, etc.). The hand scores points; the goal is to score enough points to beat a target ("the Blind").

Crucially for this project: the player's objective in normal play is to **survive a run** (beat all blinds through Ante 8). However, the **score per hand** can grow astronomically — well into the billions, trillions, and beyond — because the engine multiplies chips by mult, and Jokers stack multiplicatively. This project trains an agent to **maximise score**, which leverages the same scoring engine but optimizes a different objective than mere survival.

## Scoring Model (core concept)

A played poker hand's score is computed from two running quantities:

- **Chips** — the additive base score. Each poker hand has a base chip value; played cards add their rank's chip value; enhancements/editions/jokers can add more.
- **Mult** — the multiplier applied to chips. Each poker hand has a base mult; jokers, editions, and enhancements modify it (some add to mult, some multiply mult).

Final round-score contribution ≈ **Chips × Mult** for the played hand. Both grow as you level hands (Planet cards), add Jokers, and enhance cards. Score is the headline metric this project optimizes; the project reward is **log-transformed** (see CLAUDE.md) because raw scores span many orders of magnitude.

## The Core Goal

- Each **Blind** has a chip-score requirement. You must reach or exceed it before running out of **hands** (plays) for that round.
- Beat the Small, Big, and Boss blind in each Ante to advance.
- **Win condition:** beat the Boss Blind of **Ante 8** (the final/"Showdown" boss). This completes a standard run.
- **Endless mode:** after winning, you may continue past Ante 8 (Ante 9+) with exponentially scaling requirements, for high-score chasing.

## High-Level Run Structure

A run is a sequence of **Antes** (numbered levels). Each Ante contains three **Blinds** played in order:

| Order | Blind | Chip requirement | Special effect | Can skip? | Must play? |
|-------|-------|------------------|----------------|-----------|------------|
| 1 | Small Blind | 1× ante base | None | Yes (for a Tag) | No |
| 2 | Big Blind | 1.5× ante base | None | Yes (for a Tag) | No |
| 3 | Boss Blind | usually 2× ante base (varies) | A special rule/debuff | No | Yes |

After **beating** any blind you "cash out" (collect $) and enter the **Shop** before the next blind. (Skipping a Small/Big blind gives a Tag instead of a shop visit and skips that blind's reward.) See `01-game-loop-and-economy.md` for the full loop, economy, and tag list.

Base chip requirements scale by ante (and by stake tier). Approximate base-game values:

| Ante | White–Blue base | Green–Purple+ | Higher stakes (Purple+) |
|------|-----------------|---------------|--------------------------|
| 1 | 300 | 300 | 300 |
| 2 | 800 | 900 | 1,000 |
| 3 | 2,000 | 2,600 | 3,200 |
| 4 | 5,000 | 8,000 | 9,000 |
| 5 | 11,000 | 20,000 | 25,000 |
| 8 | 50,000 | 100,000 | 200,000 |

⚠️ Antes 6–7 omitted above (not confirmed in this research pass); exact per-stake scaling differs by stake. Treat the table as indicative, not authoritative for every cell. The Boss Blind requirement is generally 2× the ante base, but specific bosses override this (e.g. The Wall ≈ 4×, The Needle ≈ 1×). See a dedicated blinds file for exact boss values.

## The Four Card "Types" You Collect

1. **Jokers** — passive/triggered modifiers held in Joker slots (default **5** slots). They are the primary engine of score growth (add chips, add mult, multiply mult, generate money, etc.). Jokers come in rarities (Common/Uncommon/Rare/Legendary) and can carry **Editions**.
2. **Consumables** — single-use cards held in consumable slots (default **2** slots), in three families:
   - **Tarot cards** — enhance/transform playing cards, generate money, etc.
   - **Planet cards** — level up a specific poker hand (raising its base chips and mult permanently for the run).
   - **Spectral cards** — powerful, often high-risk transformations (add seals, editions, destroy cards, etc.).
3. **Vouchers** — permanent, run-long upgrades bought from the shop (one voucher slot per shop). Examples: more shop slots, more interest cap, boss-reroll ability.
4. **Playing-card modifications** — changes applied to the actual playing cards in your deck:
   - **Enhancements** (e.g. Bonus, Mult, Wild, Glass, Steel, Gold, Stone, Lucky) — change how a card scores or behaves.
   - **Editions** (Foil, Holographic, Polychrome, Negative) — also apply to Jokers; add chips/mult/slots.
   - **Seals** (Gold, Red, Blue, Purple) — trigger effects when the card is played, held, or discarded.

## Loss Condition

You **lose the run** if you fail to meet a Blind's chip requirement before running out of **hands** for that round (you also cannot skip a Boss Blind). Certain effects (e.g. the Mr. Bones joker) can save you from one loss. Running out of discards does not lose the round by itself — only running out of hands without meeting the target does.

## Run Modifiers Overview

Two orthogonal sets of modifiers shape difficulty and starting conditions (details in their own files):

- **15 Decks** — each deck changes starting conditions or rules (e.g. Red Deck: +1 discard; others change hands, money, slots, suits, etc.). The chosen deck is fixed for the run.
- **8 Stakes** — escalating difficulty tiers (White, Red, Green, Black, Blue, Purple, Orange, Gold). Higher stakes raise chip requirements, remove some rewards (e.g. Red Stake removes the Small Blind reward), and add penalties. Beating a stake unlocks the next.

## Glossary of Core Terms

| Term | Definition |
|------|-----------|
| **Chips** | Additive base score of a played hand (from the hand type, card ranks, and bonuses). |
| **Mult** | The multiplier applied to Chips. Final hand score ≈ Chips × Mult. |
| **Hand** | (1) A poker hand you play (Pair, Flush, etc.); (2) one of your limited *plays* per round (default 4 hands/round). |
| **Discard** | Throwing away selected cards to draw replacements without scoring; limited per round (default 3). |
| **Ante** | A numbered level grouping three blinds; Ante 8's boss is the standard win point. |
| **Blind** | A scoring target within an ante: Small, Big, or Boss. |
| **Round** | One blind attempt (the per-round play/discard loop). |
| **Joker** | A held modifier card that alters scoring/economy; default 5 slots. |
| **Consumable** | A single-use Tarot/Planet/Spectral card; default 2 slots. |
| **Voucher** | A permanent run-long upgrade bought in the shop. |
| **Enhancement** | A modification to a playing card changing how it scores/behaves (Bonus, Mult, Wild, Glass, Steel, Gold, Stone, Lucky). |
| **Edition** | A visual/scoring overlay (Foil, Holographic, Polychrome, Negative) applied to playing cards or Jokers. |
| **Seal** | A stamp on a playing card (Gold, Red, Blue, Purple) triggering an effect on play/hold/discard. |
| **Tag** | A reward gained for skipping a Small/Big blind (see economy file). |
| **Stake** | A difficulty tier (8 total) increasing requirements/penalties. |
| **Deck** | A starting configuration (15 total) altering rules/start state. |
| **Hand level** | A poker hand's upgrade level, raised by Planet cards, increasing its base chips & mult. |

## See also

- `01-game-loop-and-economy.md`
