# Architecture Overview

This document equips agents (human or AI) with a rapid, comprehensive understanding of the codebase's architecture, enabling efficient navigation and effective contribution from day one. **Update this document as the codebase evolves.**

This is a research project to train a reinforcement-learning agent toward mastery of the poker roguelike _Balatro_. It is **not** a web application — it is a fast Rust game simulator paired with a Python RL learner. The two are deliberately separated by a hard language/process boundary (see §2 and §6), because the parts have opposite performance and ecosystem needs: the simulator must run millions of steps per second (Rust), while the learner depends on the mature RL/PyTorch ecosystem (Python).

---

## 1. Project Structure

High-level overview of the directory layout, categorised by architectural layer. The two top-level layers — `game/` (Rust) and `agent/` (Python) — both live under `/src` and communicate across a single batched FFI boundary.

```
[Project Root]/
├── src/
│   ├── game/                  # RUST WORKSPACE — the fast layer (≈ refactor of balatro-rs/core)
│   │   ├── rules/             # Authoritative game rules & state (the single source of truth)
│   │   │   ├── state          # GameState: deck, hand, HELD jokers (+ order & internal
│   │   │   │                  #   state), consumable slots, money, ante, blind, hand levels
│   │   │   ├── card           # Card type: rank, suit + Enhancement / Seal / Edition enums (DATA)
│   │   │   ├── jokers          # Joker catalog (the 150 definitions) + effect impls + shop gen
│   │   │   ├── consumables     # Tarot / Planet / Spectral: catalog + use-effects + shop gen
│   │   │   ├── bosses          # Boss-blind modifiers  (NEW — port from /calculator fork)
│   │   │   └── calc            # Scoring PIPELINE & order of operations; invokes joker hooks
│   │   │                       #   AND enhancement/seal/edition effects; reads hand levels
│   │   ├── sim/               # Transition fn: apply(action) -> state'; legality enforcement;
│   │   │                      #   run loop, stage machine, shop. Agent proposes; sim disposes.
│   │   ├── solver/            # Tactical optimiser (Layer 1): searches plays/discards via calc.
│   │   │                      #   Greedy now → expectimax-over-draw later. Pure & stateless.
│   │   ├── env/               # RL wrapper: reset / step / legal-mask + REWARD + OBSERVATION
│   │   │                      #   ENCODER (state -> feature vector w/ card & joker identity
│   │   │                      #   + solver eval). Vectorised. Exposes pyo3 bindings to Python.
│   │   ├── tests/             # Rust unit + full-game integration tests
│   │   └── Cargo.toml         # Rust workspace manifest
│   │
│   └── agent/                 # PYTHON — the learner (replaces balatro-rs/pylatro/gym)
│       ├── policy/            # Neural policy/value networks (MaskablePPO / masked CleanRL PPO)
│       ├── train/             # Rollout orchestration, curriculum control, hyperparameters
│       ├── store/             # ("mem") Run telemetry, eval datasets, BC/offline data.
│       │                      #   NOT consulted by the on-policy PPO update loop (see §3.2.4).
│       ├── eval/              # Held-out-seed win rates; scorer-vs-calculator oracle checks
│       └── pyproject.toml     # Python dependencies and scripts
│
├── engine/                    # Vendored fork of balatro-rs (reference / source material)
├── calculator/                # Vendored fork of balatro-calculator (oracle + porting source)
├── docs/                      # Project documentation
├── scripts/                   # Automation (build, train launchers, data seeding)
├── .github/                   # CI/CD configuration
├── .gitignore
├── README.md                  # Project overview and quick start
└── ARCHITECTURE.md            # This document
```

---

## 2. High-Level System Diagram

Data flows in a single loop: the Python learner proposes batched actions, the Rust environment advances all simulators in lockstep and returns batched observations + rewards + legal masks, and the learner updates its policy. The language boundary is crossed **once per batch**, not once per step.

