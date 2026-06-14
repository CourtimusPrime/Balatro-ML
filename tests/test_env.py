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
    """N_ACTIONS == 37."""
    assert N_ACTIONS == 37


def test_action_index_unique():
    """All ACTION_INDEX values are unique; len(ACTION_INDEX) == 37."""
    values = list(ACTION_INDEX.values())
    assert len(values) == 37
    assert len(set(values)) == 37


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
    """decode_action(37) raises ValueError (out-of-range; 31-36 are now valid)."""
    with pytest.raises(ValueError):
        decode_action(37)


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
    expected_keys = {"cards", "jokers", "consumables", "shop", "pack", "game_state"}
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
# ENV-01 / ENV-03: Booster-pack action + mask stubs (Wave 0 RED)
#
# These stubs assert the REAL intended behaviour for Phase 02.1.
# They FAIL until Slice A (02.1-02) implements the production code.
# Do NOT edit test_n_actions / test_action_index_unique / test_decode_action_invalid
# here — Slice A (plan 02.1-02) owns those contract updates.
# ---------------------------------------------------------------------------


def test_decode_action_booster_pack():
    """decode_action(31..36) return correct dicts; decode_action(37) raises.

    RED: fails until Slice A adds SELECT_PACK_CARD_BASE=31 / SKIP_PACK=36 / N_ACTIONS=37.
    """
    # Indices 31-35: select_pack_card_0..4
    assert decode_action(31) == {"action": "select_pack_card", "index": 0}
    assert decode_action(35) == {"action": "select_pack_card", "index": 4}
    # Index 36: skip_pack
    assert decode_action(36) == {"action": "skip_pack"}
    # Index 37: invalid (new upper bound)
    with pytest.raises(ValueError):
        decode_action(37)


def test_booster_pack_mask():
    """build_mask("booster_pack", picks=1, 1 occupied Tarot card) enables select_pack_card_0 + skip_pack.

    RED: fails until Slice A adds the booster_pack branch to build_mask.
    """
    # One Tarot card in slot 0; consumable slot free (1 consumable, 2 slots).
    tarot_card = {"type": "Tarot", "id": 0, "cost": 0, "edition": 0, "enhancement": 0, "seal": 0}
    mask = build_mask(
        phase="booster_pack",
        hand_size=0,
        n_selected=0,
        discards_remaining=0,
        shop_items=[],
        jokers=[],
        consumables=[None],
        money=0,
        reroll_cost=0,
        pack_cards=[tarot_card, None, None, None, None],
        pack_picks_remaining=1,
        consumable_slots=2,
        joker_slots=5,
    )
    # select_pack_card_0 (index 31) must be True; others (32-35) False (empty slots)
    assert bool(mask[31]), "select_pack_card_0 should be True for occupied Tarot + free slot"
    assert not any(mask[32:36]), "select_pack_card_1..4 should be False (empty slots)"
    # skip_pack (36) must always be True
    assert bool(mask[36]), "skip_pack must always be True"


def test_picks_zero():
    """build_mask("booster_pack", picks=0) enables only skip_pack (no selects).

    RED: fails until Slice A adds the booster_pack branch to build_mask.
    """
    tarot_card = {"type": "Tarot", "id": 0, "cost": 0, "edition": 0, "enhancement": 0, "seal": 0}
    mask = build_mask(
        phase="booster_pack",
        hand_size=0,
        n_selected=0,
        discards_remaining=0,
        shop_items=[],
        jokers=[],
        consumables=[],
        money=0,
        reroll_cost=0,
        pack_cards=[tarot_card, tarot_card, tarot_card, None, None],
        pack_picks_remaining=0,
        consumable_slots=2,
        joker_slots=5,
    )
    # No select_pack_card_i should be True when picks exhausted
    assert not any(mask[31:36]), "No selects legal when picks=0"
    # skip_pack must still be True
    assert bool(mask[36]), "skip_pack must always be True"


