# Jokers

Complete reference for every base-game Balatro joker: rarity, shop cost, exact effect (additive +Mult vs multiplicative Xmult vs Chips), and unlock requirement.

> As of: v1.0.1o-FULL (released base game, ~1.0.1n/1.0.1o)
> Total jokers: 150 (Common 61, Uncommon 64, Rare 20, Legendary 5)

Jokers are the primary engine of scoring. They sit in joker slots and apply their effects during scoring, in left-to-right order. Of the 150 base jokers, 105 are available from the start and 45 are unlocked by meeting specific conditions.

---

## Joker mechanics

### Rarity & appearance rates
When a joker is generated at random (shop, packs, certain effects), the rarity roll is:
- **Common** — 70% chance
- **Uncommon** — 25% chance
- **Rare** — 5% chance
- **Legendary** — 0% from random generation. Legendary jokers appear ONLY from **The Soul** spectral card.

Rarity is color-coded in game: Common (blue tag), Uncommon (green), Rare (red), Legendary (orange/special).

### Slots
- Default joker limit is **5 slots**. The 5-slot cap can be raised (e.g., Negative-edition jokers add a slot without consuming one) or lowered by certain effects.
- Jokers held beyond capacity cannot be acquired; you must sell or skip.

### Selling value
- A joker's sell value is roughly **floor(cost / 2)**, minimum $1, and increases as some jokers gain value (e.g., Egg, gift effects). Selling is a strategic action — several jokers (Swashbuckler, Ceremonial Dagger, Invisible Joker, Luchador, Diet Cola) interact with sell value or the act of selling.

### Editions (apply to jokers)
Editions modify a joker on top of its base effect:
- **Foil** — +50 Chips
- **Holographic (Holo)** — +10 Mult (additive +Mult)
- **Polychrome (Poly)** — X1.5 Mult (multiplicative Xmult)
- **Negative** — does NOT add to the score directly; instead it does not consume a joker slot (effectively +1 slot). Highly valuable.

### Order matters
Jokers are evaluated **left to right** during scoring. Order is critical: additive +Mult should generally resolve before Xmult, and copy jokers depend on position. Examples:
- **Blueprint** copies the joker **to its right**; **Brainstorm** copies the **leftmost** joker.
- Stack all +Chips and +Mult jokers to the LEFT of your Xmult jokers so the multiplier applies to the largest possible additive base.
- Retrigger jokers (Mime, Sock and Buskin, Hack, Dusk, Seltzer, Hanging Chad) and probability/economy jokers can be order-sensitive too.

### Static vs scaling
- **Static** jokers give a fixed effect every time (e.g., Joker +4 Mult).
- **Scaling** jokers grow during a run (e.g., Ride the Bus, Green Joker, Constellation, Hologram, Campfire, Obelisk, Vampire, Canio, Yorick). These are tagged **[scaling]** below. Scaling jokers are the backbone of high-score builds because their effect compounds across a run.

---

## Common jokers (61)

70% of random rarity rolls. Cheapest tier; the additive +Mult and +Chips backbone of early game.

