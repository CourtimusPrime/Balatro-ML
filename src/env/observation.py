"""
Pydantic v2 observation models. Receives raw dicts from SocketBridge.get_state()
and normalises string fields to integers via normalise.py maps. Raises
ValidationError on malformed payloads (logs raw payload at ERROR first). Stone
cards are forced to suit=0, value=0.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from loguru import logger

from src.data.normalise import (
    SUIT_MAP,
    VALUE_MAP,
    ENHANCEMENT_MAP,
    EDITION_MAP,
    SEAL_MAP,
    JOKER_ID_MAP,
    TAROT_ID_MAP,
    PLANET_ID_MAP,
    SPECTRAL_ID_MAP,
    CONSUMABLE_TYPE_MAP,
    PACK_TYPE_MAP,
    VOUCHER_ID_MAP,
    BOSS_BLIND_ID_MAP,
    _get,
)


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def _map(table: dict[str, int], v: object, absent_sentinel: int = -1) -> int:
    """Thin wrapper over _get for observation-internal usage."""
    return _get(table, v, absent_sentinel)


# ---------------------------------------------------------------------------
# CardObs
# ---------------------------------------------------------------------------

_STONE_CARD_ENHANCEMENT = 6  # ENHANCEMENT_MAP["Stone Card"]


class CardObs(BaseModel):
    """A single playing card in hand or deck."""

    model_config = ConfigDict(extra="forbid")

    suit:        int   # 0=stone/absent, 1=Spades, 2=Clubs, 3=Hearts, 4=Diamonds
    value:       int   # 0=stone/absent, 2=2 … 14=Ace
    enhancement: int   # 0=Base … 8=Lucky Card
    edition:     int   # 0=none, 1=foil, 2=holo, 3=polychrome, 4=negative
    seal:        int   # 0=none, 1=Gold, 2=Red, 3=Blue, 4=Purple
    debuffed:    bool
    selected:    bool
    in_hand:     bool
    in_deck:     bool

    @field_validator("suit", mode="before")
    @classmethod
    def _suit(cls, v: object) -> int:
        # Unknown strings resolve to -1; stone card forcing sets to 0 in model_validator
        return _map(SUIT_MAP, v, absent_sentinel=-1)

    @field_validator("value", mode="before")
    @classmethod
    def _value(cls, v: object) -> int:
        # Unknown strings resolve to -1; stone card forcing sets to 0 in model_validator
        return _map(VALUE_MAP, v, absent_sentinel=-1)

    @field_validator("enhancement", mode="before")
    @classmethod
    def _enhancement(cls, v: object) -> int:
        return _map(ENHANCEMENT_MAP, v, absent_sentinel=0)

    @field_validator("edition", mode="before")
    @classmethod
    def _edition(cls, v: object) -> int:
        return _map(EDITION_MAP, v, absent_sentinel=0)

    @field_validator("seal", mode="before")
    @classmethod
    def _seal(cls, v: object) -> int:
        return _map(SEAL_MAP, v, absent_sentinel=0)

    @model_validator(mode="after")
    def _force_stone_card(self) -> CardObs:
        """Stone cards have no suit or value — force both to 0."""
        if self.enhancement == _STONE_CARD_ENHANCEMENT:
            self.suit = 0
            self.value = 0
        return self


# ---------------------------------------------------------------------------
# JokerObs
# ---------------------------------------------------------------------------

class JokerObs(BaseModel):
    """A joker card in the joker slots."""

    model_config = ConfigDict(extra="forbid")

    id:          int    # JOKER_ID_MAP index; -1=unknown
    edition:     int    # 0=none, 1=foil, 2=holo, 3=polychrome, 4=negative
    eternal:     bool
    perishable:  bool
    rental:      bool
    sell_value:  int
    counter:     float
    target_id:   int    # -1 if no target (Blueprint/Brainstorm only)

    @field_validator("id", mode="before")
    @classmethod
    def _id(cls, v: object) -> int:
        return _map(JOKER_ID_MAP, v, absent_sentinel=-1)

    @field_validator("edition", mode="before")
    @classmethod
    def _edition(cls, v: object) -> int:
        return _map(EDITION_MAP, v, absent_sentinel=0)

    @field_validator("target_id", mode="before")
    @classmethod
    def _target_id(cls, v: object) -> int:
        return _map(JOKER_ID_MAP, v, absent_sentinel=-1)


# ---------------------------------------------------------------------------
# ConsumableObs
# ---------------------------------------------------------------------------

_CONSUMABLE_ID_MAPS: dict[str, dict[str, int]] = {
    "Tarot":    TAROT_ID_MAP,
    "Planet":   PLANET_ID_MAP,
    "Spectral": SPECTRAL_ID_MAP,
}


class ConsumableObs(BaseModel):
    """A consumable card (Tarot, Planet, or Spectral)."""

    model_config = ConfigDict(extra="forbid")

    id:   int   # TAROT/PLANET/SPECTRAL_ID_MAP index; -1=unknown
    type: int   # 0=Tarot, 1=Planet, 2=Spectral; -1=unknown

    @model_validator(mode="before")
    @classmethod
    def _resolve_id_by_type(cls, data: Any) -> Any:
        """Dispatch id to the correct map based on the raw type string."""
        if not isinstance(data, dict):
            return data
        raw_type = data.get("type", "")
        raw_id   = data.get("id", "")
        id_map = _CONSUMABLE_ID_MAPS.get(str(raw_type))
        if id_map is not None:
            resolved_id = _map(id_map, raw_id, absent_sentinel=-1)
        else:
            resolved_id = -1
        return {**data, "id": resolved_id}

    @field_validator("type", mode="before")
    @classmethod
    def _type(cls, v: object) -> int:
        return _map(CONSUMABLE_TYPE_MAP, v, absent_sentinel=-1)


# ---------------------------------------------------------------------------
# ShopItemObs
# ---------------------------------------------------------------------------

_SHOP_TYPE_MAP: dict[str, int] = {
    "Joker":        0,
    "Tarot":        1,
    "Planet":       2,
    "Spectral":     3,
    "Base":         4,  # playing card
    "Voucher":      5,
    "Booster":      6,
}

_SHOP_ITEM_ID_MAPS: dict[str, dict[str, int]] = {
    "Joker":    JOKER_ID_MAP,
    "Tarot":    TAROT_ID_MAP,
    "Planet":   PLANET_ID_MAP,
    "Spectral": SPECTRAL_ID_MAP,
    "Voucher":  VOUCHER_ID_MAP,
}


class ShopItemObs(BaseModel):
    """A single item in the shop."""

    model_config = ConfigDict(extra="forbid")

    type:        int   # 0=joker,1=tarot,2=planet,3=spectral,4=playing_card,5=voucher,6=booster_pack
    id:          int   # appropriate map index; -1=unknown
    cost:        int
    edition:     int   # 0=none, 1=foil, 2=holo, 3=polychrome, 4=negative
    enhancement: int   # 0=none/Base
    seal:        int   # 0=none

    @model_validator(mode="before")
    @classmethod
    def _resolve_id_by_type(cls, data: Any) -> Any:
        """Dispatch id to the correct map based on the raw type string."""
        if not isinstance(data, dict):
            return data
        raw_type = data.get("type", "")
        raw_id   = data.get("id", "")
        id_map = _SHOP_ITEM_ID_MAPS.get(str(raw_type))
        if id_map is not None:
            resolved_id = _map(id_map, raw_id, absent_sentinel=-1)
        else:
            resolved_id = -1
        return {**data, "id": resolved_id}

    @field_validator("type", mode="before")
    @classmethod
    def _type(cls, v: object) -> int:
        return _map(_SHOP_TYPE_MAP, v, absent_sentinel=-1)

    @field_validator("edition", mode="before")
    @classmethod
    def _edition(cls, v: object) -> int:
        return _map(EDITION_MAP, v, absent_sentinel=0)

    @field_validator("enhancement", mode="before")
    @classmethod
    def _enhancement(cls, v: object) -> int:
        return _map(ENHANCEMENT_MAP, v, absent_sentinel=0)

    @field_validator("seal", mode="before")
    @classmethod
    def _seal(cls, v: object) -> int:
        return _map(SEAL_MAP, v, absent_sentinel=0)


# ---------------------------------------------------------------------------
# ShopObs
# ---------------------------------------------------------------------------

class ShopObs(BaseModel):
    """The shop — items and reroll cost."""

    model_config = ConfigDict(extra="forbid")

    items:       list[ShopItemObs]
    reroll_cost: int


# ---------------------------------------------------------------------------
# GameStateObs
# ---------------------------------------------------------------------------

class GameStateObs(BaseModel):
    """Scalar game-state fields."""

    model_config = ConfigDict(extra="forbid")

    ante:               int
    blind:              int   # 0=Small, 1=Big, 2=Boss
    blind_name:         str   # raw string; not normalised
    chips_needed:       int
    chips_scored:       int
    hands_remaining:    int
    discards_remaining: int
    money:              int
    hand_size:          int
    joker_slots:        int
    consumable_slots:   int
    hand_levels:        dict[str, int]   # hand name → level (raw string keys)
    reroll_cost:        int
    pack_picks_remaining: int = 0   # remaining picks in open booster pack; 0 outside pack phase
    pack_type:          int = -1    # PACK_TYPE_MAP int; -1 when no pack open

    @field_validator("pack_type", mode="before")
    @classmethod
    def _pack_type(cls, v: object) -> int:
        if isinstance(v, str):
            return _map(PACK_TYPE_MAP, v, absent_sentinel=-1)
        return _map(PACK_TYPE_MAP, v, absent_sentinel=-1)


# ---------------------------------------------------------------------------
# LastHandObs
# ---------------------------------------------------------------------------

class LastHandObs(BaseModel):
    """The scored poker hand on a `hand_played` event (Panels 5 & 6).

    Emitted by mod/state.lua only on `event == "hand_played"`; absent (None)
    for every other event. Carries the scored poker hand name plus the per-hand
    chips and mult so the dashboard's best-run hand-by-hand panel and the
    hand-type-frequency panel render real values (03-RESEARCH Pitfall 4).
    """

    model_config = ConfigDict(extra="forbid")

    hand_type: str   # raw poker hand name (e.g. "Pair", "Flush"); not normalised
    chips:     int   # per-hand chips applied
    mult:      int   # per-hand mult applied
    n_cards:   int   # number of scoring cards in the played hand


# ---------------------------------------------------------------------------
# FullObservation
# ---------------------------------------------------------------------------

class FullObservation(BaseModel):
    """Complete observation from a single game event."""

    model_config = ConfigDict(extra="forbid")

    cards:       list[CardObs]
    jokers:      list[JokerObs]
    consumables: list[ConsumableObs]
    shop:        ShopObs
    game_state:  GameStateObs
    phase:       str   # "playing" | "shop" | "blind_select" | "booster_pack"
    event:       str   # "draw" | "hand_played" | "discard" | "blind_start" | ...
    pack:        list[ShopItemObs] = []   # offered cards in open booster pack; [] outside pack phase
    last_hand:   LastHandObs | None = None   # scored poker hand on hand_played; None otherwise


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_observation(raw: dict) -> FullObservation:
    """Validate and normalise a raw observation dict from SocketBridge.get_state().

    Logs the raw payload at ERROR level before re-raising on any failure.
    """
    try:
        return FullObservation.model_validate(raw)
    except Exception:
        logger.error(f"Malformed observation | raw={raw!r}")
        raise
