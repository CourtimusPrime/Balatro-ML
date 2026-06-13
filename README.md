# Balatro ML

A reinforcement learning agent that learns to maximise scores across all decks and antes in Balatro. The agent trains 24/7 via self-play and optionally ingests human gameplay sessions to bootstrap strategy.

---

## Goal

Train an agent to achieve the highest possible scores in Balatro across all 15 decks and all 8 stake levels. The objective is **score maximisation**, not just run completion — the agent optimises for peak chip counts, not win rate, which means it must learn to identify and commit to high-ceiling joker synergies rather than playing conservatively.

Findings will be published to the Balatro subreddit, including emergent strategies, joker synergy heatmaps, and a score progression chart over training time.

---

## Architecture Overview

```
Balatro (Lua/Steamodded)
        │
        │  TCP socket localhost:12345 (agent)
        │  TCP socket localhost:12346 (human sessions)
        ▼
Python Gymnasium Environment
        │
        ├── Observation: card array + jokers + game state
        ├── Action: card selection / shop decisions
        └── Reward: log-transformed score + shaped intermediates
        │
        ▼
PPO Training Loop (Stable-Baselines3)
        │
        ├── Transformer policy network (PyTorch)
        ├── Prioritised replay buffer
        ├── Curriculum learning (Stake 1 → Stake 8)
        └── Imitation learning from human sessions
        │
        ▼
SQLite Database → Streamlit Dashboard
```

---

## Installation

### 1. Mise (runtime version manager)

```bash
curl https://mise.run | sh
echo 'eval "$(mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Python (via mise)

```bash
mise install
```

Python version is pinned in `.mise.toml`. A `.python-version` file is also provided for tools that read that convention.

### 3. Python dependencies (via UV)

```bash
uv venv
uv pip install -r requirements.txt

# Dev tools (linting, type checking, tests)
uv pip install -r requirements-dev.txt
```

### 4. Balatro mod (Steamodded)

Install [lovely-injector](https://github.com/ethangreen-dev/lovely-injector) and [Steamodded](https://github.com/Steamodded/smods) into your Balatro installation. On Linux via Steam, the mod directory is:

```
~/.local/share/love/Mods/
```

Copy the `mod/` directory into your Mods folder:

```bash
cp -r mod/ ~/.local/share/love/Mods/balatro_ml/
```

Balatro must be running before the Python training process starts. The mod will automatically attempt to connect to the Python socket on launch.

---

## Usage

### Start training (24/7)

```bash
uv run python scripts/train.py
```

Runs as a background process. To run as a persistent systemd service:

```bash
sudo cp scripts/balatro-trainer.service /etc/systemd/system/
sudo systemctl enable balatro-trainer
sudo systemctl start balatro-trainer
sudo systemctl status balatro-trainer
```

Training logs are written to `logs/trainer.log` with automatic rotation.

### Launch dashboard

```bash
uv run streamlit run src/dashboard/app.py
```

Opens at `http://localhost:8501`. Auto-refreshes every 30 seconds during active training.

### Record a human gameplay session

Press `Ctrl+Shift+R` in-game to toggle human recording mode. A notification will confirm recording is active. The session streams to port 12346 and is ingested asynchronously by the training process without interrupting self-play.

```bash
# View recent human sessions and their quality scores
uv run python scripts/record_human.py --list
```

### Run tests

```bash
uv run pytest
```

---

## Project Structure

