# Scoring System

The fundamental score formula and exact evaluation sequence Balatro uses to turn a played hand into points.

> As of: Balatro v1.0 (patch 1.0.1n/1.0.1o)

## The Fundamental Formula

Every scored hand resolves to a single product:

```
score = total Chips × total Mult
```

- **Chips** are the additive component (a running sum that starts from the hand's base chips).
- **Mult** is the multiplier component (a running value that starts from the hand's base mult).
- The two are accumulated separately during scoring, then multiplied **once** at the very end.

Because the final step is a single multiplication, anything that raises Chips and anything that raises Mult are *not* interchangeable: the optimal play maximizes the **product**, which usually means balancing the two rather than dumping everything into one side.

## Scoring Sequence (exact order)

Balatro evaluates a played hand in strict phases. Within a phase, things resolve **left to right** by card/joker position. The order is fixed and deterministic.

| Phase | What happens | Affects |
|-------|--------------|---------|
| 1 | **Base hand values applied.** The game identifies the poker hand type, looks up its current level, and seeds the running Chips and Mult with that hand's base Chips and base Mult. | Chips, Mult |
| 2 | **Scored cards evaluated, left to right.** For each card that is part of the played poker hand, add its rank chip value, then apply that card's enhancement, edition, and seal effects. | Chips, Mult |
| 3 | **Held-in-hand cards evaluated, left to right.** Cards remaining in hand (not played) trigger any "while held in hand" effects (e.g., Steel card Xmult, Baron with Kings). | Mult (and Xmult) |
| 4 | **Jokers evaluated, left to right.** Each joker applies its effect in slot order. This includes +Chips, +Mult, ×Mult, retriggers, and copy effects. | Chips, Mult |
| 5 | **Final multiply.** `score = Chips × Mult`, then compared against the blind's required score. | — |

### Why joker order matters

Phases 2–4 modify a *running* Chips value and a *running* Mult value. A `+Mult` joker adds to the current Mult; a `×Mult` joker multiplies the current Mult. Because addition and multiplication do not commute, the **left-to-right position** of jokers changes the result whenever both additive and multiplicative mult are present.

**Worked example** — base hand 40 × 4, plus a `+4 Mult` joker and a `×2 Mult` joker:

| Joker arrangement | Mult evaluation | Score |
|-------------------|-----------------|-------|
| `+4 Mult` left of `×2 Mult` | `(4 + 4) × 2 = 16` | `40 × 16 = 640` |
| `×2 Mult` left of `+4 Mult` | `(4 × 2) + 4 = 12` | `40 × 12 = 480` |

So the **general optimal ordering** of jokers, left to right, is:

1. `+Chips` jokers
2. `+Mult` jokers
3. Conditional / `×Mult` jokers
4. Polychrome (`×1.5`) and other final multipliers (rightmost)

Notes on ordering:
- The relative order of multiple `+Mult` jokers among themselves does **not** matter (addition is associative/commutative).
- The relative order of multiple `×Mult` jokers among themselves does **not** matter (multiplication is associative/commutative).
- Order only matters at the **boundary** between additive and multiplicative effects — push all `×` effects to the right of all `+` effects.
- When several jokers are triggered by the *same* scored card, they still fire in left-to-right joker-slot order.

## How a Played Card Contributes

When a card scores (Phase 2), it adds its **rank chip value** first, then layers on enhancement/edition/seal effects.

### Base chip value by rank

| Rank | Base Chips |
|------|-----------|
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | 7 |
| 8 | 8 |
| 9 | 9 |
| 10 | 10 |
| Jack (J) | 10 |
| Queen (Q) | 10 |
| King (K) | 10 |
| Ace (A) | 11 |

So number cards 2–10 give their face value, all face cards (J/Q/K) give 10, and the Ace gives 11. (See `04-enhancements-editions-seals.md` for the modifiers added on top.)

### Layering on top of rank chips

After the base rank chips are added, the card's modifiers apply, generally in this internal order: enhancement → edition → seal. Examples (full values in `04-enhancements-editions-seals.md`):

- **Bonus** enhancement: `+30 Chips`
- **Mult** enhancement: `+4 Mult`
- **Glass** enhancement: `×2 Mult` (with a chance to shatter)
- **Foil** edition: `+50 Chips`
- **Holographic** edition: `+10 Mult`
- **Polychrome** edition: `×1.5 Mult`

## Which Cards "Score"

By default, **only the cards that form the played poker hand actually score.** Cards you play that are not part of the recognized hand contribute nothing on their own.

- In a **Pair**, only the two paired cards score; a third/fourth card played alongside (as kickers) does **not** add its chips.
- In **Two Pair**, the four cards in the two pairs score; a fifth card does not.
- In a **Flush**, **Straight**, **Full House**, **Straight Flush**, and the five-card special hands, all five cards score (the whole hand is used).
- In **High Card**, only the single highest card scores.

This is why "all 5 cards score" hands (Flush, Straight, Full House, etc.) generally rack up more chips than a bare Pair — more cards contribute their rank chips and their per-card modifiers.

### Scored vs held-in-hand effects

- **Scored effects** (Phase 2) trigger only when the card is part of the played hand. Most enhancements (Bonus, Mult, Glass, Lucky, etc.) only fire when the card scores.
- **Held-in-hand effects** (Phase 3) trigger from cards left in your hand, *not* played. The **Steel** enhancement (`×1.5 Mult`) and certain jokers (e.g., Baron, Mime) operate on held cards.
- A card can be made to count in both ways or to retrigger via jokers (e.g., Hack, Sock and Buskin, Mime, Dusk) — retriggers re-run the card's scoring effects.

Some jokers also let normally-non-scoring cards score (e.g., **Splash** makes *every* played card score regardless of whether it's part of the poker hand).

## Hand Levels (Planet Cards)

Each poker-hand type has a **level**, starting at Level 1. Playing a **Planet card** raises the level of its associated hand by 1 (see `07-planet-cards.md`). Leveling is **additive and permanent for the run**.

Each level adds a fixed amount of **base Chips** and **base Mult** to that hand type (the per-level increments differ per hand — see `03-poker-hands.md`). The bonus is applied to the *base* values in Phase 1, before any cards or jokers are scored.

```
hand base Chips at level L = base_chips(1) + (L − 1) × per_level_chips
hand base Mult  at level L = base_mult(1)  + (L − 1) × per_level_mult
```

**Worked example** — Full House (base 40 × 4 at Level 1; +25 Chips, +2 Mult per level):

| Level | Base Chips | Base Mult | Base product |
|-------|-----------|-----------|--------------|
| 1 | 40 | 4 | 160 |
| 2 | 65 | 6 | 390 |
| 5 | 140 | 12 | 1,680 |
| 10 | 265 | 22 | 5,830 |

Leveling raises both factors, so the base product grows roughly quadratically with level even before cards and jokers are added.

## Additive Mult vs Multiplicative Mult ("+" vs "×")

This distinction is the single most important scoring concept.

- **`+Mult`** adds to the running Mult value. Sources: Mult enhancement (+4), Holographic edition (+10), most "+Mult" jokers.
- **`×Mult` (Xmult)`** multiplies the running Mult value. Sources: Glass card (×2), Polychrome edition (×1.5), Steel card (×1.5, held), and many powerful jokers.

Because Phase 4 walks the joker row left to right, an `×Mult` applied **after** all `+Mult` multiplies the *entire accumulated* additive mult — which is strictly better (by the distributive law) than applying it earlier. Always arrange so additive mult is fully built up before any multiplier hits.

Chips have no multiplicative analog in the base game's hand modifiers in the same row — chip multipliers are rare (e.g., the Hiker joker permanently grows card chips; some jokers convert). In practice the `+`/`×` ordering concern is about the **Mult** track.

## Rounding and the Score Cap

- **Rounding:** the final score is **floored to an integer** (truncated down) before being compared to the blind requirement. Internally Chips and Mult can be fractional (e.g., a `×1.5` on an odd Mult), but the displayed/compared score drops the fractional part.
- **Large numbers / display:** once scores exceed what fits in plain notation, Balatro switches to **scientific / abbreviated notation** (e.g., `1.798e10`, then named magnitudes). Internally scores are 64-bit doubles.
- **The "naneinf" cap:** the maximum representable score is the IEEE-754 double-precision max, **≈ 1.7977e308**. Beyond this the value becomes `inf` (the community "naneinf" ceiling). This is effectively unreachable in fair play but matters for extreme joker-synergy runs and for any ML reward that uses raw (un-log-transformed) scores — clamp or log-transform to avoid `inf`/`NaN` propagation.

## See also

- `03-poker-hands.md` — base Chips/Mult and per-level increments for every hand
- `04-enhancements-editions-seals.md` — exact card modifier values
- `07-planet-cards.md` — which Planet card levels which hand
- `05-jokers.md` — joker effects and ordering interactions
