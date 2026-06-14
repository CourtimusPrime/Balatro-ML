"""
Tests for src.env.observation Pydantic v2 models.

All tests run fully offline — no live game or socket required. Unit tests use
inline dicts for targeted validation checks; only the round-trip test loads
tests/fixtures/sample_state.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.env.observation import (
    CardObs,
    ConsumableObs,
    FullObservation,
    JokerObs,
    parse_observation,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers — minimal raw dicts for inline tests
# ---------------------------------------------------------------------------

def _minimal_card_raw() -> dict:
    """Return a minimal valid raw card dict (all 9 fields as Lua emits them)."""
    return {
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


def _minimal_joker_raw() -> dict:
    """Return a minimal valid raw joker dict (all 8 fields as Lua emits them)."""
    return {
        "id": "j_joker",
        "edition": "",
        "eternal": False,
        "perishable": False,
        "rental": False,
        "sell_value": 3,
        "counter": 0.0,
        "target_id": "",
    }


# ---------------------------------------------------------------------------
# CardObs tests
# ---------------------------------------------------------------------------

def test_card_obs_known_suit():
    """CardObs normalises a known suit string to its integer index."""
    raw = _minimal_card_raw()
    obs = CardObs.model_validate(raw)
    assert obs.suit == 1  # Spades → 1


def test_stone_card_forced_zero():
    """Stone Card enhancement forces suit=0 and value=0 regardless of raw values."""
    raw = _minimal_card_raw()
    raw["enhancement"] = "Stone Card"
    raw["suit"] = "Hearts"
    raw["value"] = "Ace"
    obs = CardObs.model_validate(raw)
    assert obs.suit == 0
    assert obs.value == 0


def test_card_obs_unknown_suit():
    """Unknown suit string resolves to -1 (sentinel for unknown keys)."""
    raw = _minimal_card_raw()
    raw["suit"] = "UnknownSuit"
    obs = CardObs.model_validate(raw)
    assert obs.suit == -1


def test_extra_field_raises():
    """CardObs with an extra unknown field raises ValidationError (extra='forbid')."""
    raw = _minimal_card_raw()
    raw["unexpected_field"] = "oops"
    with pytest.raises(ValidationError):
        CardObs.model_validate(raw)


# ---------------------------------------------------------------------------
# JokerObs tests
# ---------------------------------------------------------------------------

def test_joker_obs_unknown_id():
    """JokerObs with an unknown joker id string resolves to -1."""
    raw = _minimal_joker_raw()
    raw["id"] = "j_unknown_xyz"
    obs = JokerObs.model_validate(raw)
    assert obs.id == -1


# ---------------------------------------------------------------------------
# ConsumableObs tests
# ---------------------------------------------------------------------------

def test_consumable_type_mapping():
    """ConsumableObs with type='Tarot' normalises type to 0."""
    raw = {"id": "c_fool", "type": "Tarot"}
    obs = ConsumableObs.model_validate(raw)
    assert obs.type == 0


# ---------------------------------------------------------------------------
# FullObservation tests
# ---------------------------------------------------------------------------

def test_full_observation_from_fixture():
    """parse_observation validates the hand-crafted sample_state.json fixture."""
    raw = json.loads((FIXTURES_DIR / "sample_state.json").read_text())
    obs = parse_observation(raw)
    assert isinstance(obs, FullObservation)
    assert obs.event == "blind_start"


def test_malformed_payload_raises():
    """parse_observation({}) raises on missing required fields (logs at ERROR first)."""
    with pytest.raises(Exception):
        parse_observation({})


def test_missing_required_field_raises():
    """FullObservation missing the 'cards' field raises ValidationError."""
    with pytest.raises(ValidationError):
        FullObservation.model_validate({"jokers": [], "consumables": [], "shop": {"items": [], "reroll_cost": 0}, "game_state": {}, "phase": "playing", "event": "draw"})


def test_shop_empty_during_playing():
    """FullObservation with shop.items=[] validates correctly (playing phase)."""
    raw = json.loads((FIXTURES_DIR / "sample_state.json").read_text())
    # The fixture already has shop.items=[]
    obs = parse_observation(raw)
    assert obs.shop.items == []
    assert obs.shop.reroll_cost == 5


# ---------------------------------------------------------------------------
# Pack observation stubs (Wave 0 RED) — turned GREEN by Slice B (plan 02.1-03)
#
# These stubs assert the REAL intended pydantic/pack behaviour.
# They FAIL now because FullObservation has no `pack` field yet.
# Data-integrity contract: malformed pack payload MUST raise ValidationError
# (CLAUDE.md directive: malformed socket data must raise Pydantic ValidationError).
# ---------------------------------------------------------------------------


def test_pack_field_accepts_booster_payload():
    """FullObservation accepts a booster_pack payload with a non-empty pack list.

    RED: fails until Slice B adds `pack: list[ShopItemObs] = []` to FullObservation.
    """
    raw = json.loads((FIXTURES_DIR / "booster_pack_state.json").read_text())
    obs = parse_observation(raw)
    assert isinstance(obs, FullObservation)
    assert obs.phase == "booster_pack"
    # pack list must be accessible and non-empty (3 Tarot cards)
    assert hasattr(obs, "pack"), "FullObservation must have a pack attribute"
    assert len(obs.pack) == 3


def test_pack_field_default_empty_for_non_pack_phase():
    """Non-pack phase (playing) validates successfully with default-empty pack list.

    RED: fails until Slice B adds `pack: list[ShopItemObs] = []` (with default) to FullObservation.
    The default ensures existing sample_state.json and all non-pack fixtures keep validating.
    """
    raw = json.loads((FIXTURES_DIR / "sample_state.json").read_text())
    obs = parse_observation(raw)
    assert isinstance(obs, FullObservation)
    assert obs.phase == "playing"
    # pack must be present with default empty list when not in booster_pack phase
    assert hasattr(obs, "pack"), "FullObservation must have a pack attribute even in non-pack phases"
    assert obs.pack == [], "pack should default to [] for non-pack phase"


def test_pack_scalars_on_game_state():
    """GameStateObs exposes pack_picks_remaining and pack_type from a booster fixture.

    RED: fails until Slice B adds `pack_picks_remaining: int = 0` and `pack_type: int = -1`
    to GameStateObs.
    """
    raw = json.loads((FIXTURES_DIR / "booster_pack_state.json").read_text())
    obs = parse_observation(raw)
    gs = obs.game_state
    assert hasattr(gs, "pack_picks_remaining"), "GameStateObs must have pack_picks_remaining"
    assert hasattr(gs, "pack_type"), "GameStateObs must have pack_type"
    # Arcana → pack_type int (via PACK_TYPE_MAP: Arcana=0)
    assert gs.pack_picks_remaining == 1
    assert gs.pack_type == 0  # Arcana maps to 0


def test_pack_scalars_default_for_non_pack_phase():
    """GameStateObs pack scalars default to 0 / -1 when not in booster_pack phase.

    RED: fails until Slice B adds defaulted pack scalars to GameStateObs.
    Defaults ensure sample_state.json (which has no pack_picks_remaining / pack_type)
    keeps validating under extra='forbid'.
    """
    raw = json.loads((FIXTURES_DIR / "sample_state.json").read_text())
    obs = parse_observation(raw)
    gs = obs.game_state
    assert hasattr(gs, "pack_picks_remaining"), "GameStateObs must have pack_picks_remaining"
    assert hasattr(gs, "pack_type"), "GameStateObs must have pack_type"
    assert gs.pack_picks_remaining == 0, "pack_picks_remaining should default to 0"
    assert gs.pack_type == -1, "pack_type should default to -1 when no pack open"


def test_malformed_pack_row_raises_validation_error():
    """A malformed pack row (missing required field) raises pydantic ValidationError.

    RED: fails until Slice B adds pack field to FullObservation.
    Data-integrity contract from CLAUDE.md: malformed socket data MUST raise ValidationError.
    """
    raw = json.loads((FIXTURES_DIR / "booster_pack_state.json").read_text())
    # Corrupt the first pack row — remove required 'type' field
    raw["pack"][0] = {"id": "c_fool", "cost": 0}  # missing type, edition, enhancement, seal
    with pytest.raises(ValidationError):
        parse_observation(raw)


def test_standard_pack_base_type_id_minus_one():
    """Standard pack (Base type playing cards) validates with id==-1 (low=-1 Box contract).

    RED: fails until Slice B adds pack field to FullObservation (and gymnasium_env
    sets pack Box low=-1).
    Standard packs always show playing cards which resolve to id==-1 via _resolve_id_by_type.
    """
    raw = json.loads((FIXTURES_DIR / "booster_pack_standard.json").read_text())
    obs = parse_observation(raw)
    assert isinstance(obs, FullObservation)
    assert obs.phase == "booster_pack"
    assert hasattr(obs, "pack"), "FullObservation must have a pack attribute"
    # All pack cards are Base type → id resolves to -1
    for pack_card in obs.pack:
        assert pack_card.id == -1, f"Base pack card must have id==-1, got {pack_card.id}"
