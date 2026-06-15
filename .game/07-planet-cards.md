# Planet Cards

Consumable cards that permanently level up a specific poker hand for the rest of the run.

> As of: v1.0 (base game, ~1.0.1n/1.0.1o)
> Total: 12 (9 standard + 3 secret)

Each Planet card corresponds to exactly one poker hand. Using a Planet card raises that hand's **level by 1**, permanently adding fixed **+Chips** and **+Mult** to the hand's *base* values for the remainder of the run. Effects are permanent and stack with every additional copy used. Levels persist across blinds/antes but reset on a new run. The general rule: the harder the hand is to make, the larger the per-level bonus.

## Standard Planet Cards (9)

| Planet | Levels which Hand | +Chips per level | +Mult per level |
|--------|-------------------|------------------|-----------------|
| Pluto | High Card | +10 | +1 |
| Mercury | Pair | +15 | +1 |
| Uranus | Two Pair | +20 | +1 |
| Venus | Three of a Kind | +20 | +2 |
| Saturn | Straight | +30 | +3 |
| Jupiter | Flush | +15 | +2 |
| Earth | Full House | +25 | +2 |
| Mars | Four of a Kind | +30 | +3 |
| Neptune | Straight Flush | +40 | +4 |

## Secret Planet Cards (3)

These only appear in the shop **after** the player has scored their corresponding (secret) poker hand at least once during the run.

| Planet | Levels which Hand | +Chips per level | +Mult per level |
|--------|-------------------|------------------|-----------------|
| Planet X | Five of a Kind | +35 | +3 |
| Ceres | Flush House | +40 | +4 |
| Eris | Flush Five | +50 | +3 |

## Mechanics notes for the agent

- **Permanent for the run:** A leveled hand keeps its bonus for every subsequent play of that hand; you do not need to re-use the Planet card each round.
- **Base values are levelled, not the final score:** The +Chips/+Mult are added to the hand's base chips and base mult *before* card chips, enhancements, and Joker multipliers are applied. (See `02-scoring-system.md` for the full scoring order.)
- **Hand level 1 is the default;** Planet cards push to level 2, 3, .... There is no in-game cap on hand level.
- **Sources of Planet cards:** shop, Celestial Packs (multiple Planets), The High Priestess Tarot (creates up to 2 random Planets), and The Fool (can copy the last Planet used). `08-spectral-cards.md` → Black Hole levels up **every** poker hand by 1 at once.
- **Telescope / Observatory (Jokers / Vouchers):** bias Celestial Pack contents toward your most-played hand and grant Xmult for your most-played hand's Planet — relevant when valuing Planet acquisition. (See Jokers/Vouchers reference if present.)

## See also
- `03-poker-hands.md` — base chips/mult per hand and which Planet levels each
- `02-scoring-system.md` — scoring order and where hand level enters the calculation
- `06-tarot-cards.md` — The High Priestess (creates Planets), The Fool (copies last Planet)
- `08-spectral-cards.md` — Black Hole (levels up all hands)
