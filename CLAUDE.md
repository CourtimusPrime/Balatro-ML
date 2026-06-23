<!-- GSD:project-start source:PROJECT.md -->
## Project

**Balatro RL**

A reinforcement-learning system that trains an agent toward *mastery* of Balatro (the poker roguelike) — clearing ante 8 and ideally well beyond, on **held-out seeds** rather than memorised RNG. It pairs a fast headless **Rust simulator** (`src/game`) with a Python **PPO learner** (`src/agent`), bridged by a batched pyo3 boundary. The agent learns the long-horizon *strategic* layer (blind skip/select, shop buys/sells, joker ordering, consumable use), while a non-learned tactical solver handles single-hand play.

**Core Value:** **The observation must encode card and joker *identity*, not counts.** A policy that cannot see which cards are in hand and which jokers are held is mathematically incapable of learning to select a good poker hand — it collapses to "always play a high card." Everything else in the design is downstream of a rich observation. If anything built leaves the agent card-blind or joker-blind, it is wrong regardless of how clean it looks.

### Constraints

- **Architecture**: Rust env + Python learner bridged by a *batched* pyo3 interface (cross FFI once per batch, EnvPool/Madrona pattern) — Rust for the millions-of-steps-per-sec part, Python for the RL ecosystem.
- **Tech stack**: Rust (`game` crate, serde, pyo3 behind `#[cfg(feature = "python")]`); Python (torch, sb3-contrib/MaskablePPO, gymnasium); `ruff`/`black` for Python, `cargo check`/`clippy`/`rustfmt` for Rust.
- **Purity**: pure game logic (`rules`, `sim`, `solver`) must not depend on Python; pyo3 attributes confined to `env`.
- **Determinism**: runs must be seedable for reproducible eval and debugging.
- **Integration tests**: random-valid-move playthroughs must reach `Stage::End` without any `handle_action` error.
- **Conventions**: every module/stub carries an `ARCHITECTURE.md`-citing doc-comment; maintain `CHANGELOG.md`.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Rust** | 1.86+ (stable, 2021 or 2024 edition) | The fast layer: `rules`, `sim`, `solver`, `env`, scoring pipeline | Project decision. Millions of steps/sec; zero-cost abstractions; the only language that makes the in-process vectorised env viable. Edition 2024 is fine on current stable; 2021 is the safe default if any dependency lags. |
| **PyO3** | **0.29.0** | Rust↔Python FFI; exposes `src/game/env` to Python | Current release (2026-06-11). Mature `Bound<'py, T>` API, `IntoPyObject` trait, robust GIL-release (`Python::detach`, formerly `allow_threads`), and free-threaded-Python support since 0.23. Confine behind `#[cfg(feature = "python")]` so `rules`/`sim`/`solver` stay Python-free (constraint §Purity). |
| **rust-numpy** | **0.29.0** | Zero-copy NumPy array interop on the Rust side of the batch boundary | Pinned to PyO3 0.29.0 (released 2026-06-13, the day after PyO3 0.29). `PyArray2<f32>` / `PyReadonlyArray` give you the batched obs/action/reward/mask arrays without per-element copies — the whole point of the EnvPool-style boundary. Uses `ndarray` 0.17 internally. |
| **maturin** | **1.14.1** | Build backend: compiles the Rust cdylib into an importable Python extension | The standard PyO3 build tool. Set as `build-backend` in `src/agent` (or a dedicated `src/game` pyproject) so `pip install` / `uv` builds the extension transparently. Supports editable installs (`maturin develop` / `uv pip install -e`). |
| **PyTorch (torch)** | **2.12.x** (CUDA 12.8 wheels: `cu128`) | Neural policy/value nets + autograd + GPU matmuls | The RL ecosystem's substrate; SB3/sb3-contrib require it. 2.12 ships stable `cu128` wheels (Blackwell-ready) and an experimental `cu132` build. Use `cu128` unless you have a specific CUDA 13.2 need — it is the broadly-tested default. |
| **Gymnasium** | **1.3.0** | RL environment API contract the Python side speaks | Farama's maintained successor to OpenAI Gym; the API SB3 2.9 targets. Your Rust `env` is exposed through a thin Python `gymnasium.vector`-compatible wrapper so SB3 sees a standard vec-env. |
| **sb3-contrib (MaskablePPO)** | **2.9.0** | The masked-PPO learner (Layer 2 strategic policy) | Project decision: masked PPO, not plain PPO, not Q-learning. `MaskablePPO` is the batteries-included, well-tested implementation of invalid-action masking. Released 2026-06-15 alongside SB3 2.9.0 (versions move in lockstep — always match them). |
| **Stable-Baselines3** | **2.9.0** | Base RL framework sb3-contrib extends | Must exactly match sb3-contrib's minor version. Provides the vec-env infra, rollout buffer, and PPO core that MaskablePPO subclasses. |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **serde** + **serde_json** | serde **1.0.228** | (De)serialise game state, joker/calculator data, replay/telemetry | Already a project dep. Use for vendoring the calculator's `structured-data.jsonld` / `cards.js`-derived data and for `store` telemetry export. |
| **rand** | **0.9.x** (pin; see warning) | RNG for deck shuffles, shop generation, boss selection | Determinism constraint. **Use `rand` 0.9, NOT 0.10**, for now — see "What NOT to Use". |
| **rand_chacha** (`ChaCha8Rng`) | matches `rand` (0.9 → `rand_chacha` 0.9) | The seedable, reproducible master PRNG per env | `ChaCha8Rng` is the documented choice for a deterministic master generator. Seed each env from a per-env u64; reproducible eval/debug is a hard constraint. |
| **rayon** | 1.10+ | Data-parallel `step` across the env batch on CPU | The EnvPool-style win: step all N envs in parallel **inside one FFI call** while the GIL is released. Pair with `Python::detach` (GIL release) so Python threads run concurrently. |
| **thiserror** | **2.0.x** | Ergonomic error types in `sim`/`rules` | For typed `handle_action` errors; integration tests assert no error reaching `Stage::End`. Convert to `PyErr` only at the `env` boundary. |
| **ndarray** | 0.17.x (transitive via rust-numpy) | Rust-side array math if needed | Pin to whatever rust-numpy 0.29 re-exports (0.17) to avoid version-mismatch errors at the `PyArray`↔`ArrayView` seam. Prefer the re-export over a direct dep. |
| **TensorBoard** | latest | Training-curve logging | SB3 has built-in TensorBoard support — lowest-friction monitoring. W&B optional later (ARCHITECTURE §6 marks it TBD). |
| **pytest** | 8.x | Python test runner | Constraint. Covers the Python learner + the scorer-oracle cross-check (`eval`). |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| **uv** | **0.11.x** | Python env + dependency manager | Use uv over pip/conda: 10–100x faster, lockfile-based reproducibility, works cleanly with maturin (`uv pip install -e .` or `uv run`). The 2025/2026 default for new Python projects. |
| **ruff** | **0.15.x** | Python linter **and** formatter | Constraint names `ruff` + `black`. Ruff now does both — `ruff format` is a drop-in black replacement. Recommend running `ruff format` and dropping standalone black to avoid two formatters fighting (see "Stack Patterns"). |
| **black** | 25.x (optional) | Formatter | Listed in constraints; redundant with `ruff format`. Keep only if you want black's exact style guarantees; otherwise ruff alone. |
| **cargo fmt / clippy / test** | bundled with Rust | Rust format, lint, test | Constraints. `cargo clippy -- -D warnings` in CI; `cargo test` runs unit + random-valid-move integration playthroughs to `Stage::End`. |
| **GitHub Actions** | — | CI: `cargo test` + `pytest` + scorer-oracle gate | ARCHITECTURE §6. The oracle check (calc vs vendored calculator) is the regression gate. |
## Installation
# --- Python side (src/agent), managed by uv ---
# pyproject.toml uses maturin as build-backend so the Rust env compiles on install.
# Build + install the Rust extension in editable/dev mode
# src/game/Cargo.toml (excerpt)
## The Batched FFI Boundary (the critical seam)
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **sb3-contrib MaskablePPO** | **CleanRL masked PPO** (`CategoricalMasked`, ~40 LOC) | Choose CleanRL if you need to customise the PPO inner loop heavily (e.g. to later bolt on the AlphaZero/MuZero research layer, custom advantage estimation, or unusual masking over multi-categorical action factors). CleanRL is a single-file you own and read top-to-bottom; SB3 hides the loop. **For this project's stated goal (get masked PPO training reliably, smoke-test off "always high card"), start with MaskablePPO** — less code to get right, batteries-included masking, callbacks, checkpointing. Migrate to CleanRL only if SB3's abstractions become a wall. |
| **rust-numpy `PyArray`** | Raw `&[u8]` buffer + manual reshape in Python | rust-numpy is the standard and gives typed, zero-copy, shape-checked arrays. Raw buffers only if you hit an exotic dtype rust-numpy lacks (you won't here — f32/i64/bool cover it). |
| **maturin** | `setuptools-rust` | maturin is the PyO3-native, lower-config choice and the community default. setuptools-rust only if you must integrate into an existing setuptools build. |
| **uv** | pip + venv, or Poetry, or conda | pip/venv is fine and universal; uv is just faster and gives a lockfile. conda only if you need non-PyPI binary deps (you don't — torch wheels cover CUDA). |
| **TensorBoard** | Weights & Biases | W&B for richer experiment tracking / sweeps once training scales; TensorBoard is zero-setup and SB3-native for the first runs. |
| **ChaCha8Rng** | `StdRng`, `SmallRng` | `ChaCha8Rng` for the reproducible master generator (StdRng/SmallRng explicitly opt OUT of cross-version reproducibility — wrong for held-out-seed eval). |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **rand 0.10 (right now)** | rand 0.10 (2026) dropped `Clone` and serde on `StdRng`/`ChaCha{8,12,20}Rng` to prevent key-stream duplication, and changed seeding ergonomics. If your vec-env relies on cloning an RNG to fork per-env streams or serialising RNG state into `store`, 0.10 breaks that pattern. | **Pin `rand = "0.9"` / `rand_chacha = "0.9"`** until you've confirmed your seeding/fork strategy works with 0.10's "reconstruct from key + set stream" approach. Then upgrade deliberately. |
| **Plain `Categorical` without masking** | Settled out-of-scope: wastes exploration on illegal actions and collapses. The whole pipeline depends on the mask. | MaskablePPO (or CleanRL `CategoricalMasked`). |
| **Per-step FFI crossing** | Crossing pyo3 once per env-step is the throughput killer the architecture exists to avoid. | One batched `step` per rollout tick (EnvPool/Madrona pattern). |
| **Returning Python lists/dicts of per-env results** | Re-introduces per-env Python object allocation, undoing the batch. | Pre-allocated `PyArray2`/`PyArray1` filled in Rust. |
| **pyo3 attributes in `rules`/`sim`/`solver`** | Violates the purity constraint; couples the hot path to Python; breaks `cargo test` without the Python feature. | `#[cfg(feature = "python")]` confined to `env`; convert errors to `PyErr` only there. |
| **Mismatched SB3 / sb3-contrib versions** | sb3-contrib subclasses SB3 internals; a minor-version skew causes import/ABI breakage. | Always pin both to the **same** version (2.9.0 / 2.9.0). |
| **Mismatched PyO3 / rust-numpy versions** | rust-numpy is tightly coupled to a specific PyO3 version; mixing (e.g. pyo3 0.29 + numpy 0.28) fails to compile at the trait boundary. | Pin both to **0.29.x**. |
| **conda for torch+CUDA** | Heavier, slower resolves; the official `download.pytorch.org/whl/cu128` wheels are the supported path. | uv/pip with the cu128 index URL. |
| **Calling the calculator JS at runtime** | Settled out-of-scope; browser JS in the training loop is the RAM/throughput death the project rejected. | Port effects into Rust `calc`; use calculator only offline as oracle (`eval`) + porting source. |
## Stack Patterns by Variant
- Use `ruff format` for everything and drop standalone `black`.
- Because ruff implements black-compatible formatting and running both invites churn/conflicts; one tool, one config in `pyproject.toml`.
- Migrate the learner from MaskablePPO to **CleanRL-style owned PPO** (or a custom loop).
- Because search + replay-window + custom value targets need control of the inner loop that SB3 abstracts away. (Out of scope now — noted so the version pins don't lock you in.)
- PyO3 0.29 + rust-numpy 0.29 support it; build with the appropriate ABI tag.
- Because the GIL-free build can let Rust+Python overlap further — but torch/SB3 free-threaded support is still maturing in 2026, so default to standard GIL builds and the `py.detach` GIL-release pattern for now.
- Keep all pyo3/numpy behind `feature = "python"`; expose `rlib` crate-type alongside `cdylib`.
- Because `rules`/`sim`/`solver` tests then compile and run with plain `cargo test` (no maturin, no Python), and the batched-env tests run only when `--features python` is set.
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| pyo3 0.29.x | rust-numpy (numpy crate) 0.29.x | Hard coupling — must match minor. rust-numpy 0.29 released one day after pyo3 0.29 specifically to track it. |
| rust-numpy 0.29 | ndarray 0.17 | rust-numpy re-exports ndarray 0.17; depend via the re-export, don't add a conflicting direct `ndarray` dep. |
| stable-baselines3 2.9.0 | sb3-contrib 2.9.0 | Lockstep — same minor always. |
| sb3-contrib 2.9 / SB3 2.9 | gymnasium 1.x (1.3.0), torch ≥ 2.x | SB3 2.x targets Gymnasium (not legacy Gym) and modern torch. |
| torch 2.12 | CUDA 12.8 (`cu128`) wheels; experimental 13.2 (`cu132`) | Use `cu128` index URL; verify your driver supports the chosen CUDA. CUDA 12.4 wheels were dropped. |
| rand 0.9 | rand_chacha 0.9 | Keep the rand-family versions aligned; do not mix 0.9 and 0.10 across the family. |
| numpy (Python) 2.5 | rust-numpy 0.29 | rust-numpy 0.29 supports NumPy 2.x; the C-ABI is handled by maturin's abi3/build. |
| maturin 1.14 | pyo3 0.29 | Current maturin builds pyo3 0.29 extensions and abi3 wheels without extra config. |
## Sources
- PyO3/pyo3 GitHub Releases — v0.29.0 (2026-06-11) confirmed current; `Python::detach` rename, free-threading since 0.23 — HIGH
- PyO3/rust-numpy GitHub Releases — v0.29.0 (2026-06-13), depends on pyo3 0.29, ndarray 0.17, free-threading since 0.24 — HIGH
- PyO3/maturin GitHub Releases — v1.14.1 (2026-06-19) — HIGH
- pyo3.rs Parallelism + Free-threading user guides — `allow_threads`/`detach` GIL-release pattern, deadlock guidance — HIGH
- PyPI (torch, gymnasium, numpy, ruff, uv) — torch 2.12.1, gymnasium 1.3.0, numpy 2.5.0, ruff 0.15.18, uv 0.11.23 — HIGH
- pytorch.org blog + dev-discuss — 2.12 ships cu128 stable + experimental cu132; cu124 dropped — HIGH
- Stable-Baselines-Team/stable-baselines3-contrib + DLR-RM/stable-baselines3 Releases — both v2.9.0 (2026-06-15), lockstep versioning — HIGH
- sb3-contrib.readthedocs.io (MaskablePPO, master) — vec-env masking constraints (SubprocVecEnv requires in-env action_masks; MaskableEvalCallback) — HIGH
- vwxyzjn/invalid-action-masking + CleanRL paper (JMLR) — CategoricalMasked, ~40 LOC masking approach — MEDIUM (official repo, not version-pinned)
- crates.io API — serde 1.0.228, ndarray 0.17.2, thiserror 2.0.18, rand 0.9/0.10 family, rand_chacha 0.10 — HIGH
- rust-random.github.io Rand Book (Updating to 0.10, Seeding, Reproducibility) — ChaCha8Rng as deterministic master; 0.10 dropped Clone/serde on RNGs — HIGH
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| cavecrew | > Decision guide for delegating to caveman-style subagents. Tells the main thread WHEN to spawn `cavecrew-investigator` (locate code), `cavecrew-builder` (1-2 file edit), or `cavecrew-reviewer` (diff review) instead of doing the work inline or using vanilla `Explore`. Subagent output is caveman-compressed so the tool-result injected back into main context is ~60% smaller — main context lasts longer across long sessions. Trigger: "delegate to subagent", "use cavecrew", "spawn investigator/builder/reviewer", "save context", "compressed agent output". | `.claude/skills/cavecrew/SKILL.md` |
| caveman | > Ultra-compressed communication mode. Cuts token usage ~75% by speaking like caveman while keeping full technical accuracy. Supports intensity levels: lite, full (default), ultra, wenyan-lite, wenyan-full, wenyan-ultra. Use when user says "caveman mode", "talk like caveman", "use caveman", "less tokens", "be brief", or invokes /caveman. Also auto-triggers when token efficiency is requested. | `.claude/skills/caveman/SKILL.md` |
| caveman-commit | > Ultra-compressed commit message generator. Cuts noise from commit messages while preserving intent and reasoning. Conventional Commits format. Subject ≤50 chars, body only when "why" isn't obvious. Use when user says "write a commit", "commit message", "generate commit", "/commit", or invokes /caveman-commit. Auto-triggers when staging changes. | `.claude/skills/caveman-commit/SKILL.md` |
| caveman-compress | > Compress natural language memory files (CLAUDE.md, todos, preferences) into caveman format to save input tokens. Preserves all technical substance, code, URLs, and structure. Compressed version overwrites the original file. Human-readable backup saved as FILE.original.md. Trigger: /caveman-compress FILEPATH or "compress memory file" | `.claude/skills/caveman-compress/SKILL.md` |
| caveman-help | > Quick-reference card for all caveman modes, skills, and commands. One-shot display, not a persistent mode. Trigger: /caveman-help, "caveman help", "what caveman commands", "how do I use caveman". | `.claude/skills/caveman-help/SKILL.md` |
| caveman-review | > Ultra-compressed code review comments. Cuts noise from PR feedback while preserving the actionable signal. Each comment is one line: location, problem, fix. Use when user says "review this PR", "code review", "review the diff", "/review", or invokes /caveman-review. Auto-triggers when reviewing pull requests. | `.claude/skills/caveman-review/SKILL.md` |
| caveman-stats | > Show real token usage and estimated savings for the current session. Reads directly from the Claude Code session log — no AI estimation. Triggers on /caveman-stats. Output is injected by the mode-tracker hook; the model itself does not compute the numbers. | `.claude/skills/caveman-stats/SKILL.md` |
| handoff | Write or update a handoff document so the next agent with fresh context can continue this work. | `.claude/skills/handoff/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