| Name | Cost | Effect (exact values) | Unlock requirement |
|------|------|----------------------|--------------------|
| Joker | $2 | +4 Mult | Available from start |
| Greedy Joker | $5 | Played Diamond cards: +3 Mult when scored | Available from start |
| Lusty Joker | $5 | Played Heart cards: +3 Mult when scored | Available from start |
| Wrathful Joker | $5 | Played Spade cards: +3 Mult when scored | Available from start |
| Gluttonous Joker | $5 | Played Club cards: +3 Mult when scored | Available from start |
| Jolly Joker | $3 | +8 Mult if played hand contains a Pair | Available from start |
| Zany Joker | $4 | +12 Mult if played hand contains Three of a Kind | Available from start |
| Mad Joker | $4 | +10 Mult if played hand contains Two Pair | Available from start |
| Crazy Joker | $4 | +12 Mult if played hand contains a Straight | Available from start |
| Droll Joker | $4 | +10 Mult if played hand contains a Flush | Available from start |
| Sly Joker | $3 | +50 Chips if played hand contains a Pair | Available from start |
| Wily Joker | $4 | +100 Chips if played hand contains Three of a Kind | Available from start |
| Clever Joker | $4 | +80 Chips if played hand contains Two Pair | Available from start |
| Devious Joker | $4 | +100 Chips if played hand contains a Straight | Available from start |
| Crafty Joker | $4 | +80 Chips if played hand contains a Flush | Available from start |
| Half Joker | $5 | +20 Mult if played hand contains 3 or fewer cards | Available from start |
| Credit Card | $1 | Go up to -$20 in debt | Available from start |
| Banner | $5 | +30 Chips for each remaining discard | Available from start |
| Mystic Summit | $5 | +15 Mult when 0 discards remaining | Available from start |
| 8 Ball | $5 | 1 in 4 chance for each played 8 to create a Tarot card when scored (needs room) | Available from start |
| Misprint | $4 | +0 to +23 Mult (random each scoring) | Available from start |
| Raised Fist | $5 | Adds double the rank of the lowest-ranked card held in hand to Mult (+Mult) | Available from start |
| Chaos the Clown | $4 | 1 free Reroll per shop | Available from start |
| Scary Face | $4 | Played face cards: +30 Chips when scored | Available from start |
| Abstract Joker | $4 | +3 Mult for each Joker card you have | Available from start |
| Delayed Gratification | $4 | Earn $2 per discard if no discards are used by end of round | Available from start |
| Gros Michel | $5 | +15 Mult; 1 in 6 chance to be destroyed at end of round | Available from start |
| Even Steven | $4 | Played even-rank cards (10, 8, 6, 4, 2): +4 Mult when scored | Available from start |
| Odd Todd | $4 | Played odd-rank cards (A, 9, 7, 5, 3): +31 Chips when scored | Available from start |
| Scholar | $4 | Played Aces: +20 Chips and +4 Mult when scored | Available from start |
| Business Card | $4 | Played face cards have 1 in 2 chance to give $2 when scored | Available from start |
| Supernova | $5 | Adds the number of times the current poker hand has been played this run to Mult (+Mult) **[scaling]** | Available from start |
| Ride the Bus | $6 | +1 Mult per consecutive hand played that contains no scoring face card; resets when a face card is scored **[scaling]** | Available from start |
| Egg | $4 | Gains $3 of sell value at end of round **[scaling sell value]** | Available from start |
| Runner | $5 | Gains +15 Chips if played hand contains a Straight **[scaling]** | Available from start |
| Ice Cream | $5 | +100 Chips; -5 Chips for every hand played **[scaling down]** | Available from start |
| Splash | $3 | Every played card counts in scoring | Available from start |
| Blue Joker | $5 | +2 Chips for each remaining card in deck | Available from start |
| Faceless Joker | $4 | Earn $5 if 3 or more face cards are discarded at the same time | Available from start |
| Green Joker | $4 | +1 Mult per hand played; -1 Mult per discard **[scaling]** | Available from start |
| Superposition | $4 | Create a Tarot card if played hand contains an Ace and a Straight (needs room) | Available from start |
| To Do List | $4 | Earn $4 if poker hand is the listed type; type changes at end of round | Available from start |
| Cavendish | $4 | X3 Mult; 1 in 1000 chance to be destroyed at end of round | Available from start |
| Red Card | $5 | Gains +3 Mult when any Booster Pack is skipped **[scaling]** | Available from start |
| Square Joker | $4 | Gains +4 Chips if played hand has exactly 4 cards **[scaling]** | Available from start |
| Riff-Raff | $6 | Creates 2 Common Jokers when Blind is selected (needs room) | Available from start |
| Photograph | $5 | First played face card gives X2 Mult when scored | Available from start |
| Reserved Parking | $6 | Each face card held in hand has 1 in 2 chance to give $1 | Available from start |
| Mail-In Rebate | $4 | Earn $5 for each discarded card of the listed rank; rank changes each round | Available from start |
| Hallucination | $4 | 1 in 2 chance to create a Tarot card when a Booster Pack is opened (needs room) | Available from start |
| Fortune Teller | $6 | +1 Mult per Tarot card used this run **[scaling]** | Available from start |
| Juggler | $4 | +1 hand size | Available from start |
| Drunkard | $4 | +1 discard each round | Available from start |
| Golden Joker | $6 | Earn $4 at end of round | Available from start |
| Popcorn | $5 | +20 Mult; -4 Mult per round played **[scaling down]** | Available from start |
| Walkie Talkie | $4 | Each played 10 or 4: +10 Chips and +4 Mult when scored | Available from start |
| Smiley Face | $4 | Played face cards: +5 Mult when scored | Available from start |
| Golden Ticket | $5 | Played Gold cards earn $4 when scored | Play a 5-card hand containing only Gold cards |
| Swashbuckler | $4 | Adds the combined sell value of all your other owned Jokers to Mult (+Mult) | Sell 20 Jokers (cumulative) |
| Hanging Chad | $4 | Retrigger the first played card used in scoring 2 additional times | Beat a Boss Blind with a High Card hand |
| Shoot the Moon | $5 | Each Queen held in hand: +13 Mult | Play every Heart card in the deck in a single round |

