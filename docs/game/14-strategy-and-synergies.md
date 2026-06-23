# Strategy and Synergies

How to build runs that scale to enormous scores: the math of multiplication, the major joker archetypes, key synergy combos, economy discipline, boss-blind counterplay, and deck/stake notes — synthesizing the rest of this knowledge base toward the project goal of **maximizing score**.

> As of: Balatro v1.0 base game (patch ~1.0.1n/1.0.1o, 2024–2025). PC/console base game, no mods.

This file references and assumes the mechanics defined in the other files (jokers, scoring, enhancements, planets, blinds, decks, stakes). Where it names a joker, see `05-jokers.md` for the exact card text. Where it names an enhancement/edition/seal, see `04-card-enhancements.md` (and `02-scoring-system.md`).

---

## 1. The Scaling Principle

### The scoring pipeline

Every played hand resolves as:

```
score = Chips × Mult
```

But that final Mult is the **end product of an ordered pipeline**. Effects apply left-to-right across scored cards, held cards, and jokers, in this conceptual order:

1. **Base** chips and base mult of the poker hand (raised by Planet levels — see `07-planet-cards.md`).
2. **+Chips** from scored card ranks, enhancements (Bonus, Stone), editions (Foil), and chip jokers.
3. **+Mult** (additive) from card enhancements (Mult cards), editions (Holographic +10), and additive-mult jokers.
4. **×Mult** (multiplicative) from Xmult jokers, Polychrome editions (×1.5), Glass cards (×2), Steel cards held in hand (×1.5), and similar.

The critical distinction, used throughout this file and the project convention:

| Term | Meaning | Example sources |
|------|---------|-----------------|
| **Chips** | Additive to the chip total | card ranks, Bonus cards, Foil (+50), Stone (+50) |
| **+Mult** | **Additive** to the multiplier | Mult cards (+4), Holographic (+10), Gros Michel (+15) |
| **Xmult** | **Multiplicative** on the whole multiplier | Polychrome (×1.5), Glass card (×2), Cavendish (×3), most "X… Mult" jokers |

### Why Xmult dominates the late game

Additive sources push the multiplier up linearly; multiplicative sources scale the **entire** accumulated multiplier. Because the pipeline applies +Mult **before** ×Mult, a single Xmult joker multiplies everything you have already built — all your +Mult, all your chips' worth of mult value. Two consequences:

- **Late antes need exponential output.** Ante 8 base targets reach 50,000–200,000 chips depending on stake (`11-blinds-and-antes.md`, `00-overview.md`), and Endless grows roughly exponentially per ante. Linear +Mult cannot keep pace; only stacking ×Mult does.
- **Stacking ×Mult is the core skill.** With chips C and additive mult M, adding +5 mult gives `C·(M+5)`. A ×1.5 joker gives `C·(M·1.5)` — and **two** ×1.5 jokers give `C·M·2.25`, three give `C·M·3.375`, and so on. Xmult sources **multiply each other**; +Mult sources merely add. This is why a few big Xmult jokers beat a board full of +Mult jokers at high antes.

### Joker slots are the scarce resource

Default 5 joker slots (more via Negative editions, the Antimatter voucher, and Joker-slot decks). Each slot occupied by a flat +Mult or +Chips joker is a slot **not** holding an Xmult engine. The well-established meta rule: **don't over-stuff with weak additive jokers** — keep room for Xmult and for *scaling* jokers that grow over the run. If your build isn't scaling fast by Ante 5, pivot: reroll for an Xmult or scaling joker rather than adding another flat bonus.

### Chips × Mult balance

A score is maximized when **neither factor is tiny**. A huge mult times 100 chips is wasted; a huge chip count times mult 4 is wasted. Practically:

- Get chips to a "healthy" floor (hand level + a couple of chip sources), then pour everything into the **mult side**, especially Xmult.
- Stone cards, Bonus cards, Foil, and Hiker/Stuntman-type chip jokers cover the chip floor cheaply so slots can go to mult.

### Level ONE poker hand, do not spread