def test_slot_gate():
    """Tarot/Spectral select masked off when all consumable slots are full; skip_pack still legal.

    RED: fails until Slice A adds slot-gating logic in build_mask.
    """
    # 2 consumables in 2 slots → no free slot
    tarot_card = {"type": "Tarot", "id": 0, "cost": 0, "edition": 0, "enhancement": 0, "seal": 0}
    spectral_card = {"type": "Spectral", "id": 0, "cost": 0, "edition": 0, "enhancement": 0, "seal": 0}
    occupied_consumables = [{"id": "c_fool", "type": 0}, {"id": "c_magician", "type": 0}]

    mask = build_mask(
        phase="booster_pack",
        hand_size=0,
        n_selected=0,
        discards_remaining=0,
        shop_items=[],
        jokers=[],
        consumables=occupied_consumables,
        money=0,
        reroll_cost=0,
        pack_cards=[tarot_card, spectral_card, None, None, None],
        pack_picks_remaining=1,
        consumable_slots=2,
        joker_slots=5,
    )
    # Tarot (slot 0) and Spectral (slot 1) must be masked off — no free consumable slot
    assert not bool(mask[31]), "Tarot select must be masked when consumable slots full"
    assert not bool(mask[32]), "Spectral select must be masked when consumable slots full"
    # skip_pack must still be True (success criterion 6)
    assert bool(mask[36]), "skip_pack must always be True even when all selects gated"


def test_skip_always_legal():
    """skip_pack (index 36) is True in EVERY booster_pack mask scenario (property test).

    RED: fails until Slice A adds the booster_pack branch to build_mask.
    """
    # Test a range of scenarios; skip_pack must be True in every case.
    planet_card = {"type": "Planet", "id": 0, "cost": 0, "edition": 0, "enhancement": 0, "seal": 0}
    tarot_card = {"type": "Tarot", "id": 0, "cost": 0, "edition": 0, "enhancement": 0, "seal": 0}
    occupied_consumables = [{"id": "c_fool", "type": 0}, {"id": "c_magician", "type": 0}]

    scenarios = [
        # (picks_remaining, pack_cards, consumables, consumable_slots, description)
        (1, [planet_card], [], 2, "single Planet, free slot"),
        (0, [planet_card], [], 2, "picks exhausted"),
        (1, [tarot_card], occupied_consumables, 2, "Tarot, slots full"),
        (2, [tarot_card, planet_card, None, None, None], [], 2, "Mega pack, 2 picks left"),
        (0, [], [], 2, "empty pack, picks=0"),
    ]
    for picks, pack_cards, consumables, consumable_slots, description in scenarios:
        mask = build_mask(
            phase="booster_pack",
            hand_size=0,
            n_selected=0,
            discards_remaining=0,
            shop_items=[],
            jokers=[],
            consumables=consumables,
            money=0,
            reroll_cost=0,
            pack_cards=pack_cards,
            pack_picks_remaining=picks,
            consumable_slots=consumable_slots,
            joker_slots=5,
        )
        assert bool(mask[36]), f"skip_pack must be True in scenario: {description}"


def test_shop_buys_booster_transition():
    """Buying a type==6 shop item (booster pack) is mask-legal when affordable.

    RED: fails until Slice A implements the shop mask affordability for type==6 items.
    Shop mask must allow buy_i for a booster-pack item when player has enough money.
    This tests the transition affordability, not the phase switch itself (which is Lua).
    """
    booster_pack_item = {"type": "Booster", "id": "p_arcana_1", "cost": 4, "edition": 0, "enhancement": 0, "seal": 0}
    mask = build_mask(
        phase="shop",
        hand_size=0,
        n_selected=0,
        discards_remaining=0,
        shop_items=[booster_pack_item],
        jokers=[],
        consumables=[],
        money=10,
        reroll_cost=5,
    )
    # buy_0 (index 10) must be True when we have enough money for a $4 pack
    assert bool(mask[10]), "buy_0 must be legal when shop has a booster pack and player has money"


def test_pack_obs_booster_fixture(booster_raw_obs):
    """pack Box populated from a booster fixture; FullObservation accepts pack payload.

    RED: fails until Slice B adds pack field to FullObservation and extends gymnasium_env.
    """
    from src.env.observation import parse_observation  # noqa: PLC0415

    obs = parse_observation(booster_raw_obs)
    # Phase should be booster_pack
    assert obs.phase == "booster_pack"
    # pack list should have 3 Tarot cards (from booster_pack_state.json)
    assert len(obs.pack) == 3
    # Each pack item should have type resolved as integer (Tarot → 1)
    assert obs.pack[0].type == 1