```
balatro-ml/
├── mod/                        # Steamodded Lua mod
│   ├── balatro_ml.json         # mod manifest
│   ├── bridge.lua              # socket connection + game event hooks
│   └── state.lua               # game state serialisation
│
├── src/
│   ├── env/
│   │   ├── socket_bridge.py    # async TCP listener, parses JSON from Lua
│   │   ├── gymnasium_env.py    # Gymnasium environment wrapper
│   │   ├── observation.py      # Pydantic schemas + tensor conversion
│   │   ├── action_space.py     # action masking, phase-aware action sets
│   │   └── reward.py           # reward function
│   ├── agent/
│   │   ├── policy.py           # transformer policy network (PyTorch)
│   │   ├── trainer.py          # PPO + imitation learning training loop
│   │   └── curriculum.py       # curriculum stage definitions + promotion logic
│   ├── data/
│   │   ├── database.py         # SQLite interface (runs, antes, hands)
│   │   ├── normalise.py        # string → int mappings matching Lua lookup tables
│   │   └── replay_buffer.py    # prioritised experience replay
│   └── dashboard/
│       └── app.py              # Streamlit dashboard
│
├── scripts/
│   ├── train.py                # entrypoint: start training loop
│   ├── dashboard.py            # entrypoint: launch dashboard
│   └── record_human.py         # entrypoint: human session tools
│
├── tests/
│   ├── test_socket.py
│   ├── test_env.py
│   └── test_reward.py
│
├── data/
│   ├── runs.db                 # SQLite training history (gitignored)
│   └── checkpoints/            # model checkpoints (gitignored)
│
├── logs/                       # training logs (gitignored)
├── dev-log.md                  # running development notes
├── .mise.toml                  # Python version pin
├── .python-version             # fallback version pin
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Observation Schema

### Design Principles

- All card and joker properties are surfaced as flat integer or boolean fields for direct tensorisation
- Cards use a monolithic array with `in_hand` / `in_deck` booleans rather than separate hand/deck arrays
- Variable-length arrays (cards, jokers, consumables, shop items) are handled via attention masking in the transformer policy
- Game state scalars are concatenated as a fixed-length context vector
- The full observation is populated differently depending on game phase (playing vs. shop)

---

### Card

All playing cards — whether in hand or remaining in deck — share a single schema. Location is tracked via boolean flags.

```python
CARD = {
    "suit":         int,   # 0=none (stone card), 1=spade, 2=club, 3=heart, 4=diamond
    "value":        int,   # 0=none (stone card), 2-13=standard, 14=ace
    "enhancement":  int,   # 0=none,  1=bonus,  2=mult,   3=wild,  4=glass,
                           # 5=steel, 6=stone,  7=gold,   8=lucky
    "edition":      int,   # 0=none, 1=foil, 2=holo, 3=poly
    "seal":         int,   # 0=none, 1=gold, 2=red, 3=blue, 4=purple
    "debuffed":     bool,  # True if boss blind has disabled this card's effects
    "selected":     bool,  # True if currently selected; always False for deck cards
    "in_hand":      bool,  # True if currently drawn into hand
    "in_deck":      bool,  # False if permanently removed from the run
}
```

**Special cases:**

- Stone cards: `suit=0, value=0, enhancement=6` — rank and suit are meaningless
- Wild cards: `suit` reflects native suit; wildness is encoded in `enhancement=3`
- Debuffed wild cards revert to native suit for hand evaluation purposes
- Ace is encoded as `value=14`; ace-low straights (A-2-3-4-5) must be learned from experience

---

### Joker

```python
JOKER = {
    "id":           int,    # 0-indexed from a fixed lookup table of all 150+ jokers
                            # the agent learns an embedding per ID through experience
    "edition":      int,    # 0=none, 1=foil, 2=holo, 3=poly, 4=negative
    "eternal":      bool,   # cannot be sold
    "perishable":   bool,   # loses retrigger after 5 antes
    "rental":       bool,   # costs $1 per round to keep
    "sell_value":   int,    # current sell value in dollars
    "counter":      float,  # current value of any scaling accumulator (0.0 if unused)
                            # e.g. Ride the Bus streak, Fibonacci mult, Green Joker count
    "target_id":    int,    # joker being copied by Blueprint or Brainstorm; -1 if none
}
```

**Notes:**

- Joker order in the array is meaningful — Blueprint copies the joker immediately to its right, Brainstorm copies the leftmost joker. Do not shuffle.
- Maximum 5 joker slots by default; expandable via certain vouchers.

---

### Consumable

```python
CONSUMABLE = {
    "id":   int,  # maps to appropriate lookup table per type
    "type": int,  # 0=tarot, 1=planet, 2=spectral
}
```

---

### Shop Item

```python
SHOP_ITEM = {
    "type":         int,  # 0=joker, 1=tarot, 2=planet, 3=spectral,
                          # 4=playing_card, 5=voucher, 6=booster_pack
    "id":           int,  # maps to the appropriate lookup table for the given type
    "cost":         int,  # current price in dollars
    "edition":      int,  # for jokers and playing cards; 0 for others
    "enhancement":  int,  # for playing cards only; 0 for others
    "seal":         int,  # for playing cards only; 0 for others
}
```

---

### Full Observation

```python
observation = {

    # All playing cards (hand + deck combined)
    "cards": [CARD, ...],

    # Active jokers in slot order — position is strategic
    "jokers": [JOKER, ...],

    # Held consumables
    "consumables": [CONSUMABLE, ...],

    # Shop contents (populated during shop phase only)
    "shop": {
        "items":       [SHOP_ITEM, ...],
        "reroll_cost": int,
    },

    # Game state scalars
    "game_state": {
        "ante":               int,   # 1-8
        "blind":              int,   # 0=small, 1=big, 2=boss
        "blind_name":         str,   # boss blind name for lookup
        "chips_needed":       int,
        "chips_scored":       int,
        "hands_remaining":    int,
        "discards_remaining": int,
        "money":              int,
        "hand_size":          int,
        "joker_slots":        int,
        "consumable_slots":   int,
        "hand_levels": {
            0:  int,  # High Card
            1:  int,  # One Pair
            2:  int,  # Two Pair
            3:  int,  # Three of a Kind
            4:  int,  # Straight
            5:  int,  # Flush
            6:  int,  # Full House
            7:  int,  # Four of a Kind
            8:  int,  # Straight Flush
            9:  int,  # Royal Flush
            10: int,  # Five of a Kind
            11: int,  # Flush House
            12: int,  # Flush Five
        },
    },

    # Current game phase
    "phase": str,  # "playing" | "shop" | "blind_select"

    # Event that triggered this state update
    "event": str,  # "draw" | "hand_played" | "discard" | "blind_start" |
                   # "shop_open" | "shop_buy" | "shop_close" |
                   # "run_win" | "run_lose"
}
```

---

### Tensor Representation

| Component            | Shape    | Notes                                     |
| -------------------- | -------- | ----------------------------------------- |
| `cards`              | `(N, 9)` | N = total cards in run (hand + deck)      |
| `jokers`             | `(J, 8)` | J = active joker count (≤ joker_slots)    |
| `consumables`        | `(C, 2)` | C = held consumables (≤ consumable_slots) |
| `shop.items`         | `(S, 6)` | S = shop items (0 during playing phase)   |
| `game_state` scalars | `(26,)`  | flattened fixed-length vector             |

Variable-length arrays are padded to their maximum size and masked in the transformer attention layers so padding tokens do not contribute to attention weights.

---

## Agent Design

### Policy Network

A transformer-based policy network with two heads:

- **Play head** — selects which cards to play or discard during the playing phase
- **Shop head** — selects what to buy, sell, skip, or reroll during the shop phase

The shared transformer backbone attends jointly over cards and jokers, learning to represent joker synergies as contextual relationships rather than independent values.

### Training

- **Algorithm**: PPO (Proximal Policy Optimisation) via Stable-Baselines3
- **Parallelism**: 24 concurrent headless Balatro instances via `SubprocVecEnv`
- **Curriculum**: Ante range and stake level increase as win rate improves
- **Imitation learning**: Human gameplay sessions are ingested alongside self-play with 2x priority weighting
- **Replay**: Prioritised experience replay, upsampling transitions with high TD error

### Reward Function

```python
reward = log(chips_scored + 1)           # log-transformed to compress score range
       + 2.0 * log(margin_over_blind)    # beat blinds by larger margins
       + 0.5 * hand_type_level_gain      # reward levelling up hands
       + 0.1 * deck_size_reduction       # reward deck thinning
       + 5.0 * log(final_score + 1)      # large terminal reward at run end
