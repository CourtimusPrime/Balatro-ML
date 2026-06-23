# Poker Hands

Every poker hand Balatro recognizes, in ranking order, with base Chips/Mult at Level 1 and per-level scaling.

> As of: Balatro v1.0 (patch 1.0.1n/1.0.1o)

## Complete Hand Table

Listed from lowest to highest base value. "Per-level" is the amount of base Chips / base Mult **added per level** when the hand's Planet card is played (see `07-planet-cards.md`).

| # | Hand | Base Chips (L1) | Base Mult (L1) | +Chips / level | +Mult / level | Planet card | Type |
|---|------|----------------|----------------|----------------|---------------|-------------|------|
| 1 | High Card | 5 | 1 | +10 | +1 | Pluto | Standard |
| 2 | Pair | 10 | 2 | +15 | +1 | Mercury | Standard |
| 3 | Two Pair | 20 | 2 | +20 | +1 | Uranus | Standard |
| 4 | Three of a Kind | 30 | 3 | +20 | +2 | Venus | Standard |
| 5 | Straight | 30 | 4 | +30 | +3 | Saturn | Standard |
| 6 | Flush | 35 | 4 | +15 | +2 | Jupiter | Standard |
| 7 | Full House | 40 | 4 | +25 | +2 | Earth | Standard |
| 8 | Four of a Kind | 60 | 7 | +30 | +3 | Mars | Standard |
| 9 | Straight Flush | 100 | 8 | +40 | +4 | Neptune | Standard |
| 10 | Five of a Kind | 120 | 12 | +35 | +3 | Planet X | Special / secret |
| 11 | Flush House | 140 | 14 | +40 | +4 | Ceres | Special / secret |
| 12 | Flush Five | 160 | 16 | +50 | +3 | Eris | Special / secret |

Notes:
- **Royal Flush** is recognized as a hand visually but is **not a separate scoring tier** — it scores and levels identically to **Straight Flush** (shares its 100 × 8 base and Neptune's leveling). There is no Royal Flush planet card.
- The three special hands (Five of a Kind, Flush House, Flush Five) do **not** appear in the Run Info hand list until the player has scored each at least once; their Planet cards (Planet X, Ceres, Eris) also only appear in the shop after the hand has been discovered.

## Standard Hand Requirements

| Hand | Requirement |
|------|-------------|
| High Card | No combination; the single highest card scores |
| Pair | Two cards of the same rank |
| Two Pair | Two cards of one rank + two of another rank |
| Three of a Kind | Three cards of the same rank |
| Straight | Five cards of sequential rank (Ace can be high or low; gaps allowed only via the Shortcut joker) |
| Flush | Five cards of the same suit (four with the Four Fingers joker) |
| Full House | Three of a kind + a pair |
| Four of a Kind | Four cards of the same rank |
| Straight Flush | Five sequential cards, all the same suit |

## Special / Secret Hand Requirements

These hands require five cards of the same rank, which is impossible with a single 52-card deck. They are enabled by **rank duplication** (Wild cards counting as any suit, copied ranks, multiple decks/duplicates, or jokers/enhancements that create copies).

| Hand | Requirement | How it becomes possible |
|------|-------------|--------------------------|
| **Five of a Kind** | Five cards of the **same rank** (suits may differ) | Added rank copies (e.g., duplicated cards from Death/Hanged Man tarot edits, multiple copies of a rank in the deck) |
| **Flush House** | A Full House (three of a kind + a pair) where **all five cards share one suit** | Same-suit Full House; Wild cards (count as any suit) make this far easier |
| **Flush Five** | Five cards of the **same rank AND the same suit** | Five identical cards — needs both rank duplication and same suit (Wild cards help by counting as the needed suit) |

Hand ranking among the specials: **Five of a Kind < Flush House < Flush Five**. Each is detected only if it actually applies; e.g., five same-rank cards that also share a suit score as **Flush Five** (the higher tier), not Five of a Kind.

## How a Hand Is Chosen

Balatro always scores the **highest-ranking** poker hand contained in the played cards. Playing five cards that form a Flush House will score as Flush House, not as the underlying Full House or Flush. Only the cards that are part of that recognized hand score by default (see `02-scoring-system.md` for which cards score).

## Hand-Level Scaling Math

Each Planet card raises the associated hand's level by 1, adding the per-level Chips and Mult to its base. The growth is **linear in each factor**, which makes the base **product** grow quadratically.

```
base Chips at level L = baseChips(1) + (L − 1) × perLevelChips
base Mult  at level L = baseMult(1)  + (L − 1) × perLevelMult
base product = base Chips × base Mult
```

### Worked example — Flush (35 × 4 at L1; +15 Chips, +2 Mult per level)

| Level | Base Chips | Base Mult | Base product |
|-------|-----------|-----------|--------------|
| 1 | 35 | 4 | 140 |
| 2 | 50 | 6 | 300 |
| 5 | 95 | 12 | 1,140 |
| 10 | 185 | 22 | 4,070 |

So a Flush leveled to 5 (`Jupiter` ×4) has a base of 95 × 12 = 1,140 **before** any card chips, enhancements, or jokers are added.

### Worked example — Four of a Kind (60 × 7 at L1; +30 Chips, +3 Mult per level)

| Level | Base Chips | Base Mult | Base product |
|-------|-----------|-----------|--------------|
| 1 | 60 | 7 | 420 |
| 5 | 180 | 19 | 3,420 |
| 10 | 330 | 34 | 11,220 |

### Reference: special hands at higher levels

| Hand | L1 product | L5 product | L10 product |
|------|-----------|-----------|-------------|
| Five of a Kind | 120 × 12 = 1,440 | 260 × 24 = 6,240 | 435 × 39 = 16,965 |
| Flush House | 140 × 14 = 1,960 | 300 × 30 = 9,000 | 500 × 50 = 25,000 |
| Flush Five | 160 × 16 = 2,560 | 360 × 28 = 10,080 | 610 × 43 = 26,230 |

(Per-level increments applied: Five of a Kind +35/+3, Flush House +40/+4, Flush Five +50/+3.)

## See also

- `02-scoring-system.md` — full scoring sequence, card chip values, +Mult vs ×Mult
- `07-planet-cards.md` — Planet cards that level each hand
- `04-enhancements-editions-seals.md` — Wild cards and other enablers of special hands
- `05-jokers.md` — Four Fingers, Shortcut, Splash and other hand-shaping jokers
