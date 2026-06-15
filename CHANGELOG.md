# Changelog

All notable changes to **Balatro ML** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Work is organised by GSD development phase. No tagged release has been cut yet;
everything below is part of the in-progress `0.1.0` development line.

## [Unreleased]

### Phase 3 — Dashboard (in progress)

Live Streamlit metrics backed by a non-blocking SQLite write pipeline.

#### Added
- SQLite persistence layer (`db.py`): `runs`, `ante_events`, and `hand_events`
  schema with WAL mode, `init_db`/connect helpers, `insert_*` writers, and six
  panel query methods (DASH-01).
- Non-blocking `Recorder` — a background queue + writer thread that records
  runs/antes/hands without visibly slowing the game simulation (DASH-02).
- `last_hand` field added to the mod snapshot and the observation model so
  hand-by-hand breakdowns can be recorded.
- Streamlit dashboard (`src/dashboard/app.py`): 7 metric panels with fragment
  auto-refresh, caching, dark theme, and `#F0A500` accent (DASH-03).
- `fmt_si` SI-formatting helper, dark theme config, and a dashboard smoke test.
- `scripts/seed_dashboard.py` — seeds the database with 50 random-agent games to
  verify the pipeline end-to-end before real training (DASH-04).

#### Fixed
- Hands are now recorded via the `commit_play` action rather than a non-existent
  `hand_played` event.
- UI-SPEC database-path correction.

#### Pending
- 03-04 live verification checkpoint (all 7 panels against seeded data).

## Phase 2.1 — Booster Pack Purchases — 2026-06-14 *(inserted)*

The agent can buy, view, and resolve Celestial / Standard / Arcana booster packs
in the shop. Action space and Lua bridge dispatch extended with pack
buy/open/select/skip actions plus masking so an illegal pack action can never be
selected (ENV-PACK-01…06).

### Added
- Offline booster-pack wire-dict fixtures and `booster_raw_obs` conftest fixture.
- Booster-pack action indices 31–36; `N_ACTIONS` bumped from 31 to **37**, with
  slot-gated `build_mask` branch for the `booster_pack` phase.
- `PACK_TYPE_MAP` plus defaulted pack/scalar fields on the Pydantic models.
- Gymnasium observation grown atomically: pack `Box(low=-1)`, 4-way pack-type
  one-hot, and `game_state` widened to `(29,)`.
- `mod/state.lua` emits pack snapshot, scalars, and a `booster_pack` phase;
  `mod/bridge.lua` gains `select_pack_card` / `skip_pack` dispatch and
  `pack_open` classification.
- `probe_lua_funcs.py` extended with `skip_booster` and a `G.STATES` dump.
- Skip-marked live acceptance tests for pack resolution (SC-3/4/5).

### Fixed
- `build_mask` shop branch now supports dict-shaped `shop_items`.

## Phase 2 — Gymnasium Environment — 2026-06-14

A learnable `gymnasium.Env` wrapping the socket bridge — a random agent plays 10
complete games with zero illegal actions (ENV-01…04, ENV-04 live pass).

### Added
- `compute_reward()` (`src/env/reward.py`): finite, log-transformed rewards across
  all components — never NaN/inf (ENV-02).
- `action_space.py`: N=31 action layout, `decode_action`, and masked `build_mask`
  so illegal actions can never be selected (ENV-01).
- `BalatroEnv` (`src/env/`): `gymnasium.Env` (`reset`/`step`/`action_masks`/
  spaces) compatible with `sb3_contrib.MaskablePPO` (ENV-03).
- `conftest.py` with `mock_env` and `minimal_raw_obs` fixtures for fully offline
  env tests.
- `BML_Bridge.dispatch` + `emit_raw` in `mod/bridge.lua`; `probe_lua_funcs.py`
  to dump `G.FUNCS` keys over the socket for live verification.
- ENV-04 random-agent 10-game live integration test.
- Mod hot-reload, per-instance port, and Proton launch/restart helpers.
- `sb3-contrib>=2.8` pinned in `pyproject.toml` and `uv.lock`.

### Fixed
- Strict 1-action / 1-response bridge protocol so the agent plays end-to-end.
- Blind-select actions deferred until the lazy UI is ready.
- `SocketBridge.stop()` drains pending tasks before closing the loop.
- Socket tests bind ephemeral ports so they don't collide with live Balatro.
- Card selection, reset drain, and runtime reload id corrected (ENV-04 passes).
- `reload_mod.py` adds the repo root to `sys.path` so `src` imports resolve.

## Phase 1 — Socket Bridge — 2026-06-13

Validated game state flows end-to-end from Balatro into Python as clean,
structured data (BRIDGE-01…05).

### Added
- `src/data/normalise.py`: all 12 string→int lookup maps and `_get` helper,
  unknown keys mapping to `-1` rather than raising (BRIDGE-02).
- Steamodded mod: `mod/manifest.json`, `mod/state.lua` (`BML_State` `G.*`
  extraction), `mod/bridge.lua` (TCP client + 9 event hooks), vendored
  `mod/lib/json.lua`.
- `src/env/observation.py`: Pydantic v2 models that validate/normalise raw
  socket JSON, raise `ValidationError` on malformed data, force stone cards to
  `suit=0,value=0`, and normalise jokers via `JOKER_ID_MAP` (BRIDGE-04).
- `scripts/verify_bridge.py` — BRIDGE-05 live verification probe.
- Cross-check tests for `normalise.py` and observation fixtures
  (`sample_state.json`).

### Fixed
- `AGENT_ORT` import typo; pytest `pythonpath` config added.
- Pre-existing async TCP socket bridge committed (BRIDGE-03, 13/13 socket tests).
- `verify_bridge.py` made standalone/manual-run friendly (`sys.path` bootstrap).
- Deterministic `test_connection_detected` (assert before closing).

## Phase 0 — Repository Bootstrap — 2026-06-13

Project scaffolding (pre-GSD).

### Added
- Repository structure (`src/`, `mod/`, `scripts/`, `tests/`, `data/`, `logs/`),
  `pyproject.toml`, pinned requirements, and Python 3.11 pinning.
- Initial Lua mod files and Python stubs.
- GSD project context and workflow guidance in `CLAUDE.md`; `.planning/`
  gitignored as GSD local-only.
