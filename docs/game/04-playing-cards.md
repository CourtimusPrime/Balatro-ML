# Playing Cards

The standard 52-card playing-card system and every modifier a card can carry: ranks, suits, enhancements, editions, and seals.

> As of: Balatro v1.0 (base game, ~1.0.1n/1.0.1o)

A playing card is the fundamental scoring unit. When a card is "scored" (part of a played hand that contributes to the poker hand, or otherwise triggered), it contributes its **base chip value** (from its rank) plus any modifier effects. Cards held in hand at end of round and certain in-hand effects (Steel, Gold, Blue Seal) trigger separately.

## Ranks and base chip value

There are 13 ranks. A scored card always contributes chips equal to its rank value (before any enhancement/edition/seal). Mult is contributed only by modifiers, not by base rank.

| Rank | Base chips | Notes |
|------|-----------|-------|
| 2 | 2 | |
| 3 | 3 | |
| 4 | 4 | |
| 5 | 5 | |
| 6 | 6 | |
| 7 | 7 | |
| 8 | 8 | |
| 9 | 9 | |
| 10 | 10 | |
| Jack (J) | 10 | Face card |
| Queen (Q) | 10 | Face card |
| King (K) | 10 | Face card |
| Ace (A) | 11 | Highest for straights; also wraps low in A-2-3-4-5 |

- **Face cards** = J, Q, K (relevant for jokers such as Scary Face, Photograph, Smiley Face, Business Card, and Sock and Buskin).
- **Number/numbered cards** = 2–10.
- For straights, Ace can be high (10-J-Q-K-A) or low (A-2-3-4-5). It is **not** both at once (no K-A-2 wraparound by default).
- A card's chip contribution can be altered by enhancements (Stone replaces rank chips; Bonus adds chips) and by Foil edition.

## Suits

There are 4 suits, 13 cards each in a fresh deck.

| Suit | Color | Symbol |
|------|-------|--------|
| Hearts | Red | ♥ |
| Diamonds | Red | ♦ |
| Clubs | Black | ♣ |
| Spades | Black | ♠ |

- **Red suits** = Hearts + Diamonds. **Black suits** = Clubs + Spades. Color grouping matters for some jokers (e.g., suit-specific jokers, and the Wild card which counts as all suits).
- Some jokers reward a specific suit (Greedy/Lusty/Wrathful/Gluttonous Joker → Diamonds/Hearts/Spades/Clubs respectively; Arrowhead → Spades; Onyx Agate → Clubs; Rough Gem → Diamonds; Bloodstone → Hearts).
- **Wild** enhancement and **Smeared Joker** (treats Hearts/Diamonds as one suit and Clubs/Spades as one suit) modify suit matching.

## Enhancements

A card may carry **at most one** enhancement. An enhancement changes how the card scores or behaves. Applied via Tarot cards (e.g., The Magician, The Empress, The Hierophant, The Hermit) and certain Spectral cards / jokers.

| Enhancement | Effect | Exact value | When it triggers |
|-------------|--------|-------------|------------------|
| **Bonus** | Extra chips | **+30 Chips** (additive) | When scored |
| **Mult** | Extra mult | **+4 Mult** (additive, `+`) | When scored |
| **Wild** | Counts as **all four suits** simultaneously | — (still keeps its rank & base chips) | Passive (suit matching) |
| **Glass** | Multiplicative mult, but fragile | **X2 Mult** (`x`); **1 in 4** chance to destroy the card after all scoring finishes | Xmult when scored; destroy check post-scoring |
| **Steel** | Multiplicative mult while in hand | **X1.5 Mult** (`x`) | While **held in hand** (not when played/scored) |
| **Stone** | Pure chips, no rank/suit | **+50 Chips**; has **no rank and no suit**; **always scores** (counts even if not part of the poker hand) | Always when in the played hand |
| **Gold** | Money if retained | **+$3** if held in hand at **end of round** | End of round, while held in hand |
| **Lucky** | Random bonus on score | **1 in 5** chance: **+20 Mult** (additive); **1 in 15** chance: **+$20**. Rolls are independent and can both hit. Avg ≈ +4 Mult and +$1.33 per trigger | When scored |

Notes:
- **Stone** cards lose rank and suit entirely: they cannot form pairs/straights/flushes by rank or suit and are not affected by rank/suit jokers, but they always add their +50 chips when in the played hand.
- **Glass** destroy chance and **Lucky** odds are affected by probability-modifying jokers (e.g., **Oops! All 6s** doubles all listed probabilities — Glass becomes 2-in-4 destroy, Lucky becomes 2-in-5 / 2-in-15).
- **Steel** and **Gold** are "held in hand" effects — they do nothing when the card is played; they reward keeping the card in hand.
- An enhancement **replaces** any previous enhancement (only one at a time); editions and seals are independent and persist.

## Editions

A card may carry **at most one** edition. Editions also apply to **Jokers** (with slightly different timing) and, for Negative, to consumables. Applied to playing cards via The Aura (Spectral), Hone/Glow Up (Spectral, multiple), shop, or jokers.

