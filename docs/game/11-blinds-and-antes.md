# Blinds and Antes

Reference for Balatro's ante/blind progression, chip-score requirements, blind rewards, and the full roster of boss blinds (regular + finisher). Intended as ground-truth game knowledge for the RL agent.

> As of: v1.0 base game (~1.0.1n / 1.0.1o)
> Total boss blinds: 28 (23 regular + 5 finisher/showdown)

---

## Ante Structure

- A **run** is won by defeating **Ante 8**. Each ante is cleared in order; you cannot win earlier.
- Every ante consists of **three blinds played in sequence**:
  1. **Small Blind** (1x ante base chips)
  2. **Big Blind** (1.5x ante base chips)
  3. **Boss Blind** (typically 2x ante base chips)
- The Small and Big Blind can each be **skipped** in exchange for a **Skip Tag** (forfeits the cash reward). The **Boss Blind cannot be skipped** — it must be played and beaten.
- After defeating the Ante 8 boss (a Finisher Blind), the run is won. The player may continue into **Endless Mode**, where antes keep incrementing (9, 10, 11, ...) with rapidly escalating chip requirements. Finisher bosses recur on every multiple of 8 (Ante 16, 24, ...).

### Blind sequence per ante

| Order | Blind | Score multiplier (x ante base) | Can skip? | Reward (White stake) |
|-------|-------|-------------------------------|-----------|----------------------|
| 1 | Small Blind | 1.0x | Yes (for a tag) | $3 |
| 2 | Big Blind | 1.5x | Yes (for a tag) | $4 |
| 3 | Boss Blind | 2.0x (varies, see below) | No | $5 (regular) / $8 (finisher) |

---

## Blind Chip (Score) Requirements

Each ante has a **base chip value**. The required score for a blind = ante base x the blind's multiplier. The base values below are for **White Stake** (the base difficulty). Higher stakes use a steeper curve — see "Stake variation" below.

### Ante base chip requirements (White Stake, Antes 0–8)

| Ante | Base chips | Small (1x) | Big (1.5x) | Boss (2x typical) |
|------|-----------|-----------|-----------|-------------------|
| 0 (and lower) | 100 | 100 | 150 | 200 |
| 1 | 300 | 300 | 450 | 600 |
| 2 | 800 | 800 | 1,200 | 1,600 |
| 3 | 2,000 | 2,000 | 3,000 | 4,000 |
| 4 | 5,000 | 5,000 | 7,500 | 10,000 |
| 5 | 11,000 | 11,000 | 16,500 | 22,000 |
| 6 | 20,000 | 20,000 | 30,000 | 40,000 |
| 7 | 35,000 | 35,000 | 52,500 | 70,000 |
| 8 | 50,000 | 50,000 | 75,000 | 100,000 |

> ⚠️ Past Ante 8 (Endless Mode) the base scales hyper-exponentially toward astronomical values; the closed-form curve is not reproduced here. Boss multipliers still apply on top of the base.

### Boss multiplier exceptions

Most bosses require **2x** the ante base, but a few differ:

| Boss | Multiplier | Effect on score requirement |
|------|-----------|-----------------------------|
| The Needle | **1x** | Easiest score, but only 1 hand allowed |
| The Wall | **4x** | Double a normal boss |
| Violet Vessel (finisher) | **6x** | Highest score requirement in the game |

### Stake variation

The base chip values above are the **White Stake** curve. Starting at certain higher stakes the required-score curve becomes steeper (notably from **Green Stake** onward, which uses a more aggressive scaling). The multiplier structure (Small 1x / Big 1.5x / Boss 2x) is the **same across all stakes** — only the per-ante base values change. Stakes also alter blind rewards: on **Red Stake and higher, the Small Blind awards no money**.

---

## Blind Rewards

| Blind | Cash for beating | Skip behavior |
|-------|------------------|---------------|
| Small Blind | $3 (Red Stake+: $0) | Skipping forfeits cash, grants a Skip Tag |
| Big Blind | $4 | Skipping forfeits cash, grants a Skip Tag |
| Boss Blind (regular) | $5 | Cannot be skipped |
| Finisher / Showdown Blind | $8 | Cannot be skipped |

Skipping a blind also advances past it with no shop visit for that blind, and the tag's effect triggers per the tag's rules.

---

## Boss Blinds

Boss blinds are the final blind of each ante and apply a special restriction or debuff for that round. There are **23 regular boss blinds** and **5 finisher (Showdown) boss blinds**.

### Selection rules

