# Balatro ML

A reinforcement-learning agent for maximizing scores across all decks in Balatro.

## Installation

### 1. Mise

```zsh
curl https://mise.run/zsh | sh
```

Add this to the end of your `~/.zshrc` file:

```zsh
eval "$(mise activate bash)"
```

---

## Design

### Principles

- All card and joker properties are surfaced as flat integer or boolean fields for direct tensorisation
- Each card becomes a 7-element vector `[suit, value, enhancement, edition, seal, debuffed, selected]`
- Each joker becomes an 8-element vector `[id, edition, eternal, perishable, rental, sell_value, counter, target_id]`
- Variable-length arrays (hand, deck, jokers, consumables, shop items) are handled via attention masking in the transformer policy
- Game state scalars are concatenated as a fixed-length context vector
- The full observation is a dictionary of these components, populated differently depending on game phase (playing vs. shop)

### Phase Notes

The observation is fully populated during the **playing phase** (selecting and playing/discarding cards). During the **shop phase**, `hand` and `deck` reflect end-of-round state, `hands_remaining` and `discards_remaining` are 0, and `shop.items` is populated. The policy network uses a shared backbone with separate heads for each phase.

---

## Observation Schema

### Schemas

#### Card

Used in both `hand` and `deck` arrays.

```python
CARD = {
  "suit":         int,   # 0=none (stone card), 1=spade, 2=club, 3=heart, 4=diamond
  "value":        int,   # 0=none (stone card), 2–13=standard, 14=ace
                         # note: ace encoded as 14; agent must learn ace-low straights
  "enhancement":  int,   # 0=none,  1=bonus,  2=mult,   3=wild,  4=glass,
                         # 5=steel, 6=stone,  7=gold,   8=lucky
  "edition":      int,   # 0=none, 1=foil, 2=holo, 3=poly
  "seal":         int,   # 0=none, 1=gold, 2=red, 3=blue, 4=purple
  "debuffed":     bool,  # True if boss blind has disabled this card's effects
  "selected":     bool,  # True if currently selected; always False for deck cards
}
```

**Special cases:**

- Stone cards: `suit=0, value=0, enhancement=6` — rank and suit are meaningless
- Wild cards: `suit` reflects the card's native suit; wildness is encoded in `enhancement=3`
- Debuffed wild cards revert to native suit for hand evaluation purposes
- Debuffed cards retain all fields but all effects (enhancement, edition, seal) are disabled

#### Joker

```python
JOKER = {
  "id":           int,   # unique joker identifier, 0-indexed from a fixed lookup table
                         # the agent learns an embedding per ID through experience
  "edition":      int,   # 0=none, 1=foil, 2=holo, 3=poly, 4=negative
  "eternal":      bool,  # True if joker cannot be sold
  "perishable":   bool,  # True if joker loses its retrigger after 5 antes
  "rental":       bool,  # True if joker costs $1 per round to keep
  "sell_value":   int,   # current sell value in dollars
  "counter":      float, # current value of any scaling accumulator (0.0 if unused)
                         # covers: Ride the Bus streak, Fibonacci mult, Green Joker
                         # hand count, Supernova hand count, etc.
  "target_id":    int,   # ID of the joker being copied by Blueprint or Brainstorm
                         # -1 if this joker does not copy another
}
```

**Notes:**

- Joker order in the array is meaningful — Blueprint copies the joker immediately to its right, Brainstorm copies the leftmost joker
- Maximum 5 joker slots by default; expandable via certain vouchers
- Negative edition jokers add +1 joker slot and are therefore not counted against the slot limit in the same way

#### Consumable

```python
CONSUMABLE = {
  "id":     int,  # maps to appropriate lookup table per type
  "type":   int,  # 0=tarot, 1=planet, 2=spectral
}
```

**Notes:**

- Maximum 2 consumable slots by default; expandable via Hieroglyph/Observatory vouchers
- Consumables can be used during the playing phase on certain game states
- Planet cards level up a specific hand type when used
- Tarot cards apply enhancements, seals, or other effects to selected cards

#### Shop Item

