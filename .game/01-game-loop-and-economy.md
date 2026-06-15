# Game Loop and Economy

Detailed mechanics of the per-round play loop, the shop, the money economy, slot limits, skipping/Tags, and boss-blind rerolls.

> As of: Balatro v1.0 base game (patch ~1.0.1n/1.0.1o, 2024–2025). Defaults reflect the standard Red Deck / White Stake unless noted.

## Per-Round Loop

Each round = one Blind attempt. The flow:

1. You are dealt cards from your deck up to your **hand size** (default **8** cards on screen).
2. **Select up to 5 cards** from your hand.
3. Choose one action on the selection:
   - **Play hand** — the selected cards are evaluated as a poker hand and scored (Chips × Mult contributes to the round total). Consumes **1 hand**.
   - **Discard** — the selected cards are thrown away without scoring. Consumes **1 discard**.
4. After a Play or Discard, your hand **refills from the deck** back up to hand size (drawing the top cards of the remaining deck). Played/discarded cards leave the hand for that round; cards already played in prior rounds of the same blind do not return until the deck reshuffles for the next blind.
5. Repeat until you either **meet the chip requirement** (win the blind immediately) or **run out of hands** (lose the run, if requirement unmet).

Default per-round resources:

| Resource | Default | Notes |
|----------|---------|-------|
| Hand size (cards held) | 8 | Modified by jokers/vouchers/decks/some boss blinds |
| Hands (plays) per round | 4 | "Most decks start with 4 hands per round" |
| Discards per round | 3 | Red Deck starts with +1 (=4); other decks/jokers vary |
| Cards selectable per play | up to 5 | A poker hand uses 1–5 cards |

Unused hands and discards do **not** carry to the next round (they reset), but unused **hands** can pay out money (see Economy). Discards must run out *and* hands run out unmet to lose — running out of discards alone is fine.

## Beating a Blind → Cash Out → Shop

When you meet a blind's chip requirement:

1. The round ends immediately (a "Cash Out" screen tallies your earnings — base blind reward + interest + unused-hand money + any card/joker payouts).
2. You collect the money and proceed to the **Shop** (for Small/Big/Boss blinds that were *played*).
3. From the shop you continue to the next blind.

**Skipping** a Small or Big blind instead grants a **Tag** and goes straight toward the next blind — you forgo that blind's reward and its shop visit. The Boss Blind cannot be skipped.

## The Shop

Default shop layout per visit:

| Section | Default slots | Notes |
|---------|---------------|-------|
| Cards (Joker / Tarot / Planet / Spectral) | **2** | Increased to 3 (Overstock voucher) or 4 (Overstock Plus). Usually Jokers but can be consumables. |
| Booster packs | **2** | First-ever shop guarantees one Buffoon Pack. |
| Vouchers | **1** | One voucher offered per shop visit. |

**Reroll** (refreshes the 2 card slots, not packs/voucher):

- Starts at **$5**, increases by **$1** per reroll within the same shop, **resets to $5** on entering a new shop.
- **Reroll Surplus** voucher: −$2 (start $3). **Reroll Glut** voucher: a further −$2 (stacks → start $1).
- The Chaos the Clown joker gives **1 free reroll** per shop. The D6 Tag makes rerolls start at $0 in the next shop.

**Booster pack base prices:** Normal $4, Jumbo $6, Mega $8. Opening a pack lets you pick a number of cards from a larger selection (counts vary by pack type/size).

**Buying / selling formula:**

- `buy_cost = (base_cost + edition_cost) × discount_percent`
- `sell_value = floor(buy_cost / 2)` (the Gift Card joker adds +$1 sell value to each item).

**Base buy prices (before editions/discounts):**

| Item | Price |
|------|-------|
| Common Joker | $1–6 |
| Uncommon Joker | $4–8 |
| Rare Joker | $7–10 |
| Tarot card | $3 |
| Planet card | $3 |
| Spectral card | $4 |

You may **sell** Jokers and Consumables back at their sell value to free slots and gain money.

## Slot Limits

| Slot type | Default limit | Increased by (examples) |
|-----------|---------------|--------------------------|
| Joker slots | **5** | Negative edition jokers (+1 each, off-grid), some vouchers/decks |
| Consumable slots | **2** | Negative consumables, certain decks/vouchers |

A **Negative** edition joker/consumable occupies *no* slot, effectively adding capacity.

## Money Economy