def test_pack_obs_contains(mock_env, booster_raw_obs):
    """observation_space.contains(obs) True with a booster fixture (inc. pack Box).

    RED: fails until Slice B adds pack Box to observation_space and wires encoding.
    """
    env, mock = mock_env
    mock.get_state.return_value = booster_raw_obs
    obs_dict, _info = env.reset()
    assert "pack" in obs_dict, "pack key must be present in obs dict"
    assert env.observation_space.contains(obs_dict), (
        "observation_space.contains must be True with booster_pack obs"
    )


# ---------------------------------------------------------------------------
# ENV-04 (live): live pack acceptance tests — skip unless BALATRO_LIVE=1
#
# These tests (SC-3/4/5) require:
#   1. A running modded Balatro (lovely-injector + Steamodded >= 1.0)
#   2. The G.FUNCS pack names confirmed/corrected via the probe checkpoint (Task 4)
#   3. BALATRO_LIVE=1 environment variable set
#
# They skip cleanly offline and MUST NOT be marked done until Task 4 (the live
# G.FUNCS probe checkpoint) confirms or corrects the ASSUMED names.
# ---------------------------------------------------------------------------

_LIVE_SKIP = pytest.mark.skipif(
    not os.environ.get("BALATRO_LIVE"),
    reason="Requires live modded Balatro + probe checkpoint resolved (set BALATRO_LIVE=1)",
)


@_LIVE_SKIP
def test_live_pack_celestial_levels_hand():
    """SC-3 live: buying a Celestial pack and selecting a Planet card levels a hand.

    Acceptance gate (live only — gated behind probe checkpoint Task 4):
    - Navigate to a shop containing a Celestial booster pack.
    - Record the current hand_levels from the observation.
    - Buy the Celestial pack (buy action for the booster item).
    - Assert the observation phase transitions to 'booster_pack'.
    - Select a Planet card (select_pack_card_0).
    - Assert that the next observation's game_state.hand_levels shows at least
      one hand type with a level increased by 1 relative to the pre-pick snapshot.
    """
    from src.env.gymnasium_env import BalatroEnv  # noqa: PLC0415
    from src.env.action_space import ACTION_INDEX  # noqa: PLC0415

    env = BalatroEnv(deck="b_red", stake=1)
    try:
        obs_dict, _ = env.reset()

        # Locate a shop state with a Celestial pack and buy it.
        # The test driver loops until it finds such a shop (or times out).
        # In practice this is run manually after navigating to a Celestial pack.
        #
        # Step 1: assert we are in shop phase with a Celestial pack available.
        assert env._current_phase == "shop", (
            "SC-3: Expected shop phase at test start — navigate to a shop with a Celestial pack"
        )

        # Step 2: find and buy the Celestial pack (type==6 item whose pack_type
        # will be 'Celestial' once opened).  Use buy_0 if the first shop item is
        # a Celestial pack — adjust index if needed in a real run.
        from src.env.observation import parse_observation  # noqa: PLC0415

        raw = env._bridge.get_state()
        pre_obs = parse_observation(raw)
        pre_hand_levels = dict(pre_obs.game_state.hand_levels)

        # Buy index 0 (assumes the first shop item is the Celestial pack).
        buy_idx = ACTION_INDEX["buy_0"]
        obs_dict, _, _, _, _ = env.step(buy_idx)

        # Step 3: assert phase is now booster_pack.
        assert env._current_phase == "booster_pack", (
            f"SC-3: Expected booster_pack phase after buying Celestial pack; got {env._current_phase!r}"
        )

        # Step 4: select the first Planet card.
        select_idx = ACTION_INDEX["select_pack_card_0"]
        obs_dict, _, _, _, _ = env.step(select_idx)

        # Step 5: assert at least one hand_levels entry increased.
        raw2 = env._bridge.get_state()
        post_obs = parse_observation(raw2)
        post_hand_levels = dict(post_obs.game_state.hand_levels)

        leveled_up = any(
            post_hand_levels.get(hand, 1) > pre_hand_levels.get(hand, 1)
            for hand in post_hand_levels
        )
        assert leveled_up, (
            f"SC-3: No hand level increased after selecting a Planet card.\n"
            f"  Before: {pre_hand_levels}\n  After:  {post_hand_levels}"
        )
    finally:
        env.close()


