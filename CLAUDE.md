# Claude Config

## Project

**Balatro ML**

A reinforcement-learning agent that learns to **maximise scores** (not win rate) across all 15 Balatro decks and all 8 stake levels. Balatro streams game state into Python over a TCP socket; a Gymnasium environment wraps it; a transformer-policy PPO agent trains 24/7 via self-play, optionally bootstrapped by human gameplay sessions.

Target results:

- Emergent strategies
- Joker-synergy heatmaps
- Score progression

**Core Value:** Game state must flow from Balatro into Python as clean, validated, structured data, and the agent must learn from it — score distribution visibly improving over training time. If the bridge is flaky or the agent never learns, nothing else matters.

## Rules

- Use `uv` as the package manager
- Always use the virtual environment before installing packages or running code (`source .venv/bin/activate`)

<!-- GSD:project-start source:PROJECT.md -->

## Project

**Balatro ML**

### Constraints

- **Tech stack**: Python 3.11, `uv` package manager, mandatory `.venv` activation before installing/running — project convention (CLAUDE.md)
- **Reward**: log-transformed throughout — scores span many orders of magnitude; log compresses the range for stable gradients
- **Dependencies**: Balatro must be running before the Python trainer starts; mod auto-connects on launch
- **Data integrity**: malformed socket data must raise (Pydantic `ValidationError`) so bugs surface immediately rather than silently corrupting training

> Note: See CLAUDE.local.md for hardware-specific configuration (gitignored).

## Technology Stack

- **Language / runtime**: Python 3.11 (pinned to 3.11.9 via `.python-version` and `.mise.toml`), managed with `uv`.
- **RL core**: Gymnasium (env interface), Stable-Baselines3 + sb3-contrib (`MaskablePPO`), PyTorch (policy network).
- **Game bridge**: Lua mod loaded via Steamodded (`>=1.0`), communicating with Python over newline-delimited JSON on a TCP socket.
- **Data validation**: Pydantic v2 — all inbound socket payloads are parsed into models; malformed data raises `ValidationError`.
- **Persistence**: SQLite via the stdlib `sqlite3` module (WAL journal mode), with NumPy / Pandas for in-memory data.
- **Dashboard**: Streamlit + Plotly (local, read-only training monitor).
- **CLI / logging / output**: Typer (entrypoints), Loguru (logging), Rich (terminal output).
- **Dev tooling**: pytest (+ pytest-asyncio), ruff (lint + format), pyright (`basic` mode).
- **Task runner**: `just` (see `justfile`); recipes wrap `uv run`.

## Conventions

- **Environment**: `uv` is the only package manager; activate `.venv` before installing or running (see Rules).
- **Commits**: Conventional Commits with a phase scope, e.g. `feat(03-04): ...`, `fix(03-04): ...`. Keep commits atomic, and log every change in `CHANGELOG.md` (see Development Rules).
- **Typing**: Every module opens with `from __future__ import annotations`; use PEP 604 (`X | None`) style. pyright runs in `basic` mode.
- **Lint / format**: ruff, line length 100, target `py311`, rule sets `E, F, I, UP`.
- **Module docstrings**: Each module begins with a docstring stating its protocol/contract. Code references design decisions inline as `Pitfall N` and `Locked decision` markers — preserve these when editing.
- **Logging**: Use the `loguru` `logger`, not stdlib `logging`.
- **Data integrity**: Validate at the boundary with Pydantic; fail loud on bad data rather than silently coercing. Raw-string game fields are converted to stable ints through the lookup tables in `src/data/normalise.py` (sentinel `-1` = unknown, `0` = absent/optional).
- **Reward**: Log-transformed throughout and guaranteed finite (`np.nan_to_num`); the authoritative formula lives in `src/env/reward.py` / README.
- **SQL**: Always bind dynamic values with `?` placeholders; never build SQL with f-strings or `.format()`.
- **Tests**: Live in `tests/`, one `test_<module>.py` per source module; pytest is configured with `pythonpath = ["."]`.

## Architecture

Data flows in a single loop: **Balatro (Lua mod) → TCP socket → Gymnasium env → PPO agent**, with a separate read-only path into the dashboard.

- **`mod/`** — Steamodded Lua mod (`BalatroML`). `bridge.lua` is a thin, run-once bootstrap that loads deps and wraps `love.update`; `logic.lua` holds the hot-reloadable connect/poll/dispatch loop; `state.lua` builds the game-state snapshot; `lib/json.lua` is the JSON codec. It emits one JSON event per game event and accepts one JSON action per message. Ports: `12345` (agent), `12346` (human recording).
- **`src/env/`** — the bridge and RL environment.
  - `socket_bridge.py`: thread-safe `SocketBridge` running an asyncio TCP server on a background daemon thread; the synchronous env calls `get_state` / `send_action`.
  - `gymnasium_env.py`: `BalatroEnv` (a `gym.Env`) with a `spaces.Dict` observation (six padded Box sub-spaces) and a flat `Discrete(37)` action space exposing `action_masks()` for `MaskablePPO`.
  - `observation.py`: Pydantic v2 models that parse raw events into `FullObservation`.
  - `action_space.py`: the 37-action index layout, `decode_action`, and `build_mask`.
  - `reward.py`: pure reward computation.
- **`src/data/`** — `normalise.py` (string→int maps) is complete; `database.py` and `replay_buffer.py` are stubs pending the training/IL work.
- **`src/agent/`** — `trainer.py` (PPO + imitation learning), `policy.py` (transformer network), and `curriculum.py` (deck/stake progression) are currently stubs.
- **`src/dashboard/`** — read-only Streamlit monitor. `db.py` owns the SQLite schema + parameterized queries, `recorder.py` writes training events, `app.py` renders the panels, `format.py` provides display helpers.
- **`scripts/`** — entrypoints (`train.py`, `dashboard.py`, `record_human.py`, `verify_bridge.py`, `reload_mod.py`, `seed_dashboard.py`) plus Balatro launch/restart shell helpers. The Python entrypoints are wired in `pyproject.toml` (`[project.scripts]`) and via the `justfile`.

> Note: several `src/agent/`, `src/data/`, and `scripts/` files are intentional stubs — the bridge, env, and dashboard are the implemented core; the training loop is the next build-out.

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.

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

## Development Rules

- To understand game knowledge, refer to @.game/CLAUDE.md
- When you make any changes, log them in @CHANGELOG.md
