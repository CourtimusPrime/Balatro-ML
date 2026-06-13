"""
Shared pytest fixtures for the BalatroEnv test suite.

Provides:
  mock_env       — BalatroEnv with SocketBridge replaced by a MagicMock; no TCP.
  minimal_raw_obs — raw dict matching FullObservation wire format; minimal valid state.
"""

from __future__ import annotations

import queue
from unittest.mock import MagicMock

import pytest

from src.env.gymnasium_env import BalatroEnv


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
