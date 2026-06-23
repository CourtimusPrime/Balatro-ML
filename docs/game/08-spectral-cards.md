# Spectral Cards

Powerful, often high-risk consumables that manipulate cards, Jokers, seals, and editions — usually with a meaningful cost.

> As of: v1.0 (base game, ~1.0.1n/1.0.1o)
> Total: 18

Spectral cards occupy consumable slots (default 2). They do **not** normally appear in the standard shop; they come from Spectral/Arcana Packs, the Ghost Deck, and certain vouchers/jokers. Many trade a strong benefit for destruction of cards/Jokers, loss of money, or reduced hand size. The Soul and Black Hole are special "legendary" spectrals that can appear inside any Arcana or Spectral pack.

## All Spectral Cards

| Name | Effect (exact) | Notable risk / cost |
|------|----------------|---------------------|
| Familiar | Destroy 1 random card in your hand, add 3 random **Enhanced face cards** (J/Q/K) to your hand | Destroys 1 random card; new cards added to current hand |
| Grim | Destroy 1 random card in your hand, add 2 random **Enhanced Aces** to your hand | Destroys 1 random card |
| Incantation | Destroy 1 random card in your hand, add 4 random **Enhanced numbered cards** (2–10) to your hand | Destroys 1 random card |
| Talisman | Add a **Gold Seal** to 1 selected card | None (requires a selected card) |
| Aura | Add **Foil, Holographic, or Polychrome** edition to 1 selected card in hand | Edition type is random |
| Wraith | Creates a random **Rare Joker** (Must have room), then sets money to **$0** | Wipes all your money to $0 |
| Sigil | Converts all cards in hand to a single **random suit** | Suit is random; no hand-size penalty |
| Ouija | Converts all cards in hand to a single **random rank**, then **−1 hand size** (permanent) | Permanent −1 hand size; rank is random |
| Ectoplasm | Add **Negative** edition to a random Joker, then **−1 hand size** | Permanent −1 hand size; penalty grows each repeated use this run |
| Immolate | Destroys **5 random cards** in hand, gain **$20** | Destroys 5 cards from your deck |
| Ankh | Create a copy of a random Joker, then **destroy all other Jokers** (copy loses Negative edition) | Destroys every other Joker you hold |
| Deja Vu | Add a **Red Seal** to 1 selected card | None (requires a selected card) |
| Hex | Add **Polychrome** to a random Joker, then **destroy all other Jokers** | Destroys every other Joker you hold |
| Trance | Add a **Blue Seal** to 1 selected card | None (requires a selected card) |
| Medium | Add a **Purple Seal** to 1 selected card | None (requires a selected card) |
| Cryptid | Create **2 copies** of 1 selected card in your hand | Copies have no edition/seal |
| The Soul | Creates a **Legendary Joker** (Must have room) | Can appear in Arcana or Spectral packs |
| Black Hole | Upgrade **every** poker hand by 1 level | Can appear in Arcana or Spectral packs |

## Risk groupings for the agent

- **Destroy cards from deck:** Familiar (−1), Grim (−1), Incantation (−1), Immolate (−5).
- **Add cards to hand:** Familiar (+3 enhanced faces), Grim (+2 enhanced Aces), Incantation (+4 enhanced numbers), Cryptid (+2 copies of a selected card).
- **Permanent hand-size reduction:** Ouija (−1), Ectoplasm (−1, escalating). These are irreversible for the run.
- **Money swing:** Wraith (sets money to $0), Immolate (+$20).
- **Joker destruction (keep only one):** Ankh (copy one, destroy the rest), Hex (Polychrome one, destroy the rest).
- **Joker creation:** Wraith (Rare), The Soul (Legendary), Ankh (copy).
- **Seals (add to 1 selected card):** Talisman (Gold), Deja Vu (Red), Trance (Blue), Medium (Purple).
- **Editions:** Aura (random Foil/Holo/Poly to a playing card), Ectoplasm (Negative to a Joker), Hex (Polychrome to a Joker), The Wheel of Fortune is a *Tarot*, not here.
- **Mass upgrade:** Black Hole (+1 level to all poker hands).

### Caution flags
- **Ankh / Hex** with a single Joker held will simply copy/enhance it (no other Jokers to destroy) — safe in that case, devastating otherwise.
- **Ectoplasm** stacks a growing hand-size penalty each time it is used in a run, even though the displayed text reads "−1 hand size".
- **Wraith** requires an open Joker slot; if Joker slots are full it will not create the Rare Joker but the money-to-$0 cost still applies — avoid when slots are full.
- **Sigil vs Ouija:** Sigil (suit) has no penalty; Ouija (rank) permanently costs −1 hand size. Neither can be used when hand size is 1. Larger hand size amplifies both effects.

## See also
- `06-tarot-cards.md` — related consumable type; enhancement/seal definitions
- `07-planet-cards.md` — Black Hole and Planet cards both level poker hands
- `02-scoring-system.md` — how enhancements, editions, and seals contribute to score
- Jokers reference (Rare/Legendary tiers created by Wraith / The Soul) if present