```python
SHOP_ITEM = {
  "type":         int,   # 0=joker, 1=tarot, 2=planet, 3=spectral,
                         # 4=playing_card, 5=voucher, 6=booster_pack
  "id":           int,   # maps to the appropriate lookup table for the given type
  "cost":         int,   # current price in dollars (may be reduced by vouchers)
  "edition":      int,   # edition for jokers and playing cards; 0 for others
  "enhancement":  int,   # enhancement for playing cards only; 0 for others
  "seal":         int,   # seal for playing cards only; 0 for others
}
```

### Full Observation

```python
observation = {

  # --- Cards ---

  "hand": [CARD, ...],
  # Cards currently drawn and available to play or discard.
  # Variable length, up to hand_size (default 8, modified by some jokers/vouchers).

  "deck": [CARD, ...],
  # Cards remaining in the deck (not yet drawn this round).
  # Variable length, shrinks as cards are removed from the run.
  # Does NOT include cards currently in hand or the discard pile.

  # --- Jokers ---

  "jokers": [JOKER, ...],
  # Active jokers in slot order. Position is strategic — do not shuffle.
  # Variable length, up to joker_slots (default 5).

  # --- Consumables ---

  "consumables": [CONSUMABLE, ...],
  # Tarot, planet, and spectral cards currently held.
  # Variable length, up to consumable slots (default 2).

  # --- Shop (populated during shop phase; empty arrays during playing phase) ---

  "shop": {
    "items":        [SHOP_ITEM, ...],  # currently available items for purchase
    "reroll_cost":  int,               # current cost to reroll the shop in dollars
  },

  # --- Game State ---

  "game_state": {
    "ante":               int,   # current ante number (1–8)
    "blind":              int,   # 0=small blind, 1=big blind, 2=boss blind
    "blind_type":         int,   # which boss blind is active (0 if not boss blind)
                                 # maps to a fixed lookup table of boss blind IDs
    "chips_needed":       int,   # score required to beat the current blind
    "chips_scored":       int,   # chips scored so far this round
    "hands_remaining":    int,   # play actions remaining this round
    "discards_remaining": int,   # discard actions remaining this round
    "money":              int,   # current dollars available
    "hand_size":          int,   # maximum cards drawn per round
    "joker_slots":        int,   # maximum joker capacity
    "consumable_slots":   int,   # maximum consumable capacity
    "hand_levels": {
      0:  int,   # High Card level
      1:  int,   # One Pair level
      2:  int,   # Two Pair level
      3:  int,   # Three of a Kind level
      4:  int,   # Straight level
      5:  int,   # Flush level
      6:  int,   # Full House level
      7:  int,   # Four of a Kind level
      8:  int,   # Straight Flush level
      9:  int,   # Royal Flush level
      10: int,   # Five of a Kind level
      11: int,   # Flush House level
      12: int,   # Flush Five level
    },
    # Hand levels determine base chips and mult for each hand type.
    # Levelled up by playing that hand type or using the corresponding planet card.
    # Critical for score maximisation — a level 10 flush scores orders of magnitude
    # more than a level 1 flush.
  },

}
```

### Tensor Representation

When converting the observation to tensors for the policy network:

| Component            | Shape    | Notes                                      |
| -------------------- | -------- | ------------------------------------------ |
| `hand`               | `(H, 7)` | H = current hand size (≤ hand_size)        |
| `deck`               | `(D, 7)` | D = remaining deck size (variable)         |
| `jokers`             | `(J, 8)` | J = active joker count (≤ joker_slots)     |
| `consumables`        | `(C, 2)` | C = held consumables (≤ consumable_slots)  |
| `shop.items`         | `(S, 6)` | S = items in shop (0 during playing phase) |
| `game_state` scalars | `(26,)`  | flattened fixed-length vector              |

Variable-length arrays are padded to their maximum size and masked in the transformer attention layers so padding tokens do not contribute to attention weights.

### Lookup Tables

The following entity types are referenced by integer ID and require fixed lookup tables defined separately:

- **Joker IDs** — all 150+ base game jokers, 0-indexed
- **Boss blind types** — all boss blind variants
- **Tarot IDs** — all 22 tarot cards
- **Planet IDs** — all 13 planet cards (one per hand type)
- **Spectral IDs** — all spectral cards
- **Voucher IDs** — all vouchers

These lookup tables also serve as the embedding index for the transformer's entity embedding layers.