Planet cards level a *specific* hand type, raising its base chips **and** base mult permanently for the run (`07-planet-cards.md`). Leveling is the cheapest persistent boost to both factors at once — but it is **per hand type**. Spreading Planets across Pair, Two Pair, Flush, etc. dilutes every one of them. The standard discipline:

- **Pick one hand you can reliably make every round** and funnel all Planets into it.
- Build the deck so that hand is consistent (suit/rank conversion via Tarots — `06-tarot-cards.md`; e.g. The Sun/Moon/Star/World to force a Flush).
- Common funnels: **Flush** (easy to force, high base chips), **High Card** (always playable, see below), **Two Pair / Full House** (consistent mid-tier), **Straight Flush** (build-around payoff).
- The High Priestess / Telescope voucher / Observatory voucher accelerate or reward single-hand commitment.

---

## 2. Major Build Archetypes

Each archetype names concrete jokers; cross-reference `05-jokers.md` for exact text. "Why it scales" focuses on the score-growth engine, not mere survival.

### Flush / Suit builds
- **Pieces:** Four Fingers (flushes/straights need only 4 cards), Smeared Joker (Hearts=Diamonds, Spades=Clubs — turns any 2 suits into 1 for flush purposes), Droll/Drunkard, suit-conversion Tarots (The Sun/Moon/Star/World), flush-scaling jokers (e.g. Bloodstone for Hearts), and any "+Mult if Flush" joker.
- **Why it scales:** Flush has a high base chip value and is trivial to make once the deck is mono-suit (Smeared + conversion). Funnel **all** Planet cards into Flush to grow both base chips and base mult; layer Xmult on top. Four Fingers + Smeared makes Flush Five / Flush House attainable for huge base scores.

### High Card / single-card builds
- **Pieces:** Baron-style held jokers aside, the core is jokers keying off a single scored card — e.g. **Vampire**, **Supernova**, **Hologram**, plus Stone/Bonus chips on the one card, and retriggers. The Banner joker (chips per unused discard) loves High Card because it doesn't care *what* you play.
- **Why it scales:** High Card is **always playable** (no hand-shape requirement), so it is the most consistent funnel for Planet levels and the easiest to retrigger and Xmult a single high-value card. It needs the most joker support but produces very consistent high-stakes results. Stack retriggers + Xmult on one enhanced card (e.g. a Glass/Steel high card with a Red Seal).

### Retrigger builds
- **Pieces:** **Mime** (retriggers all held-in-hand abilities), **Hack** (retriggers scored 2–5s), **Hanging Chad** (retriggers the first scored card +2 times), **Sock and Buskin** (retriggers all scored face cards), **Dusk** (retrigger on final hand of round), **Seltzer**, **Red Seals** (retrigger that one card on play/hold), and **Hack/Sock** combos.
- **Why it scales:** A retrigger re-runs a card's *entire* contribution — its chips, its +Mult, **and** its Xmult (e.g. a Glass card's ×2 or a Steel card's ×1.5 fires again). Retriggers therefore **multiply your best card's effect** and compound with every other layer. Red Seals + Mime/Sock turn one enhanced card into several effective copies.

### Mult-stacking / additive economy hybrids
- **Pieces:** +Mult-per-condition jokers (Gros Michel/Cavendish line, Joker, Jolly/Zany/etc. for hand types), Holographic editions (+10 mult each), Mult-enhanced cards (+4 each), The Empress (mass Mult cards).
- **Why it scales (and its ceiling):** Cheap, reliable early-game floor that gets the chip×mult product off the ground. **It plateaus** — additive mult can't keep up past mid-game, so this archetype is a *bridge* to an Xmult build, not a finisher. Keep these only until Xmult engines come online, then sell for slots.

### Xmult engines (the finishers)
These are scaling jokers whose multiplier **grows permanently** over the run — the backbone of any high-score build:

| Joker | Engine | Notes |
|-------|--------|-------|
| **Hologram** | +X0.25 Mult per playing card **added to deck** | feed with Tarots/Spectrals that create cards; uncapped |
| **Constellation** | +X0.1 Mult per **Planet card used** (starts X1) | pairs with single-hand Planet spam; not retroactive |
| **Campfire** | +X0.25 per **card sold**, resets when Boss defeated | sell-fuel; strongest right before a boss |
| **Vampire** | +X0.1 per scored **Enhanced** card (removes the enhancement) | consumes enhancements for permanent Xmult |
| **Lucky Cat** | +X0.25 each time a **Lucky card** triggers (starts X1) | pair with mass Lucky cards (The Magician) |
| **Glass Joker** | +X0.75 per **Glass card destroyed** (starts X1) | pairs with Glass deck + retriggers that break glass |
| **Madness / Obelisk / Throwback / Ramen / Caino / Yorick / Hit the Road** | various per-condition Xmult growth | see `05-jokers.md`; all reward sustaining a condition |

Plus **flat Xmult finishers** (don't grow, but big): **Cavendish** (×3), **Card Sharp** (×3 if hand type already played this round), **The Duo/Trio/Family/Order/Tribe** (×Mult for specific hand types), **Blueprint/Brainstorm** (copy an Xmult), and **Polychrome** editions (×1.5) on jokers.

> **Project takeaway:** acquiring an Xmult scaling joker **and keeping its condition fed** is the single most important determinant of final score. Indirect feeds (selling for Campfire, adding cards for Hologram, using Planets for Constellation) let the engine run every round.

### Money / economy builds
- **Pieces:** **Bull** (+2 Chips per $1 held), **Bootstraps** (+2 Mult per $5 held), **To the Moon** voucher (+$1 interest per $5), **Seed Money / Money Tree** vouchers (raise interest cap to $10 / $20), **Gold cards** ($3 each when held at round end), **Gold Seal** ($3 when played), **Rocket** (+$ per round, grows when Boss beaten), **To Do List / Business Card / Cloud 9 / Egg / Delayed Gratification**, **The Hermit** Tarot (double money, cap +$20).
- **Why it scales for SCORE (not just survival):** A money build is only a score engine when money is *converted* into score. **Bull turns each held dollar into +2 chips** and **Bootstraps turns each $5 into +2 Mult** — so a large bankroll directly inflates chips and mult. Otherwise economy is indirect: more money → more rerolls → faster Xmult acquisition. Hoard to the interest cap, convert at the finish line.

### Legendary / Blueprint + Brainstorm copy engines
- **Pieces:** **Blueprint** (copies the joker to its **immediate right**), **Brainstorm** (copies the **leftmost** joker), Legendaries (Canio +Xmult on face destroy, Triboulet ×2 per played King/Queen, Yorick, Chicot, Perkeo).
- **Why it scales:** Each copy joker effectively **duplicates your best Xmult source** — a second ×3 becomes ×9 on that pair of slots. Positioning is load-bearing: place the joker to be copied so the copy sits adjacent (Blueprint to the **left of** its target's-right slot; Brainstorm targets the leftmost). Blueprint + Brainstorm can **chain** to copy the same engine twice. With Negative editions you can run both copies plus the original Xmult engine without losing slots.

### Steel / held-in-hand builds
- **Pieces:** **Baron** (×1.5 Mult per **King held in hand**), **Steel cards** (×1.5 while held unplayed), **Mime** (retriggers held-in-hand abilities → Steel and Baron fire twice), The Chariot Tarot (make Steel cards), Red Seal on a Steel King, Blueprint/Brainstorm copying Baron.
- **Why it scales (multiplicatively):** Each Steel King held supplies ×1.5 from the card **and** ×1.5 from Baron, and these stack across multiple Kings — pure multiplication. A single Steel King + Red Seal under Baron yields ≈×1.5⁴ ≈ ×5.1; adding **Mime** (retrigger held effects) pushes one card to ≈×1.5⁶ ≈ ×11.4. Fill the hand with Steel Kings and copy Baron for board-wide multiplicative explosion. You play a tiny hand (often High Card) while the **held** cards do the scoring.

### Discard-synergy builds
- **Pieces:** **Faceless Joker** ($ for discarding 3+ face cards), **Mail-In Rebate** (+$ per discarded rank of the round), **Castle** (+Chips per discarded card of a chosen suit, locks each round), **Banner** (+30 Chips per **remaining** discard), **Trading Card** ($ + destroy on single-card discard), **Burnt Joker** (level up the hand type of your first discard), extra-discard sources (Red Deck, vouchers, Drunkard).
- **Why it scales:** Discards become a **second resource stream**. Castle is a per-suit chip scaler that grows all run; Burnt Joker turns discards into free hand-leveling (chips **and** mult on your funnel hand); Banner rewards *holding* discards for a big chip injection. Combine with a flexible hand (High Card/Flush) so discarding aggressively to dig for your engine costs nothing.

---

## 3. Key Synergies

| Combo | Pieces | Why it works |
|-------|--------|--------------|
| **Baron + Steel Kings** | Baron, several Steel Kings held in hand | Each King = ×1.5 (Steel) × ×1.5 (Baron); stacks multiplicatively across Kings while you play a tiny hand |
| **Baron + Mime** | Baron, Mime, Steel Kings | Mime retriggers all held-in-hand effects → both Steel and Baron fire **twice** per King (per-card ≈×1.5⁶ at best) |
| **Baron + Blueprint/Brainstorm** | Baron + a copy joker | Adds another ×1.5-per-King layer on top |
| **Four Fingers + Smeared Joker** | Four Fingers, Smeared Joker | 4-card flushes from a 2-suit (effectively 1-suit) deck → trivial Flush / Flush House / Flush Five every round |
| **Glass deck + Glass Joker + retrigger** | 5+ Glass cards, Glass Joker, Hanging Chad/Sock/Red Seal | Glass gives ×2 each (retriggered = ×2 again); each glass that **breaks** permanently feeds Glass Joker +X0.75 |
| **The Magician + Lucky Cat** | mass Lucky cards, Lucky Cat, retriggers | Every Lucky trigger feeds Lucky Cat +X0.25 permanently; retriggers multiply trigger count |
| **Hologram + card creation** | Hologram, Tarots/Spectrals/decks that add cards | Each added card = permanent +X0.25; uncapped scaling engine |
| **Constellation + single-hand Planet spam** | Constellation, High Priestess/Telescope, one funnel hand | Every Planet used = +X0.1 **and** levels your one hand — double-dips into both factors |
| **Blueprint + Brainstorm chain** | both copy jokers + one strong Xmult | The same Xmult engine copied twice; with Negative editions, original + 2 copies |
| **Bull / Bootstraps + interest economy** | Bull, Bootstraps, To the Moon, Seed Money | Hoarded cash converts directly to +Chips (Bull) and +Mult (Bootstraps) at the finish |
| **Vampire + enhanced-card supply** | Vampire, Tarots that mass-enhance | Each enhanced card scored feeds +X0.1 permanently (consumes the enhancement) |
| **Burnt Joker + discard build** | Burnt Joker, extra discards, one funnel hand | First discard each round levels the funnel hand for free (chips **and** mult) |
| **Hanging Chad + High Card** | Hanging Chad, one big enhanced card | First scored card retriggered +2 → triple the chips/mult/Xmult of your single key card |
| **Triboulet + face-card hand** | Triboulet (legendary), Kings/Queens | ×2 Mult per played King/Queen — multiplicative on every face card scored |

---

## 4. Economy Strategy

### Interest mechanics (base game)
- You earn **$1 interest per $5 held at round end, capped at $5/round** (i.e. interest stops counting above $25).
- **Voucher modifiers:** To the Moon (+$1 interest per $5), **Seed Money** (cap → $10, i.e. up to $50 held counts), **Money Tree** (cap → $20). Stacked, end-of-round interest can reach ~$40.

### When to spend vs save
- **Early antes (1–3):** prioritize a cheap chip/mult floor and your **first scaling/Xmult joker**; keep ≥ $25 so interest never lapses. Don't impulse-buy flat jokers that crowd slots.
- **Mid antes (4–6):** spend down to (but not below) the interest cap each shop to acquire Xmult engines, copy jokers (Blueprint/Brainstorm), and Negative editions (free slots). Saving past the cap earns nothing extra unless you have Bull/Bootstraps/cap-raising vouchers.
- **Late / Endless:** if running Bull/Bootstraps, hoard maximally — the bankroll *is* score. Otherwise, convert money to rerolls hunting the final Xmult.

### Reroll discipline
- Reroll cost rises each reroll within a shop (resets next shop). Reroll **with purpose**: when hunting one specific engine and you're above the interest cap, rerolls are nearly free in opportunity cost.
- The **Reroll/Chaos the Clown** voucher and Chaos the Clown joker grant a free reroll each shop — strong for engine-hunting.
- Don't reroll yourself below $25 (or your cap) early; lost interest compounds.

---

## 5. Boss Blind Counterplay

Boss blinds impose debuffs; preparation means having the right counter *before* you see the boss. Cross-reference `11-blinds-and-antes.md` for the full boss list and exact effects. General-purpose answers:

- **Luchador** (joker) — sell to **disable the current Boss Blind's effect**.
- **Chicot** (legendary joker) — **disables every Boss Blind** for the whole run (and reverts requirement scaling like The Wall back to the normal 2×).
- **Director's Cut / Retcon** voucher — reroll the boss blind.

Specific notable bosses:

| Boss | Effect | Counterplay |
|------|--------|-------------|
| **The Wall** | Requirement is **~4× the ante base** (double the normal boss) | Pure output; Chicot/Luchador removes the doubling (back to 2×). Bring your big Xmult online here. |
| **The Needle** | Sets you to **1 hand** for the round | **Burglar** (sell discards for +3 hands, ignores the 1-hand cap), or a build that wins in **one hand**. Luchador/Chicot restores hands but keeps the (lower) target. |
| **The Ox** | Playing your **most-played hand** gives $0 | Have a viable secondary hand, or Gold/economy that doesn't rely on cashout; Tarots to retool the deck. |
| **The Psychic** | Must play exactly **5 cards** | Avoid sub-5-card funnels here (problematic for High Card/Pair builds); keep a 5-card hand available. |
| **The Eye / The Mouth** | Each hand type playable once / only one hand type all round | Hurts single-hand funnels — keep a couple of viable hand types for these. |
| **The Plant** | All **face cards debuffed** | Bad for Baron/face builds; rely on non-face scorers that round. |
| **The Pillar / The Flint** | Debuff previously-played cards / **halve base chips & mult** | Flint especially punishes thin builds — have raw Xmult to overcome the halving. |

**Project takeaway:** the model should learn to **hold a counter** (Luchador, Burglar) or maintain hand-shape flexibility when a punishing boss is anticipated, rather than committing to a fragile single-hand line. For pure score-max in Endless, big Xmult simply overpowers most debuffs.

---

## 6. Deck and Stake Notes

### Deck guidance for score (see the decks file for exact rules)
- **Red Deck** (+1 discard) — more digging for engine pieces; great for discard-synergy builds.
- **Blue Deck** (+1 hand) — extra scoring attempt; safety and more Planet/engine value per round.
- **Yellow Deck** (+$10 start) — faster economy ramp → earlier Xmult acquisition.
- **Black Deck** (+1 joker slot, −1 hand) — **extra slot is huge** for stacking Xmult; strong for high-score builds that win in few hands.
- **Ghost Deck** (Spectrals appear, start with Hex) — pushes edition/enhancement scaling (Polychrome, seals).
- **Checkered Deck** (only Spades & Hearts) — half-built toward Flush; with Smeared, instant mono-suit.
- **Plasma Deck** — **balances Chips and Mult before scoring** (averages them) and raises blind sizes. The balancing means you must keep **both** factors high; rewards builds that don't lean lopsided, and the high base score per hand suits Endless score-chasing.
- **Abandoned / Erratic** — Abandoned (no face cards) suits non-face builds; Erratic (random ranks/suits) is high-variance, occasionally a free Flush/Five-of-a-Kind deck.

> Deck choice for **score-max** generally favors extra **joker slots** (Black), extra **plays** (Blue/Plasma), or fast **economy** (Yellow), all of which accelerate getting Xmult engines online.

### Stake constraints (escalating; Gold stacks them all)
- **White → Blue:** rising requirements and lost rewards (e.g. Red Stake removes the Small Blind reward); play tighter economy.
- **Black Stake:** Eternal stickers appear — **Eternal jokers cannot be sold or destroyed**. This blocks sell-fuel engines (Campfire feeding via selling, selling a flat joker for slots) if the joker is Eternal. Plan to keep the slot.
- **Orange & Gold Stakes:** add **Perishable** (debuffed after **5 rounds** — useless for long-run scaling jokers) and Gold adds **Rental** ($3/round upkeep, $1 to acquire — an economy drain).
- **Gold Stake reality:** only ~1 in 4 shop/pack jokers is **clean** of all stickers; ~76% carry Eternal/Perishable/Rental or combinations. (Reported figures: 30% Perishable, 30% Rental on these stakes; ~28% fully clean.) Implications: avoid building around a **Perishable** scaling joker (it dies before it matters); be cautious investing in **Eternal** jokers you'd want to sell later; budget for **Rental** upkeep. Favor **acquiring clean** copies of your core engines and consider Negative-edition or Eternal versions of jokers you *intend* to keep forever.

---

## 7. Score-Maximization (Endless) Notes

After winning Ante 8 you may continue into **Endless** (Ante 9+); requirements scale roughly exponentially, so finite/additive builds die quickly and only compounding engines survive. The engines that push runs to astronomical scores (millions → trillions → the game's `naneinf` ceiling):

- **Compounding Xmult scalers that never cap:** Hologram (per added card), Constellation (per Planet), Lucky Cat, Glass Joker, Vampire, Campfire — each round adds permanent Xmult, so output grows multiplicatively run-over-run.
- **Copy multiplication:** Blueprint + Brainstorm duplicating the strongest Xmult engine (with Negative editions to avoid slot loss) squares its contribution.
- **Retrigger compounding:** Mime / Hanging Chad / Sock and Buskin / Red Seals re-run the entire Xmult stack on key cards every hand.
- **Held-in-hand multiplication:** Baron + many Steel Kings + Mime — pure multiplication across the held hand, copyable.
- **Hand-level snowball:** funnel **all** Planets into one hand (Constellation double-dips this) so base chips and base mult are already enormous before Xmult applies.
- **Economy-to-score conversion:** with capped-out interest plus Bull (+2 chips/$1) and Bootstraps (+2 mult/$5), a massive bankroll inflates both factors directly.

**Endless thesis for the project:** the runs with the highest scores are not the ones with the most jokers — they are the ones where **two or more uncapped Xmult engines are kept fed every round, copied, and retriggered, on top of one heavily-leveled poker hand.** The agent's reward (log-transformed per CLAUDE.md) should make these compounding lines clearly preferable to additive plateaus.

---

## See also
- `00-overview.md` — scoring model, run structure, glossary
- `02-scoring-system.md` — exact Chips × Mult resolution order and enhancement effects
- `04-card-enhancements.md` — enhancements, editions (Polychrome/Holo/Foil/Negative), seals
- `05-jokers.md` — exact text, rarity, and Xmult/+Mult classification for every joker named here
- `06-tarot-cards.md` — suit/rank conversion and mass-enhancement Tarots that feed engines
- `07-planet-cards.md` — leveling one poker hand
- `08-spectral-cards.md` — high-power transformations (seals, editions, card creation)
- `11-blinds-and-antes.md` — full boss-blind list, requirements, and per-stake scaling
- decks and stakes reference files — exact per-deck rules and per-stake stickers/penalties
