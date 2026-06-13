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
