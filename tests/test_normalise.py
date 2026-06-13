"""
Cross-check tests for src/data/normalise.py.

Asserts every string key emitted by mod/state.lua resolves to a known integer
in the corresponding map (BRIDGE-02).  Unknown keys must return -1, never raise.
"""

from __future__ import annotations

import pytest

from src.data.normalise import (
    BOSS_BLIND_ID_MAP,
    CONSUMABLE_TYPE_MAP,
    EDITION_MAP,
    ENHANCEMENT_MAP,
    JOKER_ID_MAP,
    PLANET_ID_MAP,
    SEAL_MAP,
    SPECTRAL_ID_MAP,
    SUIT_MAP,
    TAROT_ID_MAP,
    VALUE_MAP,
    VOUCHER_ID_MAP,
    _get,
)

# ---------------------------------------------------------------------------
# Sets mirroring the exact raw string keys that mod/state.lua emits on the wire
# ---------------------------------------------------------------------------

_STATE_LUA_SUIT_KEYS = {"Spades", "Clubs", "Hearts", "Diamonds"}

_STATE_LUA_VALUE_KEYS = {
    "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "Jack", "Queen", "King", "Ace",
}

_STATE_LUA_ENHANCEMENT_KEYS = {
    "Base", "Bonus Card", "Mult Card", "Wild Card", "Glass Card",
    "Steel Card", "Stone Card", "Gold Card", "Lucky Card",
}

_STATE_LUA_EDITION_KEYS = {"foil", "holo", "polychrome", "negative"}

_STATE_LUA_SEAL_KEYS = {"Gold", "Red", "Blue", "Purple"}

_STATE_LUA_CONSUMABLE_TYPE_KEYS = {"Tarot", "Planet", "Spectral"}


# ---------------------------------------------------------------------------
# Card attribute map tests
# ---------------------------------------------------------------------------

def test_suit_map_known_keys() -> None:
    for key in _STATE_LUA_SUIT_KEYS:
        assert SUIT_MAP[key] >= 1, f"SUIT_MAP[{key!r}] should be >= 1"


def test_value_map_known_keys() -> None:
    assert VALUE_MAP["2"] == 2
    assert VALUE_MAP["Ace"] == 14
    for key in _STATE_LUA_VALUE_KEYS:
        assert VALUE_MAP[key] >= 2, f"VALUE_MAP[{key!r}] should be >= 2"


def test_enhancement_map_known_keys() -> None:
    for key in _STATE_LUA_ENHANCEMENT_KEYS:
        assert key in ENHANCEMENT_MAP, f"{key!r} missing from ENHANCEMENT_MAP"
        assert ENHANCEMENT_MAP[key] >= 0


def test_edition_map_known_keys() -> None:
    for key in _STATE_LUA_EDITION_KEYS:
        assert key in EDITION_MAP, f"{key!r} missing from EDITION_MAP"
        assert EDITION_MAP[key] >= 1


def test_seal_map_known_keys() -> None:
    for key in _STATE_LUA_SEAL_KEYS:
        assert key in SEAL_MAP, f"{key!r} missing from SEAL_MAP"
        assert SEAL_MAP[key] >= 1


def test_consumable_type_map_known_keys() -> None:
    for key in _STATE_LUA_CONSUMABLE_TYPE_KEYS:
        assert key in CONSUMABLE_TYPE_MAP, f"{key!r} missing from CONSUMABLE_TYPE_MAP"
        assert CONSUMABLE_TYPE_MAP[key] >= 0


# ---------------------------------------------------------------------------
# ID map completeness tests
# ---------------------------------------------------------------------------

def test_joker_id_map_completeness() -> None:
    assert len(JOKER_ID_MAP) == 150, f"Expected 150 jokers, got {len(JOKER_ID_MAP)}"
    assert set(JOKER_ID_MAP.values()) == set(range(150)), "JOKER_ID_MAP values must be 0..149 with no gaps"


def test_tarot_id_map_completeness() -> None:
    assert len(TAROT_ID_MAP) == 22, f"Expected 22 tarots, got {len(TAROT_ID_MAP)}"
    assert set(TAROT_ID_MAP.values()) == set(range(22))


