"""
Action space definition for BalatroEnv.

N=37 flat Discrete space. ACTION_INDEX maps action name → int index.
decode_action(i) returns the JSON dict sent to Lua. build_mask(phase, ...) returns
a np.ndarray bool (37,) indicating which actions are legal in the current state.

Action index layout:
  Playing phase   (0-9):  toggle_card_0..7, commit_play, commit_discard
  Shop phase     (10-28):  buy_0..7, sell_joker_0..4, use_consumable_0..3, reroll, leave_shop
  Blind-select   (29-30):  select_blind, skip_blind
  Booster-pack   (31-36):  select_pack_card_0..4, skip_pack
"""

from __future__ import annotations

from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Index constants — the N=31 contract between action_space.py and gymnasium_env.py
# ---------------------------------------------------------------------------

# Playing phase (indices 0-9)
TOGGLE_CARD_BASE    = 0   # indices 0-7: toggle_card_i
COMMIT_PLAY         = 8
COMMIT_DISCARD      = 9

# Shop phase (indices 10-28)
BUY_BASE            = 10  # indices 10-17: buy_i
SELL_JOKER_BASE     = 18  # indices 18-22: sell_joker_i
USE_CONSUMABLE_BASE = 23  # indices 23-26: use_consumable_i
REROLL              = 27
LEAVE_SHOP          = 28

# Blind-select phase (indices 29-30)
SELECT_BLIND        = 29
SKIP_BLIND          = 30

# Booster-pack phase (indices 31-36)
SELECT_PACK_CARD_BASE = 31   # indices 31-35: select_pack_card_i (i in 0..4)
SKIP_PACK             = 36

N_ACTIONS           = 37

# ---------------------------------------------------------------------------
# Name → index mapping (31 entries)
# ---------------------------------------------------------------------------

ACTION_INDEX: dict[str, int] = {
    **{f"toggle_card_{i}": TOGGLE_CARD_BASE + i for i in range(8)},
    "commit_play":    COMMIT_PLAY,
    "commit_discard": COMMIT_DISCARD,
    **{f"buy_{i}": BUY_BASE + i for i in range(8)},
    **{f"sell_joker_{i}": SELL_JOKER_BASE + i for i in range(5)},
    **{f"use_consumable_{i}": USE_CONSUMABLE_BASE + i for i in range(4)},
    "reroll":        REROLL,
    "leave_shop":    LEAVE_SHOP,
    "select_blind":  SELECT_BLIND,
    "skip_blind":    SKIP_BLIND,
    **{f"select_pack_card_{i}": SELECT_PACK_CARD_BASE + i for i in range(5)},
    "skip_pack":     SKIP_PACK,
}

# Reverse lookup: index → decoded action dict (used by decode_action)
_INDEX_TO_ACTION: dict[int, dict[str, Any]] = {
    **{TOGGLE_CARD_BASE + i: {"action": "toggle_card", "index": i} for i in range(8)},
    COMMIT_PLAY:     {"action": "commit_play"},
    COMMIT_DISCARD:  {"action": "commit_discard"},
    **{BUY_BASE + i: {"action": "buy", "index": i} for i in range(8)},
    **{SELL_JOKER_BASE + i: {"action": "sell_joker", "index": i} for i in range(5)},
    **{USE_CONSUMABLE_BASE + i: {"action": "use_consumable", "index": i} for i in range(4)},
    REROLL:       {"action": "reroll"},
    LEAVE_SHOP:   {"action": "leave_shop"},
    SELECT_BLIND: {"action": "select_blind"},
    SKIP_BLIND:   {"action": "skip_blind"},
    **{SELECT_PACK_CARD_BASE + i: {"action": "select_pack_card", "index": i} for i in range(5)},
    SKIP_PACK:    {"action": "skip_pack"},
}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def _pick_is_placeable(
    card: dict,
    consumables: list,
    jokers: list,
    consumable_slots: int,
    joker_slots: int,
) -> bool:
    """Return True if *card* can be placed given current slot availability.

    Card type integers (from ShopItemObs.type, post-normalisation):
      0=joker, 1=tarot, 2=planet, 3=spectral, 4=playing_card/base

    Planet (2) and Base/playing-card (4) are always placeable.
    Tarot (1) / Spectral (3) need a free consumable slot.
    Joker (0, Buffoon) needs a free joker slot.
    Any other type defaults to False.
    """
    # Support both raw dict cards (from tests) and Pydantic model objects
    card_type = card.get("type") if isinstance(card, dict) else getattr(card, "type", None)

    # Normalise string type names (wire format before normalisation)
    _TYPE_MAP = {
        "Joker": 0, "Tarot": 1, "Planet": 2, "Spectral": 3,
        "Base": 4, "Celestial": 2,
    }
    if isinstance(card_type, str):
        card_type = _TYPE_MAP.get(card_type, -1)

    if card_type in (2, 4):
        # Planet and playing card: always placeable
        return True
    if card_type in (1, 3):
        # Tarot / Spectral: need a free consumable slot
        occupied = sum(1 for c in consumables if c is not None)
        return occupied < consumable_slots
    if card_type == 0:
        # Joker / Buffoon: need a free joker slot
        occupied = sum(1 for j in jokers if j is not None)
        return occupied < joker_slots
    return False


