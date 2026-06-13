"""
Tests for BalatroEnv (ENV-01, ENV-03, ENV-04).

ENV-01 (action space unit tests) — run fully offline; test action_space.py directly
    with no mock or live game needed.

ENV-03 (offline env tests) — stub; will be RED until Plan 03 creates gymnasium_env.py.
    Uses mock_bridge fixture that patches SocketBridge.

ENV-04 (integration test) — skip-marked; requires a live Balatro game (set BALATRO_LIVE=1).
"""

from __future__ import annotations

import json
import os
import queue
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.env.action_space import N_ACTIONS, ACTION_INDEX, decode_action, build_mask

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# ENV-04 skip marker
# ---------------------------------------------------------------------------

BALATRO_LIVE = pytest.mark.skipif(
    not os.environ.get("BALATRO_LIVE"),
    reason="Requires live Balatro game (set BALATRO_LIVE=1)",
)

# ---------------------------------------------------------------------------
# ENV-03 fixture — BalatroEnv with SocketBridge replaced by a MagicMock
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_bridge(monkeypatch):
    """BalatroEnv with SocketBridge replaced by a MagicMock — no live socket.

    NOTE: importing BalatroEnv inside the fixture keeps the module importable
    even when gymnasium_env.py is still a stub (RED until Plan 03).
    """
    from src.env.gymnasium_env import BalatroEnv  # noqa: PLC0415

    mock = MagicMock()
    mock.is_connected = True
    with patch("src.env.gymnasium_env.SocketBridge", return_value=mock):
        env = BalatroEnv(deck="b_red", stake=1)
    yield env, mock
    env.close()


# ---------------------------------------------------------------------------
# ENV-01: Action space (green after Plan 02 implements action_space.py)
# ---------------------------------------------------------------------------


def test_n_actions():
    """N_ACTIONS == 31."""
    assert N_ACTIONS == 31


def test_action_index_unique():
    """All ACTION_INDEX values are unique; len(ACTION_INDEX) == 31."""
    values = list(ACTION_INDEX.values())
    assert len(values) == 31
    assert len(set(values)) == 31


def test_decode_action_toggle_card():
    """decode_action(0) and decode_action(7) return correct toggle_card dicts."""
    assert decode_action(0) == {"action": "toggle_card", "index": 0}
    assert decode_action(7) == {"action": "toggle_card", "index": 7}


def test_decode_action_commit_play():
    """decode_action(8) returns commit_play dict."""
    assert decode_action(8) == {"action": "commit_play"}


def test_decode_action_shop_actions():
    """decode_action returns correct dicts for buy, reroll, leave_shop, blind actions."""
    assert decode_action(10) == {"action": "buy", "index": 0}
    assert decode_action(27) == {"action": "reroll"}
    assert decode_action(28) == {"action": "leave_shop"}
    assert decode_action(29) == {"action": "select_blind"}
    assert decode_action(30) == {"action": "skip_blind"}


def test_decode_action_invalid():
    """decode_action(31) raises ValueError (out-of-range)."""
    with pytest.raises(ValueError):
        decode_action(31)


def test_build_mask_shape():
    """build_mask returns np.ndarray shape (31,) dtype bool."""
    mask = build_mask("playing", 5, 0, 3, [], [], [], 10, 2)
    assert isinstance(mask, np.ndarray)
    assert mask.shape == (N_ACTIONS,)
    assert mask.dtype == bool


def test_build_mask_playing_phase():
    """Playing phase: hand slots 0-4 True, commit_play/discard True, shop off."""
    mask = build_mask(
        phase="playing",
        hand_size=5,
        n_selected=2,
        discards_remaining=1,
        shop_items=[],
        jokers=[],
        consumables=[],
        money=10,
        reroll_cost=2,
    )
    # toggle_card_0..4 should be True (hand_size=5)
    assert all(mask[0:5])
    # toggle_card_5..7 should be False (no cards there)
    assert not any(mask[5:8])
    # commit_play at index 8 (n_selected=2, in 1..5 range)
    assert bool(mask[8])
    # commit_discard at index 9 (n_selected=2, discards_remaining=1)
    assert bool(mask[9])
    # All shop/blind actions should be off
    assert not any(mask[10:])


