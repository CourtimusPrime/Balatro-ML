"""
Tests for BalatroEnv (ENV-01, ENV-03, ENV-04).

ENV-01 (action space unit tests) — run fully offline; test action_space.py directly
    with no mock or live game needed.

ENV-03 (offline env tests) — uses mock_env fixture from conftest.py that patches
    SocketBridge. No live socket or Balatro game required.

ENV-04 (integration test) — skip-marked; requires a live Balatro game (set BALATRO_LIVE=1).
"""

from __future__ import annotations

import json
import logging
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
# ENV-03 fixture — kept for backward compat; conftest.py provides mock_env
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
# ENV-03: Offline env tests — use mock_env fixture from conftest.py
# ---------------------------------------------------------------------------


def test_reset_returns_valid_obs(mock_env, minimal_raw_obs):
    """ENV-03: reset() returns (dict, dict) with observation_space keys."""
    env, mock = mock_env
    mock.get_state.return_value = minimal_raw_obs

    result = env.reset()

    assert isinstance(result, tuple)
    assert len(result) == 2
    obs_dict, info = result
    assert isinstance(obs_dict, dict)
    assert isinstance(info, dict)
    expected_keys = {"cards", "jokers", "consumables", "shop", "game_state"}
    assert set(obs_dict.keys()) == expected_keys


def test_step_return_signature(mock_env, minimal_raw_obs):
    """ENV-03: step() returns (dict, float, bool, bool, dict)."""
    env, mock = mock_env
    # reset first then step
    mock.get_state.side_effect = [minimal_raw_obs, minimal_raw_obs]

    env.reset()
    result = env.step(8)  # commit_play

    assert isinstance(result, tuple)
    assert len(result) == 5
    obs, reward, terminated, truncated, info = result
    assert isinstance(obs, dict)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_action_masks_shape_on_env(mock_env):
    """ENV-03: action_masks() returns np.ndarray shape (31,) dtype bool."""
    env, _mock = mock_env
    masks = env.action_masks()
    assert isinstance(masks, np.ndarray)
    assert masks.shape == (N_ACTIONS,)
    assert masks.dtype == bool


def test_action_masks_phase_routing(mock_env):
    """ENV-03: phase routing masks off wrong-phase actions."""
    env, _mock = mock_env

    # Playing phase: shop action (leave_shop) must be off
    env._current_phase = "playing"
    masks = env.action_masks()
    assert not masks[ACTION_INDEX["leave_shop"]]

    # Shop phase: playing action (commit_play) must be off
    env._current_phase = "shop"
    masks = env.action_masks()
    assert not masks[ACTION_INDEX["commit_play"]]


def test_check_env(mock_env, minimal_raw_obs):
    """ENV-03: gymnasium check_env passes without errors against mock bridge."""
    from gymnasium.utils.env_checker import check_env  # noqa: PLC0415

    env, mock = mock_env
    # check_env calls reset() then multiple steps; provide many raw obs responses
    mock.get_state.return_value = minimal_raw_obs

    check_env(env, skip_render_check=True)


def test_maskable_ppo_constructs(mock_env):
    """ENV-03: MaskablePPO('MultiInputPolicy', env) constructs without error."""
    from sb3_contrib import MaskablePPO  # noqa: PLC0415

    env, _mock = mock_env
    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        verbose=0,
        policy_kwargs={"normalize_images": False},
    )
    assert model is not None


# ---------------------------------------------------------------------------
# ENV-04: Integration test — requires live Balatro (skip unless BALATRO_LIVE=1)
# ---------------------------------------------------------------------------


# Expected observation keys and dtypes (from observation_space, Plan 03 / RESEARCH.md)
_EXPECTED_OBS_DTYPES = {
    "cards": np.int32,
    "jokers": np.float32,
    "consumables": np.int32,
    "shop": np.int32,
    "game_state": np.float32,
}

# Per-game step-limit guard: double MAX_STEPS (1000) so a stuck game fails fast
# with a descriptive message instead of hanging the test run.
_STEP_LIMIT = 2000

_log = logging.getLogger(__name__)


@BALATRO_LIVE
def test_random_agent_10_games():
    """ENV-04: random agent completes 10 full games, zero illegal actions, done fires."""
    from src.env.gymnasium_env import BalatroEnv  # noqa: PLC0415

    env = BalatroEnv(deck="b_red", stake=1)
    try:
        for game in range(10):
            obs, info = env.reset()

            # Validate observation structure and dtypes early to catch shape
            # mismatches before stepping.
            assert isinstance(obs, dict), f"reset() obs is not a dict: {type(obs)}"
            assert set(obs.keys()) == set(_EXPECTED_OBS_DTYPES), (
                f"obs keys {set(obs.keys())} != expected {set(_EXPECTED_OBS_DTYPES)}"
            )
            for key, expected_dtype in _EXPECTED_OBS_DTYPES.items():
                assert obs[key].dtype == expected_dtype, (
                    f"obs['{key}'] dtype {obs[key].dtype} != expected {expected_dtype}"
                )
            assert env.observation_space.contains(obs), (
                f"reset() obs not contained in observation_space (game {game})"
            )

            terminated = truncated = False
            steps = 0
            while not (terminated or truncated):
                masks = env.action_masks()
                assert masks.any(), "All actions masked — env bug"
                legal = np.where(masks)[0]
                action = int(np.random.choice(legal))
                obs, reward, terminated, truncated, info = env.step(action)
                assert np.isfinite(reward), f"Non-finite reward at step: {reward}"
                steps += 1
                assert steps < _STEP_LIMIT, (
                    f"Game {game} exceeded step limit ({_STEP_LIMIT}) without ending — "
                    "possible hang or missing terminal condition"
                )

            assert terminated or truncated, f"Game {game} did not end (no terminated/truncated)"
            _log.debug("Game %d completed in %d steps", game, steps)
    finally:
        env.close()
