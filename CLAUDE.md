# Claude Config

## Rules

- Use `uv` as the package manager
- Always use the virtual environment before installing packages or running code (`source .venv/bin/activate`)

<!-- GSD:project-start source:PROJECT.md -->
## Project

**Balatro ML**

A reinforcement-learning agent that learns to **maximise scores** (not win rate) across all 15 Balatro decks and all 8 stake levels. Balatro streams game state into Python over a TCP socket; a Gymnasium environment wraps it; a transformer-policy PPO agent trains 24/7 via self-play, optionally bootstrapped by human gameplay sessions. Results — emergent strategies, joker-synergy heatmaps, score progression — are intended for publication to the Balatro subreddit.

**Core Value:** Game state must flow from Balatro into Python as clean, validated, structured data, and the agent must learn from it — score distribution visibly improving over training time. If the bridge is flaky or the agent never learns, nothing else matters.

### Constraints

- **Tech stack**: Python 3.11, `uv` package manager, mandatory `.venv` activation before installing/running — project convention (CLAUDE.md)
- **Hardware**: Intel i5-1340P, 12 cores, 16GB RAM — caps worker count (~24), memory (`MemoryMax=12G`), and requires thermal monitoring (keep CPU < 85°C sustained; `CPUQuota=85%`)
- **Reward**: log-transformed throughout — scores span many orders of magnitude; log compresses the range for stable gradients
- **Dependencies**: Balatro must be running before the Python trainer starts; mod auto-connects on launch
- **Data integrity**: malformed socket data must raise (Pydantic `ValidationError`) so bugs surface immediately rather than silently corrupting training
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
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