@_LIVE_SKIP
def test_live_pack_standard_adds_deck_card():
    """SC-4 live: buying a Standard pack and selecting a playing card adds it to the deck.

    Acceptance gate (live only — gated behind probe checkpoint Task 4):
    - Navigate to a shop containing a Standard booster pack.
    - Record the deck card count from the pre-pick observation.
    - Buy the Standard pack and assert phase transitions to 'booster_pack'.
    - Select a playing card (select_pack_card_0).
    - Assert the deck card count (or membership) increased by 1 in the next observation.
    """
    from src.env.gymnasium_env import BalatroEnv  # noqa: PLC0415
    from src.env.action_space import ACTION_INDEX  # noqa: PLC0415
    from src.env.observation import parse_observation  # noqa: PLC0415

    env = BalatroEnv(deck="b_red", stake=1)
    try:
        obs_dict, _ = env.reset()

        assert env._current_phase == "shop", (
            "SC-4: Expected shop phase at test start — navigate to a shop with a Standard pack"
        )

        raw = env._bridge.get_state()
        pre_obs = parse_observation(raw)
        # Count deck cards (in_deck=True in the cards list)
        pre_deck_count = sum(1 for c in pre_obs.cards if c.in_deck)

        buy_idx = ACTION_INDEX["buy_0"]
        obs_dict, _, _, _, _ = env.step(buy_idx)

        assert env._current_phase == "booster_pack", (
            f"SC-4: Expected booster_pack phase after buying Standard pack; got {env._current_phase!r}"
        )

        select_idx = ACTION_INDEX["select_pack_card_0"]
        obs_dict, _, _, _, _ = env.step(select_idx)

        raw2 = env._bridge.get_state()
        post_obs = parse_observation(raw2)
        post_deck_count = sum(1 for c in post_obs.cards if c.in_deck)

        assert post_deck_count > pre_deck_count, (
            f"SC-4: Deck card count did not increase after selecting a Standard pack card.\n"
            f"  Before: {pre_deck_count} deck cards\n  After:  {post_deck_count} deck cards"
        )
    finally:
        env.close()


@_LIVE_SKIP
def test_live_pack_arcana_to_consumable():
    """SC-5 live: buying an Arcana pack and selecting a Tarot lands it in a consumable slot.

    Acceptance gate (live only — gated behind probe checkpoint Task 4):
    - Navigate to a shop containing an Arcana booster pack.
    - Record the consumable count from the pre-pick observation.
    - Buy the Arcana pack and assert phase transitions to 'booster_pack'.
    - Select the first Tarot card (select_pack_card_0), assuming a free consumable slot.
    - Assert a consumable slot is populated (count increased by 1) in the next observation.
    """
    from src.env.gymnasium_env import BalatroEnv  # noqa: PLC0415
    from src.env.action_space import ACTION_INDEX  # noqa: PLC0415
    from src.env.observation import parse_observation  # noqa: PLC0415

    env = BalatroEnv(deck="b_red", stake=1)
    try:
        obs_dict, _ = env.reset()

        assert env._current_phase == "shop", (
            "SC-5: Expected shop phase at test start — navigate to a shop with an Arcana pack"
        )

        raw = env._bridge.get_state()
        pre_obs = parse_observation(raw)
        pre_consumable_count = len(pre_obs.consumables)

        buy_idx = ACTION_INDEX["buy_0"]
        obs_dict, _, _, _, _ = env.step(buy_idx)

        assert env._current_phase == "booster_pack", (
            f"SC-5: Expected booster_pack phase after buying Arcana pack; got {env._current_phase!r}"
        )

        select_idx = ACTION_INDEX["select_pack_card_0"]
        obs_dict, _, _, _, _ = env.step(select_idx)

        raw2 = env._bridge.get_state()
        post_obs = parse_observation(raw2)
        post_consumable_count = len(post_obs.consumables)

        assert post_consumable_count > pre_consumable_count, (
            f"SC-5: Consumable count did not increase after selecting a Tarot from an Arcana pack.\n"
            f"  Before: {pre_consumable_count} consumables\n  After:  {post_consumable_count} consumables"
        )
    finally:
        env.close()


# ---------------------------------------------------------------------------
# ENV-04: Integration test — requires live Balatro (skip unless BALATRO_LIVE=1)
# ---------------------------------------------------------------------------


# Expected observation keys and dtypes (from observation_space, Plan 03 / RESEARCH.md)
_EXPECTED_OBS_DTYPES = {
    "cards": np.int32,
    "jokers": np.float32,
    "consumables": np.int32,
    "shop": np.int32,
    "pack": np.int32,
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
