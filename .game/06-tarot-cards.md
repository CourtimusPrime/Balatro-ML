# Tarot Cards

Consumable cards (named after the 22 Major Arcana) that enhance/convert playing cards or generate money, cards, and resources.

> As of: v1.0 (base game, ~1.0.1n/1.0.1o)
> Total: 22

Tarot cards are consumables that occupy consumable slots (default 2). Cards that "select" require you to highlight cards in your hand first; cards that "create" require a free consumable/Joker slot. The base appearance weight in shops/packs is 25.5% (most common consumable type).

## All Tarot Cards

| Name | Effect (exact) |
|------|----------------|
| The Fool | Creates the last Tarot or Planet card used during this run (The Fool itself cannot be created/copied) |
| The Magician | Enhances up to 2 selected cards to **Lucky** Cards |
| The High Priestess | Creates up to 2 random **Planet** cards (Must have room) |
| The Empress | Enhances up to 2 selected cards to **Mult** Cards |
| The Emperor | Creates up to 2 random **Tarot** cards (Must have room) |
| The Hierophant | Enhances up to 2 selected cards to **Bonus** Cards |
| The Lovers | Enhances 1 selected card into a **Wild** Card |
| The Chariot | Enhances 1 selected card into a **Steel** Card |
| Justice | Enhances 1 selected card into a **Glass** Card |
| The Hermit | Doubles money (Max of $20 gained) |
| The Wheel of Fortune | 1 in 4 chance to add Foil, Holographic, or Polychrome edition to a random Joker |
| Strength | Increases rank of up to 2 selected cards by 1 (wraps Ace→2... King→Ace) |
| The Hanged Man | Destroys up to 2 selected cards |
| Death | Select 2 cards, convert the left card into the right card (drag to rearrange selection order) |
| Temperance | Gives the total sell value of all current Jokers (Max of $50) |
| The Devil | Enhances 1 selected card into a **Gold** Card |
| The Tower | Enhances 1 selected card into a **Stone** Card |
| The Star | Converts up to 3 selected cards to **Diamonds** |
| The Moon | Converts up to 3 selected cards to **Clubs** |
| The Sun | Converts up to 3 selected cards to **Hearts** |
| Judgement | Creates a random **Joker** card (Must have room) |
| The World | Converts up to 3 selected cards to **Spades** |

## Targeting / cap summary

- **Enhance 1 card:** The Lovers, The Chariot, Justice, The Devil, The Tower.
- **Enhance up to 2 cards:** The Magician, The Empress, The Hierophant.
- **Convert suit, up to 3 cards:** The Sun (Hearts), The Moon (Clubs), The Star (Diamonds), The World (Spades).
- **Rank/structure edits:** Strength (+1 rank to up to 2), Death (copy left→right, 2 selected), The Hanged Man (destroy up to 2).
- **Create cards (need room):** The High Priestess (2 Planets), The Emperor (2 Tarots), Judgement (1 Joker), The Fool (copies last Tarot/Planet used).
- **Money:** The Hermit (double money, cap +$20), Temperance (sum of Joker sell values, cap +$50).
- **Joker edition:** The Wheel of Fortune (25% chance: Foil/Holo/Poly to a random Joker).

### Notes for the agent
- A card can only hold one enhancement at a time; re-enhancing overwrites the previous enhancement (seals and editions are separate layers and are preserved).
- "Up to N" means the effect applies to however many eligible cards are selected, capped at N. Selecting fewer wastes none of the cap but applies to fewer cards.
- The Wheel of Fortune is a gamble: it does nothing 75% of the time and there is no consolation effect.

## See also
- `02-scoring-system.md` — how enhancements (Lucky, Mult, Bonus, Steel, Glass, Gold, Stone, Wild) affect scoring
- `04-card-enhancements.md` (enhancements, editions, seals) if present
- `07-planet-cards.md` — Planet cards created by The High Priestess / copied by The Fool
- `08-spectral-cards.md` — related consumable type
