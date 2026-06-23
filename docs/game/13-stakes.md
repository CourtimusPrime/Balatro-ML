# Stakes

The 8 difficulty tiers (Stakes) in Balatro. Each stake is **cumulative**: it adds its own modifier on top of every lower stake's modifier.

> As of: v1.0.1 (base game, ~1.0.1n/1.0.1o). Confirmed count: 8 stakes.

## How stakes work

- Stakes set the difficulty of a run and are chosen per deck on the deck-select screen.
- **Cumulative stacking**: a stake includes all modifiers from every stake below it. For example, Gold Stake (the hardest) carries White + Red + Green + Black + Blue + Purple + Orange modifiers as well as its own.
- **Unlock chain**: completing (winning) a run on a given stake **with a particular deck** unlocks the next stake *for that deck*. (Stake progress is tracked per deck; the colored stake "chips" on the deck-select screen show how far each deck has progressed.)
- Several decks unlock by winning a run on a stake of a given tier or higher, regardless of deck (see `12-decks.md`).

## All 8 Stakes (White → Gold)

| # | Stake | Color | New modifier added (on top of all lower stakes) |
|---|-------|-------|--------------------------------------------------|
| 1 | White Stake | White | Base difficulty — no added modifier |
| 2 | Red Stake | Red | **Small Blind gives no reward money** ($0 from a defeated Small Blind) |
| 3 | Green Stake | Green | **Required score scales faster** for each Ante |
| 4 | Black Stake | Black | **Eternal Jokers may appear** in the shop (30% chance of an Eternal sticker on shop/pack Jokers) |
| 5 | Blue Stake | Blue | **-1 Discard** every round |
| 6 | Purple Stake | Purple | **Required score scales even faster** for each Ante (a second, steeper ante-scaling bump on top of Green's) |
| 7 | Orange Stake | Orange | **Perishable Jokers may appear** (30% chance of a Perishable sticker on shop/pack Jokers) |
| 8 | Gold Stake | Gold | **Rental Jokers may appear** (30% chance of a Rental sticker on shop/pack Jokers) |

### Cumulative summary (what is active at each stake)

| Stake | Active modifiers (this stake + all below) |
|-------|-------------------------------------------|
| White | (base) |
| Red | Small Blind: no reward |
| Green | + faster ante-score scaling |
| Black | + Eternal Jokers may appear |
| Blue | + -1 Discard |
| Purple | + even faster ante-score scaling |
| Orange | + Perishable Jokers may appear |
| Gold | + Rental Jokers may appear |

## Joker stickers introduced by stakes

Stakes from Black upward introduce **Joker stickers** — modifiers attached to Jokers found in shops and booster packs. From the introducing stake onward, each affected Joker rolls roughly a **30% chance** to carry the relevant sticker.

| Sticker | Introduced at | Effect |
|---------|---------------|--------|
| **Eternal** | Black Stake | The Joker **cannot be sold or destroyed**. It is locked in your Joker slots for the rest of the run. |
| **Perishable** | Orange Stake | The Joker becomes **debuffed (disabled) after 5 rounds**. A countdown shows the remaining rounds; once it expires the Joker does nothing (but still occupies a slot). |
| **Rental** | Gold Stake | The Joker **costs $3 at the end of each round** to keep. It is also cheaper to buy (reduced shop cost, commonly $1). If you can't pay, it is lost. |

Notes on stickers:
- Stickers stack with the cumulative stake rule: at Gold Stake all three sticker types can roll on Jokers (a single Joker may carry more than one sticker, e.g. Eternal + Rental).
- Eternal removes the ability to sell a Joker for money or to remove an unwanted/debuffed Joker, which constrains build flexibility on Black Stake and higher.
- Perishable's debuff is permanent once it triggers; planning around the 5-round window matters from Orange Stake on.
- Rental imposes a recurring economic drain, making the Gold Stake economy noticeably tighter (compounded with Red Stake's loss of Small Blind reward).

⚠️ The exact sticker chance (~30%) and the precise in-game tooltip wording can vary slightly by patch; the modifiers, order, and cumulative behavior above are cross-checked across the community wiki and multiple guides for base-game v1.0.x.

## See also

- `12-decks.md` — the 15 decks (several unlock by winning runs on specific stake tiers)