---

## Uncommon jokers (64)

25% of random rarity rolls. Includes most retrigger, suit-conversion, and early Xmult enablers.

| Name | Cost | Effect (exact values) | Unlock requirement |
|------|------|----------------------|--------------------|
| Joker Stencil | $8 | X1 Mult for each empty Joker slot (Joker Stencil itself counts as occupying a slot) | Available from start |
| Four Fingers | $7 | All Flushes and Straights can be made with 4 cards instead of 5 | Available from start |
| Mime | $5 | Retrigger all cards held in hand abilities | Available from start |
| Ceremonial Dagger | $6 | When Blind selected, destroy Joker to the right and add double its sell value to this Joker's Mult (+Mult) **[scaling]** | Available from start |
| Marble Joker | $6 | Adds one Stone card to the deck when Blind is selected | Available from start |
| Loyalty Card | $5 | X4 Mult every 6 hands played (counter resets after applying) | Available from start |
| Dusk | $5 | Retrigger all played cards in the final hand of the round | Available from start |
| Fibonacci | $8 | Each played Ace, 2, 3, 5, or 8 gives +8 Mult when scored | Available from start |
| Steel Joker | $7 | Gives X0.2 Mult for each Steel Card in your full deck **[scaling with deck]** | Available from start |
| Hack | $6 | Retrigger each played 2, 3, 4, and 5 | Available from start |
| Pareidolia | $5 | All cards are considered face cards | Available from start |
| Space Joker | $5 | 1 in 4 chance to upgrade the level of the played poker hand | Available from start |
| Burglar | $6 | When Blind selected, gain +3 Hands and lose all discards for the round | Available from start |
| Blackboard | $6 | X3 Mult if all cards held in hand are Spades or Clubs (or hand is empty) | Available from start |
| Sixth Sense | $6 | If first hand of round is a single 6, destroy it and create a Spectral card (needs room) | Available from start |
| Constellation | $6 | Gains X0.1 Mult every time a Planet card is used **[scaling]** | Available from start |
| Hiker | $5 | Every played card permanently gains +5 Chips when scored **[scaling deck]** | Available from start |
| Card Sharp | $6 | X3 Mult if played poker hand has already been played this round | Available from start |
| Madness | $7 | When Blind selected, gain X0.5 Mult and destroy a random Joker **[scaling]** | Available from start |
| Séance | $6 | If poker hand is a Straight Flush, create a random Spectral card (needs room) | Available from start |
| Vampire | $7 | Gains X0.1 Mult per scored Enhanced card, removing the enhancement **[scaling]** | Available from start |
| Shortcut | $7 | Allows Straights to be made with gaps of 1 rank (e.g., 10 8 6 5 3) | Available from start |
| Hologram | $7 | Gains X0.25 Mult every time a playing card is added to your deck **[scaling]** | Available from start |
| Cloud 9 | $7 | Earn $1 for each 9 in your full deck at end of round | Available from start |
| Rocket | $6 | Earn $1 at end of round; payout increases by $2 when a Boss Blind is defeated **[scaling]** | Available from start |
| Midas Mask | $7 | All played face cards become Gold cards when scored | Available from start |
| Luchador | $5 | Sell this card to disable the current Boss Blind's effect | Available from start |
| Gift Card | $6 | Adds $1 of sell value to every Joker and Consumable at end of round **[scaling sell value]** | Available from start |
| Turtle Bean | $6 | +5 hand size, reduced by 1 each round **[scaling down]** | Available from start |
| Erosion | $6 | +4 Mult for each card below the starting deck size (52) in your full deck | Available from start |
| To the Moon | $5 | Earn an extra $1 of interest per $5 you have at end of round | Available from start |
| Stone Joker | $6 | +25 Chips for each Stone card in your full deck **[scaling with deck]** | Available from start |
| Lucky Cat | $6 | Gains X0.25 Mult each time a Lucky card successfully triggers **[scaling]** | Available from start |
| Bull | $6 | +2 Chips for each $1 you currently have | Available from start |
| Diet Cola | $6 | Sell this card to create a free Double Tag | Available from start |
| Trading Card | $6 | If first discard of round is a single card, destroy it and earn $3 | Available from start |
| Flash Card | $5 | Gains +2 Mult per shop reroll **[scaling]** | Available from start |
| Spare Trousers | $6 | Gains +2 Mult if played hand contains a Two Pair **[scaling]** | Available from start |
| Ramen | $6 | X2 Mult, loses X0.01 Mult per card discarded **[scaling down]** | Available from start |
| Seltzer | $6 | Retrigger all cards played for the next 10 hands **[depleting]** | Available from start |
| Castle | $6 | Gains +3 Chips per discarded card of a chosen suit; suit changes each round **[scaling]** | Available from start |
| Mr. Bones | $5 | Prevents death if total chips scored are at least 25% of the requirement; self-destructs after | Lose 5 runs (cumulative) |
| Acrobat | $6 | X3 Mult on the final hand of the round | Play 200 hands (cumulative) |
| Sock and Buskin | $6 | Retrigger all played face cards | Play 300 face cards (cumulative) |
| Troubadour | $6 | +2 hand size; -1 hand (play) each round | Win 5 consecutive rounds, each with only 1 hand played |
| Certificate | $6 | When round begins, add a random playing card with a random seal to your hand | Have a Gold card with a Gold Seal at the same time |
| Smeared Joker | $7 | Hearts and Diamonds count as the same suit; Spades and Clubs count as the same suit | Have 3 or more Wild cards in your deck |
| Throwback | $6 | Gains X0.25 Mult for each Blind skipped this run **[scaling]** | Continue a saved run from the main menu |
| Rough Gem | $7 | Played Diamond cards earn $1 each when scored | Have at least 30 Diamond cards in your deck |
| Bloodstone | $7 | Played Heart cards have a 1 in 2 chance to give X1.5 Mult when scored | Have at least 30 Heart cards in your deck |
| Arrowhead | $7 | Played Spade cards give +50 Chips when scored | Have at least 30 Spade cards in your deck |
| Onyx Agate | $7 | Played Club cards give +7 Mult when scored | Have at least 30 Club cards in your deck |
| Glass Joker | $6 | Gains X0.75 Mult for every Glass card that is destroyed **[scaling]** | Have 5 or more Glass cards in your deck at once |
| Showman | $5 | Joker, Tarot, Planet, and Spectral cards may appear multiple times (duplicates allowed) | Reach Ante level 4 |
| Flower Pot | $6 | X3 Mult if played hand contains a Diamond, Club, Heart, and Spade card | Reach Ante level 8 |
| Merry Andy | $7 | +3 discards each round; -1 hand size | Win a run in 12 or fewer rounds |
| Oops! All 6s | $4 | Doubles all listed probabilities (e.g., 1 in 4 becomes 2 in 4) | Earn at least 10,000 chips in a single hand |
| The Idol | $6 | Each played card of the listed rank and suit gives X2 Mult; card changes each round | Earn at least 1,000,000 chips in a single hand |
| Seeing Double | $6 | X2 Mult if played hand has a scoring Club card AND a scoring card of any other suit | Play a hand containing four 7 of Clubs |
| Matador | $7 | Earn $8 if played hand triggers the Boss Blind's ability | Defeat a Boss Blind in one hand without using a discard |
| Satellite | $6 | Earn $1 at end of round per unique Planet card used this run **[scaling]** | Have at least $400 at one time |
| Cartomancer | $6 | Create a Tarot card when Blind is selected (needs room) | Discover (use/see) every Tarot card |
| Astronomer | $8 | All Planet cards and Celestial Packs in the shop are free | Discover (use/see) every Planet card |
| Bootstraps | $7 | +2 Mult for every $5 you currently have | Have at least 2 Polychrome Jokers at the same time |