def test_build_mask_shop_phase():
    """Shop phase: leave_shop always True; commit_play/discard off."""
    mask = build_mask(
        phase="shop",
        hand_size=0,
        n_selected=0,
        discards_remaining=0,
        shop_items=[],
        jokers=[],
        consumables=[],
        money=10,
        reroll_cost=2,
    )
    # leave_shop (index 28) always True in shop
    assert bool(mask[28])
    # commit_play/discard off
    assert not bool(mask[8])
    assert not bool(mask[9])


def test_build_mask_blind_select_phase():
    """Blind-select phase: only select_blind (29) and skip_blind (30) True."""
    mask = build_mask(
        phase="blind_select",
        hand_size=0,
        n_selected=0,
        discards_remaining=0,
        shop_items=[],
        jokers=[],
        consumables=[],
        money=0,
        reroll_cost=0,
    )
    assert mask.sum() == 2
    assert bool(mask[29])
    assert bool(mask[30])


def test_build_mask_no_discards():
    """Playing phase with discards_remaining=0: commit_discard (9) is False."""
    mask = build_mask(
        phase="playing",
        hand_size=5,
        n_selected=2,
        discards_remaining=0,
        shop_items=[],
        jokers=[],
        consumables=[],
        money=10,
        reroll_cost=2,
    )
    assert not bool(mask[9])
    # commit_play still enabled (n_selected=2)
    assert bool(mask[8])


# ---------------------------------------------------------------------------
# ENV-03 stubs (RED until Plan 03 creates gymnasium_env.py)
# ---------------------------------------------------------------------------


def test_reset_returns_valid_obs(mock_bridge):
    """ENV-03 stub: reset() returns (dict, dict) matching observation_space keys."""
    env, mock = mock_bridge
    assert env is not None


def test_step_return_signature(mock_bridge):
    """ENV-03 stub: step() returns (dict, float, bool, bool, dict)."""
    env, mock = mock_bridge
    assert env is not None


def test_action_masks_shape_on_env(mock_bridge):
    """ENV-03 stub: action_masks() returns np.ndarray shape (31,) dtype bool."""
    env, mock = mock_bridge
    assert env is not None


def test_action_masks_phase_routing(mock_bridge):
    """ENV-03 stub: phase routing masks off wrong-phase actions."""
    env, mock = mock_bridge
    assert env is not None


def test_check_env(mock_bridge):
    """ENV-03 stub: gymnasium check_env passes without warnings."""
    env, mock = mock_bridge
    assert env is not None


def test_maskable_ppo_constructs(mock_bridge):
    """ENV-03 stub: MaskablePPO('MultiInputPolicy', env) constructs without error."""
    env, mock = mock_bridge
    assert env is not None


# ---------------------------------------------------------------------------
# ENV-04: Integration test — requires live Balatro (skip unless BALATRO_LIVE=1)
# ---------------------------------------------------------------------------


@BALATRO_LIVE
def test_random_agent_10_games():
    """ENV-04: random agent completes 10 full games, zero illegal actions, done fires."""
    from src.env.gymnasium_env import BalatroEnv  # noqa: PLC0415

    env = BalatroEnv(deck="b_red", stake=1)
    for game in range(10):
        obs, info = env.reset()
        terminated = truncated = False
        while not (terminated or truncated):
            masks = env.action_masks()
            assert masks.any(), "All actions masked — env bug"
            legal = np.where(masks)[0]
            action = int(np.random.choice(legal))
            obs, reward, terminated, truncated, info = env.step(action)
            assert np.isfinite(reward), f"Non-finite reward at step: {reward}"
        assert terminated or truncated
    env.close()