```
                         ┌──────────────────────── src/agent (Python) ───────────────────────┐
                         │                                                                    │
   ┌─────────┐  obs/reward/mask (batched)   ┌──────────────┐  advantages   ┌──────────────┐   │
   │         │ ───────────────────────────▶ │   train/     │ ────────────▶ │   policy/    │   │
   │ src/game│                              │  (rollouts,  │               │ (MaskablePPO)│   │
   │  /env   │ ◀─────────────────────────── │  curriculum) │ ◀──────────── │   nets       │   │
   │ (pyo3)  │   actions (batched)          └──────┬───────┘   action dist └──────────────┘   │
   └────┬────┘                                     │                                          │
        │                                          ▼ (async, off the hot loop)                │
        │                                   ┌──────────────┐        ┌──────────────┐          │
        │                                   │   store/     │        │    eval/     │          │
        │                                   │ (telemetry,  │        │ (held-out    │          │
        │                                   │  BC data)    │        │  seeds)      │          │
        │                                   └──────────────┘        └──────┬───────┘          │
        │                                                                  │                  │
        └──────────────────── src/game (Rust) ────────────────────────────┼──────────────────┘
                                                                           │
   sim ──uses──▶ calc ◀──uses── solver          calculator/ ──oracle──────▶┘ (scorer cross-check)
    │             ▲                                                          (offline only)
    │             │ invokes hooks
   rules/state ──▶ jokers / consumables / bosses / card-effects
```

Key architectural boundaries:

- **Agent proposes, sim disposes.** The learner never mutates game state; it emits an `Action` index, and `sim` validates legality and applies the transition. `rules/state` is the only source of truth.
- **One scorer, two consumers.** `calc` is called by `sim` (to adjudicate the real score) and by `solver` (to evaluate candidate plays). It is never duplicated.
- **The observation encoder is the make-or-break seam.** It lives in `env` and converts `GameState` into the neural feature vector. It must encode card and joker _identity_ (not just counts) — the absence of this in the reference engine is the root cause of the classic "always plays high card" failure (see §9).
- **`store` is not the learning substrate.** On-policy PPO learns from the current rollout batch, not from an archive of past runs (see §3.2.4).

---

## 3. Core Components

### 3.1. Game Layer (`src/game`, Rust)

**Name:** Balatro Simulator + Tactical Solver + RL Environment

**Description:** The complete, fast, headless game. Implements the rules, the run loop (antes, blinds, shop, economy), scoring, the 150-joker system, consumables, and boss modifiers. Provides an exhaustive legal-move generator and a fixed-size binary action mask for RL. Wraps all of this in a vectorised Gymnasium-style environment exposed to Python via pyo3.

**Sub-modules and their single responsibilities:**

- `rules/state` — authoritative `GameState`. Holds deck, current hand, held jokers (with order and per-joker internal state), consumable slots, money, ante/blind, and hand levels.
- `rules/card` — the `Card` type. Rank, suit, and the `Enhancement` / `Seal` / `Edition` enums as **data fields** (their _behaviour_ lives in `calc`).
- `rules/jokers` — the joker **catalog** (all 150 definitions and their effect callbacks) plus shop generation. Effects register hooks (`on_play`, `on_score`, `on_handrank`, `on_modify_hand`) into the `calc` pipeline.
- `rules/consumables` — Tarot / Planet / Spectral catalog, their use-effects, and shop generation. Planets modify hand levels, which live in `rules/state` and are read by `calc`.
- `rules/bosses` — boss-blind modifiers (e.g. forced card counts, suit debuffs, discards). **New work**, ported from the `calculator/` fork.
- `rules/calc` — the scoring **pipeline** and its order of operations (the thing that makes joker order matter): base hand → per-card scoring → enhancement/seal/edition effects → joker hooks → final `chips × mult`. Uses big-number arithmetic for late-game scores.
- `sim` — the transition function and stage machine. Validates and applies actions; runs the full game loop. Sole enforcer of legality.
- `solver` — the **tactical** layer (Layer 1). Given a hand, jokers, remaining hands/discards, target, and boss effect, searches play/discard subsets (scored via `calc`) and returns the best. Greedy initially; expectimax over the next draw later. Pure and stateless.
- `env` — the RL boundary. `reset` / `step` / legal-mask, the **reward function**, and the **observation encoder**. Vectorised (batched `step`) and exposed via pyo3.

**Technologies:** Rust, pyo3 (Python bindings), serde. Workspace structure mirrors the cloned `balatro-rs` (`core` → `rules`).

### 3.2. Agent Layer (`src/agent`, Python)