---

## Rare jokers (20)

5% of random rarity rolls. Home of the strongest Xmult scalers and the copy jokers.

| Name | Cost | Effect (exact values) | Unlock requirement |
|------|------|----------------------|--------------------|
| DNA | $8 | If first hand of round is a single card, add a permanent copy of it to your deck and draw it to hand **[scaling deck]** | Available from start |
| Vagabond | $8 | Create a Tarot card if a hand is played while you have $4 or less (needs room) | Available from start |
| Baron | $8 | Each King held in hand gives X1.5 Mult | Available from start |
| Obelisk | $8 | Gains X0.2 Mult per consecutive hand played without playing your most-played poker hand; resets when you play it **[scaling]** | Available from start |
| Baseball Card | $8 | Each Uncommon Joker you own gives X1.5 Mult | Available from start |
| Ancient Joker | $8 | Each played card of the listed suit gives X1.5 Mult when scored; suit changes at end of round | Available from start |
| Campfire | $9 | Gains X0.25 Mult for each card sold; resets to X1 when a Boss Blind is defeated **[scaling]** | Available from start |
| Blueprint | $10 | Copies the ability of the Joker to the right | Win a run |
| Wee Joker | $8 | Gains +8 Chips when each played 2 is scored **[scaling]** | Win a run in 18 or fewer rounds |
| Hit the Road | $8 | Gains X0.5 Mult for every Jack discarded this round; resets each round **[scaling]** | Discard 5 Jacks at the same time |
| The Duo | $8 | X2 Mult if played hand contains a Pair | Win a run without playing a Pair |
| The Trio | $8 | X3 Mult if played hand contains a Three of a Kind | Win a run without playing a Three of a Kind |
| The Family | $8 | X4 Mult if played hand contains a Four of a Kind | Win a run without playing a Four of a Kind |
| The Order | $8 | X3 Mult if played hand contains a Straight | Win a run without playing a Straight |
| The Tribe | $8 | X2 Mult if played hand contains a Flush | Win a run without playing a Flush |
| Stuntman | $7 | +250 Chips; -2 hand size | Earn at least 100,000,000 (1e8) chips in a single hand |
| Invisible Joker | $8 | After 2 rounds, sell this card to duplicate a random Joker (removes Negative from the copy) | Win a run without ever having more than 4 Jokers |
| Brainstorm | $10 | Copies the ability of the leftmost Joker | Discard a Royal Flush |
| Driver's License | $7 | X3 Mult if you have at least 16 Enhanced cards in your full deck | Enhance at least 16 cards in your deck |
| Burnt Joker | $8 | Upgrades the level of the first poker hand discarded each round | Sell 50 cards (cumulative) |