Income sources at the end of a played blind (and elsewhere):

### Base blind reward (on beating, when *played* not skipped)

| Blind | Reward |
|-------|--------|
| Small Blind | $3 (⚠️ **$0** on Red Stake and higher) |
| Big Blind | $4 |
| Boss Blind | $5 |
| Showdown Boss (Ante 8 finisher) | $8 |

No reward if the round was "saved" by Mr. Bones. Skipped blinds give no reward (they give a Tag instead). Challenge decks (Cruelty, The Omelette) can disable some/all rewards.

### Interest

- **$1 for every $5 held**, evaluated at end of round.
- Default cap **$5 per round** — i.e. money above **$25** earns no extra interest.
- Cap raised by vouchers: Seed Money → $10 cap; Money Tree → $20 cap.
- No interest in Green Deck, The Omelette, or Mad World.

### Unused hands

- **$1 per unused hand** at round end (default).
- Green Deck pays **$2 per remaining hand** instead (but earns no interest).
- The Omelette / Mad World pay nothing for extra hands.

### Gold cards & seals

- **Gold enhancement** (Gold card): **+$3** if that card is *held in hand* at end of round.
- **Gold Seal**: **+$3** each time that card is *played and scores*.

### Selling items

- Jokers / Consumables sell for `floor(buy_cost / 2)`. Gift Card joker adds +$1 each.

### Other notable sources (examples, not exhaustive)

- Golden Joker: +$4 per round. Satellite joker: +$1 per unique Planet card used this run.
- Investment Tag: +$25 after defeating the next Boss Blind.
- Tarot/Spectral payouts: Temperance (up to $50), The Hermit (up to $20).

## Skipping Blinds and the Tag System

Skipping the **Small** or **Big** blind grants a **Tag** (and skips that blind's reward + shop). Tags may trigger immediately or on a later condition (e.g. next shop). Multiple held tags trigger oldest-first. **Boss blinds cannot be skipped.**

There are **24 tags**. Nine cannot appear in Ante 1 (marked "2+" below): Negative, Standard, Meteor, Buffoon, Handy, Garbage, Ethereal, Top-up, Orbital.

| Tag | Effect | Ante |
|-----|--------|------|
| Boss Tag | Rerolls the Boss Blind | Any |
| Buffoon Tag | Free Mega Buffoon Pack | 2+ |
| Charm Tag | Free Mega Arcana Pack | Any |
| Coupon Tag | Initial cards and booster packs in next shop are free | Any |
| D6 Tag | Rerolls in next shop start at $0 | Any |
| Double Tag | Gives a copy of the next selected Tag (Double Tag excluded) | Any |
| Economy Tag | Doubles your money (max +$40) | Any |
| Ethereal Tag | Free Spectral Pack | 2+ |
| Foil Tag | Next base-edition shop Joker is free and becomes Foil | Any |
| Garbage Tag | $1 per unused discard this run (minimum $0) | 2+ |
| Handy Tag | $1 per played hand this run (minimum $0) | 2+ |
| Holographic Tag | Next base-edition shop Joker is free and becomes Holographic | Any |
| Investment Tag | Gain $25 after defeating the next Boss Blind | Any |
| Juggle Tag | +3 hand size next round | Any |
| Meteor Tag | Free Mega Celestial Pack | 2+ |
| Negative Tag | Next base-edition shop Joker is free and becomes Negative | 2+ |
| Orbital Tag | Upgrade a (random/specified) poker hand by 3 levels | 2+ |
| Polychrome Tag | Next base-edition shop Joker is free and becomes Polychrome | Any |
| Rare Tag | Shop has a free Rare Joker | Any |
| Speed Tag | $5 per skipped blind this run (minimum $5) | Any |
| Standard Tag | Free Mega Standard Pack | 2+ |
| Top-up Tag | Create up to 2 Common Jokers (must have room) | 2+ |
| Uncommon Tag | Shop has a free Uncommon Joker | Any |
| Voucher Tag | Adds one Voucher to the next shop | Any |

## Boss Blind Reroll

Boss blinds are not skippable, but their *type* can be rerolled with a voucher:

- **Director's Cut** voucher: reroll the Boss Blind **once per ante**, costing **$10** per reroll.
- **Retcon** voucher: **unlimited** boss rerolls at **$10** each (requires having discovered 25 blinds to appear in the shop).

Without one of these vouchers, the boss blind cannot be rerolled.

## See also

- `00-overview.md`