def test_planet_id_map_completeness() -> None:
    assert len(PLANET_ID_MAP) == 12, f"Expected 12 planets, got {len(PLANET_ID_MAP)}"
    assert set(PLANET_ID_MAP.values()) == set(range(12))


def test_spectral_id_map_completeness() -> None:
    assert len(SPECTRAL_ID_MAP) == 18, f"Expected 18 spectrals, got {len(SPECTRAL_ID_MAP)}"
    assert set(SPECTRAL_ID_MAP.values()) == set(range(18))


def test_voucher_id_map_completeness() -> None:
    assert len(VOUCHER_ID_MAP) == 32, f"Expected 32 vouchers, got {len(VOUCHER_ID_MAP)}"
    assert set(VOUCHER_ID_MAP.values()) == set(range(32))


def test_boss_blind_id_map_completeness() -> None:
    assert len(BOSS_BLIND_ID_MAP) == 28, f"Expected 28 boss blinds, got {len(BOSS_BLIND_ID_MAP)}"
    assert set(BOSS_BLIND_ID_MAP.values()) == set(range(28))


# ---------------------------------------------------------------------------
# _get helper contract tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("table", [
    SUIT_MAP, VALUE_MAP, ENHANCEMENT_MAP, EDITION_MAP, SEAL_MAP,
    JOKER_ID_MAP, TAROT_ID_MAP, PLANET_ID_MAP, SPECTRAL_ID_MAP,
    CONSUMABLE_TYPE_MAP, VOUCHER_ID_MAP, BOSS_BLIND_ID_MAP,
])
def test_unknown_key_returns_minus_one(table: dict[str, int]) -> None:
    assert _get(table, "__definitely_not_a_key__") == -1


def test_absent_sentinel_returns_zero() -> None:
    assert _get(SUIT_MAP, "", absent_sentinel=0) == 0
    assert _get(VALUE_MAP, "", absent_sentinel=0) == 0
    assert _get(EDITION_MAP, "", absent_sentinel=0) == 0
    assert _get(SEAL_MAP, "", absent_sentinel=0) == 0


def test_int_passthrough() -> None:
    assert _get(SUIT_MAP, 3) == 3
    assert _get(JOKER_ID_MAP, 0) == 0
    assert _get(JOKER_ID_MAP, 149) == 149


# ---------------------------------------------------------------------------
# Specific sentinel / value tests
# ---------------------------------------------------------------------------

def test_stone_card_enhancement() -> None:
    assert ENHANCEMENT_MAP["Stone Card"] == 6


def test_negative_edition_jokers_only() -> None:
    assert EDITION_MAP["negative"] == 4


def test_joker_boundary_keys() -> None:
    assert JOKER_ID_MAP["j_joker"] == 0
    assert JOKER_ID_MAP["j_perkeo"] == 149


def test_boss_blind_boundary_keys() -> None:
    assert BOSS_BLIND_ID_MAP["bl_hook"] == 0
    assert BOSS_BLIND_ID_MAP["bl_final_bell"] == 27


# ---------------------------------------------------------------------------
# Cross-check: every state.lua enum key resolves to >= 0 (BRIDGE-02)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lua_keys,table", [
    (_STATE_LUA_SUIT_KEYS, SUIT_MAP),
    (_STATE_LUA_VALUE_KEYS, VALUE_MAP),
    (_STATE_LUA_ENHANCEMENT_KEYS, ENHANCEMENT_MAP),
    (_STATE_LUA_EDITION_KEYS, EDITION_MAP),
    (_STATE_LUA_SEAL_KEYS, SEAL_MAP),
    (_STATE_LUA_CONSUMABLE_TYPE_KEYS, CONSUMABLE_TYPE_MAP),
])
def test_lua_key_coverage(lua_keys: set[str], table: dict[str, int]) -> None:
    """Every key that mod/state.lua will emit must resolve to a non-negative integer."""
    missing = [k for k in lua_keys if _get(table, k) < 0]
    assert not missing, f"Keys missing from map: {missing!r}"
