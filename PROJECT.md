# HANDOFF — Balatro RL

## 0. Orient yourself in 5 minutes

1. **Goal:** train an RL agent toward _mastery_ of Balatro (clearing ante 8, ideally well beyond).
2. **The whole design exists to defeat one failure mode** (see §2). If you understand that failure, every architectural decision follows.
3. **Layers:** a fast Rust simulator (`src/game`) and a Python learner (`src/agent`), separated by a batched pyo3 boundary. Read `ARCHITECTURE.md` §1–§2.
4. **Current state:** scaffold only — modules stubbed, `cargo check` passes, nothing trains yet (see §5).
5. **Next artifact:** the observation encoder spec + impl in `src/game/env` (see §6, item 1). This is the highest-leverage file in the project. Do not get pulled into porting jokers first.
6. **Before changing a "settled decision" (§4), stop and flag it** — those were reasoned through deliberately; reopening them silently will cost days.

---

## 1. What we're building and why

Balatro is a poker roguelike: you play poker hands to clear score targets ("blinds"), and between blinds you visit a shop to buy **jokers** (up to 5 held; ~150 exist) that transform how hands score, plus consumables, vouchers, and card upgrades. A run is antes 1–8; mastery means building a joker "engine" whose score scales fast enough to beat exponentially rising targets.

**Success criterion:** a policy that wins runs on _held-out seeds_ (not memorised RNG) at a meaningful rate, evaluated by `src/agent/eval`.

The hard part of Balatro is **not** playing a single hand well — that's a solvable optimisation (see the tactical solver, §3). The hard part is the long-horizon strategic layer: which blinds to skip, what to buy, which build to commit to, how to manage economy. That is where learning is pointed.

---

## 2. THE root-cause insight (the reason this project is shaped the way it is)

A prior attempt **always played a high card and lost the first blind**, no matter how much it trained. It also crashed from running multiple instances of the real game on limited RAM.

Both trace to **one mistake: training against the live game with an impoverished signal.** Decomposed:

- **Card-blind observation → guaranteed degeneracy.** If the policy's observation does not contain _which_ cards are in hand and _which_ jokers are held, it is mathematically impossible to learn to select a good poker hand. The best a card-blind policy can do is a fixed prior over "select N cards and play," which collapses to the simplest stable action — a high card. **The forked reference engine's Gym env has exactly this flaw**: its observation is scalar _counts_ (`available_len`, `jokers_len`, …) with zero card or joker identity. That observation was dumbed down to fit a **tabular Q-learning** agent (the obs tuple is a Q-table key). Both the observation and the algorithm are dead ends and are being replaced.
- **Sparse terminal reward → no gradient.** Win/lose-only reward is constant across episodes that always lose → zero gradient → the policy never moves off its initialisation. Fix: **dense reward on chips scored per hand** (the reference env already does `score_diff/100`, which is correct; it just didn't matter while the agent was card-blind).
- **Live game → RAM + throughput death.** Real game instances are hundreds of MB each and run at human speed; RL needs 10^6–10^8 steps. Fix: train against a **fast headless Rust sim**, vectorised in-process (KB per env, millions of steps/sec).

**The single most important lesson, confirmed by the one published success** (a PPO agent with an ~814-dim state and 17+ run wins): **engineer the observation richly** — encode joker identity/fingerprints, explicit hand evaluation, economy, and boss state — so the network learns _strategy on top of a rich representation_ instead of rediscovering poker from scratch.

**Corollary for you:** if anything you build leaves the agent unable to see its cards or jokers, it is wrong, regardless of how clean it looks.

---

## 3. The layered design

| Layer                             | Lives in               | Learned?         | Responsibility                                                                                                                                                                   |
| --------------------------------- | ---------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0. Simulator**                  | `src/game/{rules,sim}` | No               | Authoritative game state + rules + run loop + legal-move generation.                                                                                                             |
| **1. Tactical solver**            | `src/game/solver`      | No (it's search) | Given a state, pick the best play/discard. Balatro scoring is exact and computable, so this is solved by enumeration + scoring, not RL. Greedy now → expectimax-over-draw later. |
| **2. Strategic policy**           | `src/agent`            | **Yes (PPO)**    | The brain: blind skip/select, shop buys/sells, joker ordering, consumable use. This is what learns.                                                                              |
| **3. Planning (future/research)** | `src/agent`            | Yes              | AlphaZero/MuZero-style search over strategic decisions for true mastery. Stochastic → needs info-set / determinized MCTS. Not now.                                               |

**Why this decomposition matters:** handing the tactical layer to a solver means the agent reliably _survives_ blinds it can survive, so the strategic learner finally sees the consequences of its shop decisions instead of dying in blind 1 forever. It converts an impossible credit-assignment problem into a hard-but-learnable one.

---

## 4. Settled decisions — do NOT silently relitigate

These were reasoned through. If you think one is wrong, **raise it explicitly with your reasoning**; don't quietly build against the alternative.

1. **Rust env + Python learner, bridged by a _batched_ pyo3 interface.** Rust for the part that runs millions of times/sec; Python because the entire mature RL ecosystem (MaskablePPO, CleanRL, reference impls) lives there. Cross the FFI boundary **once per batch of environments**, not once per step (EnvPool/Madrona pattern). All-Rust learning was considered and rejected: payoff is thin (throughput is dominated by env steps + GPU matmuls, identical underneath) and the debugging cost is high.
2. **The calculator fork is offline-only.** `balatro-calculator` is browser JS; it is **never** called in the training loop. It serves two offline roles: (a) a **scoring oracle** to cross-check `calc`, and (b) a **porting source** for joker effects, enhancements/seals/editions, and boss modifiers. Do not attempt a runtime JS bridge.
3. **`calc` and `jokers` are coupled by a hook interface, not separable.** Jokers _are_ scoring logic. There is no "score a hand" that doesn't know your jokers. `calc` owns the scoring **pipeline + order of operations**; effect modules (`jokers`, `consumables`, `bosses`, card enhancements) **register hooks into it**. `calc` depends on the hook _trait_, not on the joker modules (this also prevents a circular dependency — see §7).
4. **Enhancements / Seals / Editions are card _data_, not modules.** They are enum fields on the `Card` type (`rules/card`). Their _behaviour_ is a scoring effect handled in `calc`. They do **not** get their own folders.
5. **Consumables (Tarot/Planet/Spectral) are their own module** (`rules/consumables`): catalog + use-effects + shop generation + actions. (Same shape as jokers: catalog + inventory + actions.)
6. **Catalog vs inventory split.** Joker/consumable _definitions_ are immutable **rules** (`rules/jokers`, `rules/consumables`). The _held_ jokers/consumables — order, per-joker accumulated internal state — are **game state** (`rules/state`). A planet's effect raises a **hand level**, which is a field in `rules/state`, read by `calc` (don't make a "leveling" module).
7. **Agent proposes, sim disposes.** The agent never mutates state. It emits an `Action` index; `sim` validates legality (affordability, slots, stage) and applies it. `rules/state` is the single source of truth and `sim` is the sole legality enforcer.
8. **`store` (formerly "mem") is NOT the PPO learning substrate.** On-policy PPO learns from the _current_ rollout batch and discards it. `store` is for telemetry, eval datasets, behavioural-cloning bootstrap data, and reproducibility. (A future planning layer would keep a _sliding replay window_ — still not "all runs forever.")
9. **Single flat Rust crate for now.** `game` with flat modules is fine at this size. **Fault line:** if pyo3 attributes start leaking out of `env` into `rules`/`sim`/`solver`, that's the signal to split `env` into its own crate over a pure `game-core`. Keep pyo3 confined to `env` behind `#[cfg(feature = "python")]` until then.
10. **Masked PPO, not plain PPO, not Q-learning.** The legal-action mask from `env` must be applied before sampling (MaskablePPO / masked CleanRL). The reference tabular Q-learning is replaced entirely.

---

## 5. Current state (update this section as it changes)

**Built (scaffold only — `cargo check` passes, nothing trains yet):**

- `src/game/` — Rust crate `game`, flat modules.
  - `Cargo.toml`: serde + optional `python` (pyo3) feature; `[lib] path = "lib.rs"`.
  - `lib.rs` → `rules sim solver env`.
  - `rules/` → `state card jokers consumables bosses calc`.
  - `tests/integration.rs`.
- `src/agent/` — Python package `agent`.
  - `pyproject.toml` (deps stubbed: `torch` / `sb3-contrib` / `gymnasium` commented out).
  - `policy/ train/ store/ eval/` — each an `__init__.py` with a §3.2 doc-comment.
- Every stub carries a one-line doc-comment citing its `ARCHITECTURE.md` section.
- `CHANGELOG.md` started.

**Not yet present (deliberate — separate steps):**

- `engine/` + `calculator/` forks are **not vendored into the tree yet** (see `STACK.md`). Vendoring approach is TBD: leaning toward **copy-in-and-own** (drop `.git` history) since we're heavily refactoring `balatro-rs` into `src/game` and porting _out_ of the calculator — not tracking upstream. `engine/` effectively _becomes_ `src/game`; `calculator/` shrinks to a reference snapshot + whatever the oracle check needs.
- No real game logic, no observation/reward, no learner, no joker effects audited.

---

## 6. Work queue (ordered by leverage — do them roughly in this order)

1. **Observation encoder spec + impl in `src/game/env` — CRITICAL PATH, DO FIRST.** Map `rules/state` → a fixed-size feature vector that encodes **identity**, not counts:
   - per **hand-card slot**: rank, suit, and (later) enhancement/edition/seal;
   - per **joker slot**: joker identity (one-hot or learned embedding) + order + relevant internal state ("fingerprints");
   - economy (money, interest state), ante/blind, **target/score ratio**, plays/discards left, deck-composition stats, boss encoding;
   - **the solver's evaluation of the current build** (best achievable hand + its score vs next target) — this is the feature that makes the strategic policy understand build strength.
     Output the exact field list, encoding, and total dimensionality. This is the shared contract for both `env` and `policy`; lock it before building either.
2. **Batched pyo3 `step`.** Vector of actions in → vector of (obs, reward, done, mask) out. One boundary crossing per batch.
3. **Reward function in `env`.** Dense chips per hand (normalised by target), + blind-clear bonus, + ante-clear bonus, + large terminal win. Watch auxiliary shaping for reward-hacking; chips-scored is the safe base signal.
4. **Masked PPO learner in `src/agent`.** Wire MaskablePPO to `env`'s mask. Smoke-test on `ante_end = 1` and confirm the agent climbs _off_ high card — that's the green light that the whole pipeline works.
5. **Scorer oracle check (`src/agent/eval`).** Feed identical scenarios to `calc` and the vendored `calculator/`; diff scores. Gate it in CI. **The reward IS the score — a scoring bug trains a wrong policy silently.**
6. **Tactical solver (`src/game/solver`).** Greedy best-hand first; confirm a solver-only agent clears early antes; then expectimax over the next draw.
7. **Joker effect audit + completion.** ~120 joker types are scaffolded in the engine but effect-completeness varies — audit which are real vs name-only stubs; complete from the `calculator/` reference. (Large, absorbing task — resist starting it before items 1–4.)
8. **Port boss modifiers, enhancements, seals, editions** from `calculator/` to close the realism gap.
9. **Curriculum (`src/agent/train`).** Expand `ante_end` 1 → 8; small joker subset → full; single deck → decks/stakes. Domain-randomise over seeds; evaluate on held-out seeds.
10. **(Research) Planning layer.** AlphaZero/MuZero-style search on top of the PPO policy; info-set/determinized MCTS for stochasticity. The open empirical question — whether reactive PPO plateaus below search — is the project's potential novel contribution.

---

## 7. Traps (look reasonable, are wrong)

- **Splitting scoring from jokers.** The most tempting clean boundary; the game won't allow it. Jokers are scoring modifications. `calc` invokes joker hooks. (§4.3)
- **Giving enhancements/seals/editions their own modules.** They're card attributes; effects live in `calc`. (§4.4)
- **Letting the agent mutate joker stacks directly.** It proposes actions; `sim` validates. (§4.7)
- **Treating `store` as what PPO learns from.** It isn't. (§4.8)
- **Training against the real game / spawning game instances.** This is the original RAM + throughput death. Train against the Rust sim only. (§2)
- **Plain PPO without the mask.** It wastes exploration on illegal actions and tends to collapse. (§4.10)
- **Trusting the engine's scorer.** Oracle-check it (§6.5).
- **Circular dependency in `rules/`.** `jokers`/`consumables`/`bosses` register _into_ `calc`, while `calc` invokes effects. Resolve via a hook **trait** defined in `calc`; effect modules implement it and are collected into a registry at scoring time. `calc` must not import the joker modules. Retrofitting this after 50 jokers exist is miserable — get it right before real effect code lands.
- **pyo3 leaking past `env`.** Keep FFI attributes confined to `env`; leakage is the crate-split signal. (§4.9)
- **Disappearing into joker-porting.** It's satisfying and large, but lower-leverage than the observation encoder. The agent learns nothing from a perfect `rules/` if the observation is card-blind. (§6.1)

---

## 8. Conventions

- Every module/stub carries a doc-comment citing its `ARCHITECTURE.md` section. Keep this up as modules grow.
- Maintain `CHANGELOG.md`.
- Rust: `cargo check` / `clippy` / `rustfmt` clean. pyo3 attributes behind `#[cfg(feature = "python")]`, confined to `env`.
- Python: `ruff` / `black`.
- **Determinism:** runs must be seedable for reproducible eval and debugging.
- **Integration tests:** random-valid-move playthroughs must reach `Stage::End` without any `handle_action` error (pattern inherited from the engine fork).
- Pure game logic (`rules`, `sim`, `solver`) must not depend on Python.

---

## 9. Key references

- `ARCHITECTURE.md` — structure, module responsibilities, system diagram, glossary.
- `STACK.md` — the vendored forks.
- `CHANGELOG.md` — what's changed.
- Engine fork source: `evanofslack/balatro-rs` (Rust engine + move generator + pyo3; `core/` → `src/game/rules`). Implements a _subset_ of the game (no boss modifiers / enhancements / tarots / spectrals / skips yet).
- Calculator fork source: `EFHIII/balatro-calculator` (browser JS; exact scorer + optimiser over 150 jokers, enhancements, editions, seals, boss effects, big-number scores). Offline oracle + porting source.
- Guiding empirical lesson: the published ~814-dim PPO agent (17+ wins) succeeded by **engineering the observation** (joker fingerprints, hand evaluation, economy, boss strategy). Card-blind observations fail.

---

## 10. If you only remember three things

1. **The observation must encode card and joker _identity_.** Everything else is downstream of this. (§2, §6.1)
2. **One scorer (`calc`), two consumers (`sim` adjudicates, `solver` evaluates); jokers register hooks into it.** Don't duplicate scoring, don't separate it from jokers. (§4.3)
3. **Train against the fast Rust sim, masked-PPO, dense chip reward; the calculator is an offline oracle; `store` is not the learning substrate.** (§2, §4)