- One boss is chosen **randomly** per ante from the **eligible pool** (bosses whose minimum-ante requirement is met).
- **Ante 1 (and lower) can only spawn 8 specific bosses** — those with no minimum-ante gate.
- The game tracks appearances: **a boss will not reappear until every eligible boss has appeared once** (defeating or rerolling counts as an appearance). This guarantees variety before repeats.
- **Finisher bosses appear only on antes that are multiples of 8** (Ante 8, 16, 24, ...). One of the 5 finishers is chosen at random for those antes; regular bosses never appear there.

### Reroll-boss vouchers

| Voucher | Effect | Cost per reroll |
|---------|--------|-----------------|
| **Director's Cut** | Reroll the boss blind **once per ante** | $10 |
| **Retcon** (upgrade of Director's Cut) | Reroll the boss blind **unlimited times** per ante | $10 each |

Rerolling on a multiple-of-8 ante always produces another **Showdown (finisher)** blind; on other antes it always produces a **regular** boss. (Related: selling the **Luchador** joker disables the current boss's effect; the **Chicot** joker disables all boss effects for the round.)

### Regular Boss Blinds (23)

| Name | Effect | Notes |
|------|--------|-------|
| The Hook | Discards 2 random cards held in hand after every played hand | Min ante: any |
| The Club | All Club cards are debuffed | Min ante: any; suit debuff |
| The Goad | All Spade cards are debuffed | Min ante: any; suit debuff |
| The Window | All Diamond cards are debuffed | Min ante: any; suit debuff |
| The Head | All Heart cards are debuffed | Min ante: any; suit debuff |
| The Psychic | Must play exactly 5 cards (not all need to score) | Min ante: any |
| The Manacle | -1 hand size | Min ante: any |
| The Pillar | Cards played earlier this ante are debuffed | Min ante: any |
| The House | First hand is drawn face down | Min ante: 2 |
| The Wall | Extra-large blind — requires **4x** base chips | Min ante: 2; no card effect, just high score |
| The Wheel | 1 in 7 cards is drawn face down during the round | Min ante: 2 |
| The Arm | Permanently decreases the level of the played poker hand by 1 | Min ante: 2 |
| The Fish | Cards are drawn face down after each hand played | Min ante: 2 |
| The Water | Start the round with 0 discards | Min ante: 2 |
| The Mouth | Only one poker hand type can be played all round | Min ante: 2 |
| The Needle | Play only **1 hand** for the whole round | Min ante: 2; score requirement is only **1x** base |
| The Flint | Base Chips and Mult of played hands are halved for the round | Min ante: 2 |
| The Mark | All face cards are drawn face down | Min ante: 2 |
| The Eye | No repeat hand types this round (each hand type usable once) | Min ante: 3 |
| The Tooth | Lose $1 per card played | Min ante: 3 |
| The Plant | All face cards (J, Q, K) are debuffed | Min ante: 4 |
| The Serpent | After every Play or Discard, always draw exactly 3 cards (ignores hand size) | Min ante: 5 |
| The Ox | Playing your most-played hand type this run sets your money to $0 | Min ante: 6 |

> The 8 bosses with "any" minimum ante (Hook, Club, Goad, Window, Head, Psychic, Manacle, Pillar) make up the Ante-1 pool.

### Finisher (Showdown) Boss Blinds (5) — Antes 8, 16, 24, ...

| Name | Effect | Notes |
|------|--------|-------|
| Amber Acorn | Flips and shuffles all Joker cards (faces hidden, positions randomized) | Min ante: 8 |
| Verdant Leaf | All playing cards are debuffed until 1 Joker is sold | Min ante: 8 |
| Violet Vessel | Very large blind — requires **6x** base chips | Min ante: 8; highest score in the game |
| Crimson Heart | One random Joker is disabled each hand (the disabled Joker changes every hand) | Min ante: 8 |
| Cerulean Bell | Forces 1 card in hand to always be selected | Min ante: 8 |

---

## Quick Reference Summary

- 8 antes to win; each = Small → Big → Boss.
- Score = ante base x {Small 1.0, Big 1.5, Boss 2.0}, with boss exceptions (Needle 1x, Wall 4x, Violet Vessel 6x).
- White-stake base curve: 300 / 800 / 2,000 / 5,000 / 11,000 / 20,000 / 35,000 / 50,000 for antes 1–8.
- Rewards: Small $3 (Red+ $0), Big $4, Boss $5, Finisher $8. Skipping Small/Big forfeits cash for a tag; Boss is mandatory.
- 28 bosses total: 23 regular + 5 finisher. Finishers only on multiples of 8.
- Reroll boss with Director's Cut (1/ante) or Retcon (unlimited); Luchador/Chicot disable boss effects.

---

## See also

- Vouchers (Director's Cut, Retcon)
- Jokers (Luchador, Chicot, Matador interactions with boss effects)
- Tags (Skip Tags granted when skipping Small/Big blinds)
- Stakes and difficulty scaling
- Card states: debuffed, face-down, force-selected