```

### Curriculum Stages

| Stage | Ante Range | Stake | Promotion Threshold |
| ----- | ---------- | ----- | ------------------- |
| 1     | 1–2        | 1     | 70% win rate        |
| 2     | 1–4        | 1     | 70% win rate        |
| 3     | 1–6        | 2     | 65% win rate        |
| 4     | 1–8        | 4     | 60% win rate        |
| 5     | 1–8        | 8     | ongoing             |

---

## Database Schema

Three tables track performance at different granularities:

**`runs`** — one row per completed game. Records final score, ante reached, deck, stake, jokers held, and dominant hand type.

**`ante_events`** — one row per blind beaten or lost. Records score achieved, chips needed, hands and discards used, and joker snapshot.

**`hand_events`** — one row per hand played. Records hand type, level, chips scored, base chips/mult, final chips, and which jokers triggered.

---

## Dashboard

Live Streamlit dashboard at `localhost:8501` tracking:

- Total runs, total hands, all-time high score, mean score, win rate
- Score distribution histogram (per run)
- Score progression over training time (scatter + rolling mean)
- Score by ante (box plot, coloured by small/big/boss)
- Score distribution per hand played (log scale)
- Mean score and play frequency per hand type (side-by-side bar charts)
- Best run ever — hand-by-hand chip breakdown

---

## Human Gameplay Ingestion

Press `Ctrl+Shift+R` in-game to toggle human recording. Sessions stream to port 12346 and are ingested by the training process without interrupting self-play workers.

Human sessions are weighted relative to the agent's current baseline:

| Session quality             | Weight |
| --------------------------- | ------ |
| Score > 1.5× agent baseline | 3.0×   |
| Score > 1.0× agent baseline | 2.0×   |
| Score > 0.5× agent baseline | 1.0×   |
| Score < 0.5× agent baseline | 0.3×   |

This means early in training almost all human gameplay is upweighted. Once the agent surpasses human performance, only exceptional runs contribute meaningful signal.

---

## Hardware

Developed and trained on an Intel i5-1340P mini PC (12 cores, 16GB RAM). Recommended concurrent game instances: **24**. Estimated throughput: ~45,000 games per day (~13.5M training steps/day).

Monitor CPU temperature during sustained training:

```bash
watch -n 2 sensors
```

If temperatures exceed 85°C sustained, reduce concurrent instances or add active cooling.

---

## Lookup Tables

The following entity types are referenced by integer ID and require fixed lookup tables in `src/data/normalise.py`:

- **Joker IDs** — all 150+ base game jokers, 0-indexed
- **Boss blind types** — all boss blind variants
- **Tarot IDs** — all 22 tarot cards
- **Planet IDs** — all 13 planet cards (one per hand type)
- **Spectral IDs** — all spectral cards
- **Voucher IDs** — all vouchers

These tables also serve as the embedding index for the transformer's entity embedding layers.

---

## Development Log

See `dev-log.md` for a running record of decisions, experiments, and findings during development.

---

## Phase Notes

The observation is fully populated during the **playing phase**. During the **shop phase**, `in_hand` cards reflect end-of-round state, `hands_remaining` and `discards_remaining` are 0, and `shop.items` is populated. The policy network uses a shared transformer backbone with separate heads for each phase.

---

## Open Questions

- **Discard pile visibility**: Cards in the discard pile are not currently surfaced. May be relevant for tracking which cards have been played and estimating what will be drawn next.
- **Ace dual encoding**: Ace as 14 may cause the agent to struggle with ace-low straights early in training. A separate `is_ace` boolean may be added if this becomes a training bottleneck.
- **Multi-counter jokers**: A small number of jokers maintain more than one internal counter. The single `counter` field covers the majority; a `counter_2` field may be added later.
- **Booster pack contents**: Surfacing expected pool composition during shop phase could improve pack-buying decisions.
