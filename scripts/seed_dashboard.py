"""DASH-04: standalone 50-game dashboard seeder.

Drives N random-agent games through the existing :class:`BalatroEnv` and feeds
the dashboard :class:`Recorder` (03-02) via the driver-loop callback shape, so
runs/antes/hands/jokers land in ``db.DB_PATH`` (``data/runs.db``) — the SAME DB
the Streamlit app (03-03) reads.

Requires a LIVE Balatro game with the BalatroML mod loaded (same requirement as
ENV-04 / verify_bridge.py); the env's SocketBridge connects on launch.

Usage (after launching Balatro with the mod):
    source .venv/bin/activate
    uv run python scripts/seed_dashboard.py --n-games 50 --reset

Flags (typer):
    --n-games N   how many games to seed (default 50)
    --reset       drop + recreate db.DB_PATH first (destructive; explicit)
    --append      append to the existing DB (default; mutually exclusive w/ --reset)
    --deck DECK   deck id (default "b_red")
    --stake S     stake level (default 1)

Locked decisions honoured:
  * Driver-loop callback (03-RESEARCH Pattern 2): the recorder lives in the loop;
    BalatroEnv is untouched. Random action =
    ``int(np.random.choice(np.flatnonzero(env.action_masks())))``.
  * Pitfall 6 (raw obs): pass the env's RAW typed observation (``env._last_obs``)
    to the recorder — never the numpy dict.
  * Truncation safety (gymnasium_env.py:210): ``env.step()`` returns ``info={}``
    on a socket-timeout truncation. The loop passes ``info`` through UNMODIFIED;
    the recorder reads ``info.get("event")`` itself — the loop NEVER indexes
    ``info["event"]``.
  * Pitfall 8: ``rec.close()`` / ``env.close()`` run in a ``finally`` so the
    final batch flushes (no lost rows) even on error.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `src.*` importable when run directly (mirrors scripts/verify_bridge.py):
# repo root is this file's parent's parent.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import typer
from loguru import logger

from src.dashboard import db
from src.dashboard.recorder import Recorder
from src.env.gymnasium_env import BalatroEnv

app = typer.Typer(add_completion=False)


def _reset_db(path: str) -> None:
    """Drop + recreate the DB file (and its WAL/SHM sidecars), then re-init schema."""
    for suffix in ("", "-wal", "-shm"):
        p = path + suffix
        if os.path.exists(p):
            os.remove(p)
            logger.info(f"--reset: removed {p}")
    db.init_db(path)
    logger.info(f"--reset: re-initialised schema at {path}")


def _play_one_game(env: BalatroEnv, rec: Recorder, deck: str, stake: int) -> int:
    """Roll a single random-agent game and record it; return the hand count.

    Chooses each action uniformly among the legal ones via ``action_masks()``,
    steps until terminated/truncated, and feeds every transition to the recorder
    using the RAW typed obs + the unmodified ``info`` dict.
    """
    env.reset()
    run_id = rec.start_run(deck=deck, stake=stake)

    # Record the reset snapshot too (reset returns info={}; the recorder reads
    # info.get("event") and emits no row for an absent event — harmless, keeps
    # ante_reached tracking warm from step 0).
    rec.on_step(run_id, env._last_obs, {})

    n_hands = 0
    info: dict = {}  # last-seen info; {} fallback so end_run never sees an unbound name
    while True:
        mask = env.action_masks()
        legal = np.flatnonzero(mask)
        if legal.size == 0:
            # No legal action: defensively end the run rather than crash.
            logger.warning("No legal actions available — ending game early")
            break
        action = int(np.random.choice(legal))

        _obs, _reward, terminated, truncated, info = env.step(action)

        # Pitfall 6: RAW typed obs. Truncation safety: pass info through
        # UNMODIFIED — never index info["event"] here (it is {} on truncation).
        rec.on_step(run_id, env._last_obs, info)
        if info.get("event") == "hand_played":
            n_hands += 1

        if terminated or truncated:
            break

    # end_run reads info.get("event") -> won=1 only on "run_win", never KeyError.
    rec.end_run(run_id, env._last_obs, info)
    return n_hands


@app.command()
def seed(
    n_games: int = typer.Option(50, "--n-games", help="Number of games to seed."),
    reset: bool = typer.Option(
        False, "--reset", help="Drop + recreate the DB first (destructive)."
    ),
    append: bool = typer.Option(
        False, "--append", help="Append to the existing DB (default behaviour)."
    ),
    deck: str = typer.Option("b_red", "--deck", help="Deck id."),
    stake: int = typer.Option(1, "--stake", help="Stake level."),
) -> None:
    """Run N random-agent games through BalatroEnv into the dashboard DB."""
    if reset and append:
        raise typer.BadParameter("--reset and --append are mutually exclusive.")

    logger.info("=" * 60)
    logger.info(
        f"DASH-04 seeder | n_games={n_games} deck={deck} stake={stake} "
        f"mode={'reset' if reset else 'append'} db={db.DB_PATH}"
    )
    logger.info("=" * 60)

    if reset:
        _reset_db(db.DB_PATH)

    env = BalatroEnv(deck=deck, stake=stake)
    rec = Recorder()
    rec.start()

    total_hands = 0
    games_done = 0
    try:
        for g in range(1, n_games + 1):
            n_hands = _play_one_game(env, rec, deck, stake)
            total_hands += n_hands
            games_done += 1
            logger.info(
                f"game {g}/{n_games} complete | hands={n_hands} "
                f"(cumulative hands={total_hands})"
            )
    finally:
        # Pitfall 8: flush the final batch before exit; always close the env.
        rec.close()
        env.close()

    logger.info("=" * 60)
    logger.info(
        f"Seeding done | games={games_done}/{n_games} hands_written={total_hands} "
        f"db={db.DB_PATH}"
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    app()