| Edition | On playing cards | On Jokers | Notes |
|---------|------------------|-----------|-------|
| **Foil** | **+50 Chips** when scored (additive) | +50 Chips (added to its scoring contribution) | Chips |
| **Holographic** | **+10 Mult** when scored (additive, `+`) | +10 Mult | Additive mult |
| **Polychrome** | **X1.5 Mult** when scored (`x`) | X1.5 Mult (applied after the joker's other effects) | Multiplicative mult |
| **Negative** | **Does NOT apply to playing cards** ⚠️ | **+1 Joker slot** | On consumables: **+1 Consumable slot**. This is the only edition that cannot be put on playing cards. |

Notes:
- On playing cards, only **Foil, Holographic, Polychrome** are possible. **Negative** can only be on Jokers (+1 joker slot) or consumables (+1 consumable slot).
- Edition mult/chips stack with the card's enhancement: a card can be e.g. Glass (X2) **and** Polychrome (X1.5), multiplying both into the hand's mult.
- For Jokers, Polychrome's X1.5 is applied after the Joker's own contribution; ordering matters for sequencing.

## Seals

A card may carry **at most one** seal. Seals are independent of enhancement and edition. Applied via Tarot cards (e.g., The Sun/Moon/Star/World for suits is unrelated; seals come from cards like the seal-granting Tarots), the Spectral card **Talisman** (Gold Seal), and certain jokers.

| Seal | Effect | Exact value | Trigger |
|------|--------|-------------|---------|
| **Red Seal** | **Retriggers** this card **1 time** (it scores twice). Also retriggers its in-hand abilities (e.g., a Red Seal Steel card triggers its X1.5 twice while held). | 1 extra trigger | On score / on in-hand evaluation |
| **Blue Seal** | Creates the **Planet card** corresponding to the **final played poker hand of the round**, if this card is **held in hand** at end of round (and there is consumable space) | 1 Planet card | End of round, while held in hand |
| **Gold Seal** | **+$3** when this card is **played and scores** | +$3 | When scored (on play) |
| **Purple Seal** | Creates a **Tarot card** when this card is **discarded** (if consumable space) | 1 Tarot card | On discard |

Notes:
- **Gold Seal** triggers when the card is *played and scores* — distinct from the **Gold enhancement**, which pays $3 when *held in hand* at end of round. A card can be both Gold-enhanced and Gold-Sealed (different triggers).
- **Blue Seal** keys off the *last poker hand played that round* and requires holding the card to end of round; if you never played a hand, no Planet is made.
- **Purple Seal** requires the card to be **discarded** (not played).

## Stacking rules

A single playing card can simultaneously carry **one enhancement + one edition + one seal**. These three are independent layers:

- **Enhancement** (Bonus/Mult/Wild/Glass/Steel/Stone/Gold/Lucky) — at most one; applying a new one replaces the old.
- **Edition** (Foil/Holographic/Polychrome; not Negative) — at most one; applying a new one replaces the old.
- **Seal** (Red/Blue/Gold/Purple) — at most one; applying a new one replaces the old.

All three apply together. Example: a **Glass + Polychrome + Red Seal** Ace of Hearts, when scored:
1. Contributes base chips (11 for Ace).
2. Glass applies **X2 Mult**.
3. Polychrome applies **X1.5 Mult**.
4. Red Seal **retriggers** the whole card once, so steps 1–3 happen **a second time** (chips and both Xmults again).
5. After scoring, Glass rolls its 1-in-4 destroy chance (once per actual scoring instance — Red Seal retrigger does roll again).

Stone cards are an exception in spirit: they have no rank/suit but can still carry an edition and a seal (a Stone card can be Foil, Red-Sealed, etc.).

## Retriggering

**Retrigger** = the card scores **again**, repeating its full scoring contribution (base chips, enhancement effects, edition effects, seal-on-score effects). Each retrigger is a separate scoring instance, so probabilistic effects (Lucky, Glass destroy) roll each time.

Sources of retriggering:

| Source | What it retriggers | How much |
|--------|--------------------|----------|
| **Red Seal** | The sealed card itself | 1 extra time |
| **Hack** (Joker) | Played cards that are **2, 3, 4, or 5** | 1 extra time each |
| **Dusk** (Joker) | All played cards, but only on the **final hand** of the round | 1 extra time each |
| **Hanging Chad** (Joker) | The **first** scored card of the hand | 2 extra times |
| **Mime** (Joker) | **Held-in-hand** card abilities (Steel, Gold, etc.) — not the played-hand scoring | 1 extra time |
| **Sock and Buskin** (Joker) | All scored **face cards** | 1 extra time each |
| **Seltzer** (Joker) | All scored cards, for the next 10 hands | 1 extra time each |

Notes:
- Held-in-hand retriggers (Mime, Red Seal on a held card) repeat the **in-hand** effect (Steel X1.5, Gold $3, Blue Seal Planet generation), not the played-hand scoring.
- Retriggers stack: a Red Seal card also boosted by Hack/Dusk triggers multiple extra times.

## See also

- `01-...` core scoring / chips × mult formula
- `03-...` jokers (full list and edition/sticker interactions)
- Consumables: Tarot cards (apply enhancements/seals), Planet cards (level up hands), Spectral cards (The Aura → editions, Talisman → Gold Seal)
- Probability jokers: Oops! All 6s (affects Glass, Lucky, and all "X in Y" odds)