#### 3.2.1. `policy`

**Name:** Policy / Value Networks

**Description:** The neural networks that map an observation to an action distribution and a value estimate. Uses **MaskablePPO** (SB3-contrib) or a CleanRL masked-PPO variant, with the legal-action mask supplied by `env` applied before sampling so illegal actions are never chosen.

**Technologies:** Python, PyTorch, Stable-Baselines3 / SB3-contrib (or CleanRL).

#### 3.2.2. `train`

**Name:** Training Orchestrator

**Description:** Drives rollouts against the vectorised `env`, computes advantages, runs PPO updates, and controls the **curriculum** (`ante_end`, joker subset, run length) that escalates difficulty as the agent improves.

**Technologies:** Python, PyTorch.

#### 3.2.3. `eval`

**Name:** Evaluation & Oracle Harness

**Description:** Measures win rate on held-out seeds (generalisation, not memorised RNG) and runs the **scorer oracle check** — feeding identical hand/joker/enhancement scenarios to `calc` and to the vendored `calculator/` and diffing the scores. Because the RL reward _is_ the score, a scoring bug trains a wrong policy; this harness catches it.

**Technologies:** Python.

#### 3.2.4. `store` (formerly "mem")

**Name:** Run Store

**Description:** Persists run telemetry, training curves, and offline datasets (e.g. behavioural-cloning data, expert/solver trajectories). **Important:** this is _not_ what PPO learns from. On-policy PPO updates from the current rollout batch and discards it; it does not query an archive of all past runs. `store` exists for telemetry, evaluation, BC bootstrap, and reproducibility. (If a future AlphaZero/MuZero-style planning layer is added, it would keep a _sliding replay window_ — still not "all runs forever.")

**Technologies:** Python; flat files / Parquet / SQLite (TBD — see §4).

---

## 4. Data Stores

### 4.1. Run Store

**Name:** Run telemetry & offline datasets

**Type:** TBD — flat files (JSONL/Parquet) or SQLite for run logs; checkpoint files for model weights.

**Purpose:** Stores per-run action histories, outcomes, and metrics for analysis; offline datasets for BC bootstrap; held-out seed lists for evaluation.

**Key collections:** `runs` (seed, actions, outcome, final score, jokers held), `metrics` (win rate, ante reached over training), `checkpoints` (policy weights).

### 4.2. Model Checkpoints

**Name:** Policy/value weights

**Type:** PyTorch checkpoint files (`.pt`), versioned on disk.

**Purpose:** Resumable training and reproducible evaluation.

---

## 5. External Integrations / APIs

**Vendored source repos (not runtime dependencies):**

- **`engine/` — fork of `balatro-rs`.** Reference implementation; `src/game` is its refactor and extension.
- **`calculator/` — fork of `balatro-calculator`.** Used **offline only** as (a) a scoring **oracle** for cross-checking `calc`, and (b) a **porting source** for joker effects, enhancements/seals/editions, and boss modifiers (`cards.js`, `breakdown.js`, `structured-data.jsonld`). Its browser/web-worker JS is _not_ called from the training loop.

**Optional future integration:**

- **`balatrobot` (Steamodded API)** — bridge a trained policy to the _real_ game for final validation only. Never a training substrate.

---

## 6. Deployment & Infrastructure

**Target:** Single Linux desktop (local research). No cloud services required.

**Build:** Cargo for `src/game` (with the `python` pyo3 feature); the build produces a Python-importable extension consumed by `src/agent`.

**Compute:** Environment stepping on CPU (vectorised Rust); neural updates on local GPU (CUDA via PyTorch). Throughput is dominated by env steps (Rust-accelerated) and GPU matmuls (same kernels regardless of host language), which is why the Python learner costs ~nothing once batched.

**CI/CD:** GitHub Actions — `cargo test` for `src/game`, `pytest` for `src/agent`, and the scorer-oracle check as a regression gate.

**Monitoring & Logging:** Training curves via TensorBoard / Weights & Biases (TBD); the `store` layer for run-level telemetry.

---

## 7. Security Considerations

Not a networked or multi-user system; standard application-security concerns are largely out of scope. Relevant integrity concerns instead:

- **Legality enforcement.** The agent must only ever influence state through validated `Action`s; `sim` is the sole authority. This prevents the policy from learning to exploit states the real game would never permit.
- **Scoring correctness.** Because reward derives from score, `calc` correctness is integrity-critical and is gated by the `calculator/` oracle check (§3.2.3).
- **Determinism / seeding.** Runs must be reproducible from a seed for valid evaluation and debugging.

---

## 8. Development & Testing Environment

**Local setup:** Build `src/game` with Cargo (pyo3 `python` feature enabled), install `src/agent` from `pyproject.toml`, then run a smoke training job. (Detailed steps → `CONTRIBUTING.md`.)

**Testing frameworks:** `cargo test` (Rust unit + full-game integration: random-valid-move playthroughs that must reach `Stage::End` without error); `pytest` (Python); the scorer-vs-calculator oracle as a cross-language regression test.

**Code quality:** `clippy` + `rustfmt` (Rust); `ruff` / `black` (Python).

---

## 9. Future Considerations / Roadmap

**Known priorities (highest leverage first):**

1. **Observation encoder (critical).** Replace the reference engine's scalar-counts observation with a feature vector encoding card and joker _identity_ plus the solver's build evaluation. This is the direct fix for the "always plays high card" failure — a card-blind observation makes good hand selection mathematically impossible.
2. **Batched pyo3 `step`.** Cross the FFI boundary once per batch of environments, not once per step (EnvPool/Madrona pattern).
3. **Swap tabular Q-learning for masked PPO.** The reference learner is a non-scaling Q-table; replace entirely.
4. **Joker effect audit & completion.** ~120 joker types are scaffolded in the engine but effect-completeness varies; port/complete from the `calculator/` fork.
5. **Port boss modifiers, enhancements, seals, editions** from the `calculator/` fork to close the realism gap.
6. **Tactical solver depth.** Greedy → expectimax-over-draw.
7. **Planning layer (research).** AlphaZero/MuZero-style search (information-set / determinized MCTS for stochasticity) on top of the PPO policy for true mastery.

**Known architectural debt / risks:** engine implements only a subset of jokers/effects today; stochasticity and partial observability make the planning layer genuinely hard; open empirical question whether reactive PPO plateaus below search-based play.

---

## 10. Project Identification

**Project Name:** _(TBD — e.g. "Balatro RL")_

**Repository URL:** _(TBD)_

**Primary Contact/Team:** _(TBD)_

**Date of Last Update:** 2026-06-24

---

## 11. Glossary / Acronyms

- **Ante:** A round-group in Balatro; the run progresses through antes 1–8, each containing Small, Big, and Boss blinds.
- **Blind:** A score target to clear within a limited number of hands. Small / Big / Boss.
- **Boss blind:** A blind with a special modifier rule (e.g. forces 5-card plays, debuffs a suit).
- **Joker:** A held card (up to 5 slots) whose effect modifies scoring; the core of build strategy. ~150 exist.
- **Enhancement / Seal / Edition:** Optional attributes on a standard card (Gold/Steel/Glass…; Red/Blue/Gold/Purple; Foil/Holo/Polychrome).
- **Consumable:** Tarot / Planet / Spectral card held in consumable slots and actively used.
- **Hand level:** Per-hand-type upgrade (raised by Planet cards) that increases that hand's base chips/mult; stored in `GameState`.
- **calc / scoring pipeline:** The ordered computation `chips × mult` that makes joker order significant.
- **solver (Layer 1):** The tactical optimiser that picks the best play/discard for a given state.
- **Observation encoder:** Converts `GameState` into the neural feature vector. The critical seam (§9.1).
- **Legal-action mask:** Fixed-size binary vector marking which action indices are valid; applied before sampling.
- **PPO / MaskablePPO:** Proximal Policy Optimization, the on-policy RL algorithm; "Maskable" applies the legal mask.
- **On-policy:** Learns only from data generated by the current policy (hence `store` is not the learning substrate).
- **BC (Behavioural Cloning):** Supervised pretraining of the policy from expert/solver trajectories.
- **pyo3:** The Rust↔Python FFI bridge used to expose `src/game/env` to `src/agent`.
- **Oracle check:** Cross-validating `calc` scores against the vendored `calculator/` to catch scoring bugs.