def decode_action(index: int) -> dict[str, Any]:
    """Return the JSON dict to send to Lua for action *index*.

    Raises ValueError if *index* is not in 0..36 (T-02-02 mitigation).
    """
    if index not in _INDEX_TO_ACTION:
        raise ValueError(
            f"Invalid action index {index!r}: must be in range 0..{N_ACTIONS - 1}"
        )
    return dict(_INDEX_TO_ACTION[index])


def build_mask(
    phase: str,
    hand_size: int,
    n_selected: int,
    discards_remaining: int,
    shop_items: list,           # list[ShopItemObs | None], max len 8
    jokers: list,               # list[JokerObs | None], max len 5; joker.eternal: bool
    consumables: list,          # list[ConsumableObs | None], max len 4
    money: int,
    reroll_cost: int,
    pack_cards: list = (),      # list[ShopItemObs | None | dict], max len 5
    pack_picks_remaining: int = 0,
    consumable_slots: int = 0,
    joker_slots: int = 0,
) -> np.ndarray:
    """Return boolean mask shape (37,) — True = legal action in current state.

    Phase routing:
      "playing"      — enables toggle_card_i for occupied slots, commit_play/discard
      "shop"         — enables buy/sell/use per slot contents and affordability,
                       reroll if affordable, leave_shop always
      "blind_select" — enables only select_blind and skip_blind
      "booster_pack" — enables select_pack_card_i for occupied+placeable slots
                       while pack_picks_remaining > 0; skip_pack always legal
      other/unknown  — all-False mask (safe default)
    """
    mask = np.zeros(N_ACTIONS, dtype=bool)

    if phase == "playing":
        # toggle_card_i: legal for each hand slot that has a card
        for i in range(min(hand_size, 8)):
            mask[TOGGLE_CARD_BASE + i] = True

        # commit_play: legal if 1-5 cards are currently selected
        if 1 <= n_selected <= 5:
            mask[COMMIT_PLAY] = True

        # commit_discard: legal if 1-5 cards selected AND discards remain
        if 1 <= n_selected <= 5 and discards_remaining > 0:
            mask[COMMIT_DISCARD] = True

    elif phase == "shop":
        # buy_i: legal if slot i has an item and we can afford it
        for i, item in enumerate(shop_items[:8]):
            item_cost = item.get("cost") if isinstance(item, dict) else getattr(item, "cost", None)
            if item is not None and item_cost is not None and money >= item_cost:
                mask[BUY_BASE + i] = True

        # sell_joker_i: legal if slot i has a non-eternal joker
        for i, joker in enumerate(jokers[:5]):
            if joker is not None and not joker.eternal:
                mask[SELL_JOKER_BASE + i] = True

        # use_consumable_i: legal if slot i has a consumable
        for i, cons in enumerate(consumables[:4]):
            if cons is not None:
                mask[USE_CONSUMABLE_BASE + i] = True

        # reroll: legal if we can afford it
        if money >= reroll_cost:
            mask[REROLL] = True

        # leave_shop: always legal in shop phase
        mask[LEAVE_SHOP] = True

    elif phase == "blind_select":
        mask[SELECT_BLIND] = True
        mask[SKIP_BLIND]   = True

    elif phase == "booster_pack":
        # select_pack_card_i: legal only for occupied+placeable slots while picks remain
        if pack_picks_remaining > 0:
            for i, card in enumerate(pack_cards[:5]):
                if card is not None and _pick_is_placeable(
                    card, consumables, jokers, consumable_slots, joker_slots
                ):
                    mask[SELECT_PACK_CARD_BASE + i] = True
        # skip_pack: ALWAYS legal — guaranteed terminal (SC-6); must NOT be nested under
        # the picks-remaining guard or the agent can jam with an all-False mask.
        mask[SKIP_PACK] = True

    return mask
