"""
Shared pytest fixtures for the BalatroEnv test suite.

Provides:
  mock_env        — BalatroEnv with SocketBridge replaced by a MagicMock; no TCP.
  minimal_raw_obs — raw dict matching FullObservation wire format; minimal valid state.
  booster_raw_obs — raw dict matching FullObservation wire format; booster_pack phase.
"""

from __future__ import annotations

import json
import queue
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.env.gymnasium_env import BalatroEnv

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# mock_env fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_env(monkeypatch):
    """BalatroEnv with SocketBridge replaced by a MagicMock — no live socket.

    Yields (env, mock) where mock is the MagicMock instance that SocketBridge()
    returns. Calls env.close() in teardown.
    """
    mock = MagicMock()
    mock.start.return_value = None
    mock.stop.return_value = None
    mock.is_connected = True
    mock._incoming = queue.Queue()

    monkeypatch.setattr("src.env.gymnasium_env.SocketBridge", lambda **kwargs: mock)

    env = BalatroEnv(deck="b_red", stake=1)
    env._current_phase = "playing"
    env._step_count = 0

    yield env, mock
    env.close()


# ---------------------------------------------------------------------------
# minimal_raw_obs fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_raw_obs():
    """Return a raw dict matching the FullObservation wire format.

    Minimal valid state: playing phase, one card in hand, no jokers, no
    consumables, empty shop, standard game-state scalars.
    """
    return {
        "event": "draw",
        "phase": "playing",
        "cards": [
            {
                "suit": "Spades",
                "value": "Ace",
                "enhancement": "Base",
                "edition": "",
                "seal": "",
                "debuffed": False,
                "selected": False,
                "in_hand": True,
                "in_deck": False,
            }
        ],
        "jokers": [],
        "consumables": [],
        "shop": {
            "items": [],
            "reroll_cost": 2,
        },
        "game_state": {
            "ante": 1,
            "blind": 0,
            "blind_name": "Small Blind",
            "chips_needed": 300,
            "chips_scored": 0,
            "hands_remaining": 4,
            "discards_remaining": 3,
            "money": 4,
            "hand_size": 8,
            "joker_slots": 5,
            "consumable_slots": 2,
            "hand_levels": {
                "High Card": 1,
                "Pair": 1,
                "Two Pair": 1,
                "Three of a Kind": 1,
                "Straight": 1,
                "Flush": 1,
                "Full House": 1,
                "Four of a Kind": 1,
                "Straight Flush": 1,
                "Royal Flush": 1,
                "Five of a Kind": 1,
                "Flush House": 1,
                "Flush Five": 1,
            },
            "reroll_cost": 2,
        },
    }


# ---------------------------------------------------------------------------
# booster_raw_obs fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def booster_raw_obs():
    """Return a raw dict matching the FullObservation wire format for the booster_pack phase.

    Mirrors booster_pack_state.json: Arcana pack, 3 Tarot card options,
    pack_picks_remaining=1, pack_type="Arcana".  Used for offline booster-pack
    env and observation tests (Wave 0 scaffold; turned GREEN by Slice B).
    """
    return json.loads((FIXTURES_DIR / "booster_pack_state.json").read_text())


# ---------------------------------------------------------------------------
# seeded_db fixture (dashboard data layer — DASH-01)
# ---------------------------------------------------------------------------


@pytest.fixture()
def seeded_db(tmp_path):
    """Build a small, deterministic temp runs.db and yield its path.

    Contents (offline, no live game):
      - 3 runs across 2 decks / 2 stakes; all finalized with distinct
        final_scores (so get_best_run has a unique winner).
      - ante_events for each run.
      - hand_events: a full hand-by-hand sequence for the top run (the
        best run), plus some hands with NULL hand_type to prove the
        get_hand_type_counts NULL-exclusion.
      - joker_events: overlapping joker sets so get_joker_cooccurrence
        finds at least one j1<j2 pair among high-scoring runs.

    Downstream plans (03-02 recorder, 03-03 app, 03-04 seed) reuse this
    fixture for their offline tests.
    """
    from src.dashboard import db

    path = str(tmp_path / "runs.db")
    db.init_db(path)
    conn = db.connect(path)

    # Run A — best run (deck b_red, stake 1), highest final_score.
    a = db.insert_run(conn, "b_red", 1, "2026-01-01T10:00:00")
    db.finalize_run(conn, a, final_score=90000, won=1, ante_reached=8,
                    num_jokers=3, ended_at="2026-01-01T10:25:00")
    db.insert_ante(conn, a, ante=1, blind_chips=300, chips_scored=450,
                   created_at="2026-01-01T10:02:00")
    db.insert_ante(conn, a, ante=2, blind_chips=800, chips_scored=1200,
                   created_at="2026-01-01T10:05:00")
    db.insert_hand(conn, a, ante=1, hand_index=0, hand_type="Pair",
                   chips=40, mult=2, n_cards=2, score=80,
                   created_at="2026-01-01T10:02:10")
    db.insert_hand(conn, a, ante=1, hand_index=1, hand_type="Flush",
                   chips=140, mult=4, n_cards=5, score=560,
                   created_at="2026-01-01T10:02:20")
    db.insert_hand(conn, a, ante=2, hand_index=2, hand_type="Full House",
                   chips=160, mult=4, n_cards=5, score=640,
                   created_at="2026-01-01T10:05:10")
    # A hand with NULL hand_type (e.g. a discard / unscored event).
    db.insert_hand(conn, a, ante=2, hand_index=3, hand_type=None,
                   chips=None, mult=None, n_cards=None, score=0,
                   created_at="2026-01-01T10:05:20")
    db.insert_jokers(conn, a, [10, 20, 30])

    # Run B — mid score (deck b_blue, stake 2).
    b = db.insert_run(conn, "b_blue", 2, "2026-01-01T11:00:00")
    db.finalize_run(conn, b, final_score=45000, won=0, ante_reached=5,
                    num_jokers=2, ended_at="2026-01-01T11:20:00")
    db.insert_ante(conn, b, ante=1, blind_chips=300, chips_scored=300,
                   created_at="2026-01-01T11:02:00")
    db.insert_hand(conn, b, ante=1, hand_index=0, hand_type="Pair",
                   chips=40, mult=2, n_cards=2, score=80,
                   created_at="2026-01-01T11:02:10")
    db.insert_hand(conn, b, ante=1, hand_index=1, hand_type="High Card",
                   chips=5, mult=1, n_cards=1, score=5,
                   created_at="2026-01-01T11:02:20")
    db.insert_jokers(conn, b, [10, 20])  # shares 10,20 with run A

    # Run C — low score (deck b_red, stake 1, same deck/stake as A).
    c = db.insert_run(conn, "b_red", 1, "2026-01-01T12:00:00")
    db.finalize_run(conn, c, final_score=10000, won=0, ante_reached=3,
                    num_jokers=1, ended_at="2026-01-01T12:10:00")
    db.insert_ante(conn, c, ante=1, blind_chips=300, chips_scored=150,
                   created_at="2026-01-01T12:02:00")
    db.insert_hand(conn, c, ante=1, hand_index=0, hand_type="High Card",
                   chips=5, mult=1, n_cards=1, score=5,
                   created_at="2026-01-01T12:02:10")
    db.insert_jokers(conn, c, [40])

    conn.commit()
    conn.close()
    yield path