---

## Legendary jokers (5)

**Source: ONLY from The Soul spectral card.** They cannot be purchased or rolled from shops/packs. Internal buy price is $20 (sell value scales accordingly). In-game unlock condition displays as "?????" until discovered.

| Name | Cost | Effect (exact values) | Source |
|------|------|----------------------|--------|
| Canio | $20 | Gains X1 Mult each time a face card is destroyed **[scaling]** | The Soul spectral card |
| Triboulet | $20 | Played Kings and Queens each give X2 Mult when scored | The Soul spectral card |
| Yorick | $20 | Gains X1 Mult for every 23 cards discarded (counter carries over) **[scaling]** | The Soul spectral card |
| Chicot | $20 | Disables the effect of every Boss Blind | The Soul spectral card |
| Perkeo | $20 | At end of shop, creates a Negative copy of 1 random consumable card you are holding | The Soul spectral card |

---

## See also

- `04-cards-and-enhancements.md` — card enhancements (Gold, Steel, Glass, Lucky, Stone, Wild), seals, and editions
- `06-consumables.md` — Tarot, Planet, and Spectral cards (including The Soul)
- `07-blinds-and-antes.md` — Boss Blinds and ante structure
- `03-scoring.md` — how Chips, +Mult, and Xmult combine into the final score
- Balatro Wiki (community): https://balatrowiki.org/w/Jokers
- Balatro Fandom Wiki: https://balatro.fandom.com/wiki/Jokers
