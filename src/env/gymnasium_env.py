"""
BalatroEnv: gymnasium.Env wrapping SocketBridge for MaskablePPO training.

Observation space: spaces.Dict with five Box sub-spaces (cards/jokers/consumables/
shop/game_state). Action space: spaces.Discrete(31) with action_masks() method.
Protocol: send one action dict → drain until next actionable event.

Lifecycle: SocketBridge is started in __init__ and stopped in close().
"""

from __future__ import annotations

import math
import queue
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from loguru import logger

from src.env.action_space import N_ACTIONS, build_mask, decode_action
from src.env.observation import FullObservation, parse_observation
from src.env.reward import compute_reward
from src.env.socket_bridge import SocketBridge


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

TERMINAL_EVENTS: frozenset[str] = frozenset({"run_win", "run_lose"})

ACTIONABLE_EVENTS: frozenset[str] = frozenset(
    {
        "draw",
        "hand_played",
        "discard",
        "blind_start",
        "shop_open",
        "shop_buy",
        "shop_close",
        "run_win",
        "run_lose",
    }
)

HAND_LEVEL_ORDER: list[str] = [
    "High Card",
    "Pair",
    "Two Pair",
    "Three of a Kind",
    "Straight",
    "Flush",
    "Full House",
    "Four of a Kind",
    "Straight Flush",
    "Royal Flush",
    "Five of a Kind",
    "Flush House",
    "Flush Five",
]

MAX_STEPS: int = 1000


# ---------------------------------------------------------------------------
# BalatroEnv
# ---------------------------------------------------------------------------


class BalatroEnv(gym.Env):
    """Gymnasium environment wrapping a live Balatro game via SocketBridge.

    Supports MaskablePPO from sb3-contrib via action_masks() method.
    Observation space is a spaces.Dict with five Box sub-spaces ready for
    MultiInputPolicy.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        deck: str = "b_red",
        stake: int = 1,
        port: int = 12345,
    ) -> None:
        super().__init__()
        self._deck = deck
        self._stake = stake

        self._bridge = SocketBridge(port=port)
        self._bridge.start()

        # Observation space — five zero-padded Box sub-spaces
        self.observation_space = spaces.Dict(
            {
                "cards": spaces.Box(
                    low=0, high=14, shape=(64, 9), dtype=np.int32
                ),
                "jokers": spaces.Box(
                    low=-1, high=149, shape=(10, 8), dtype=np.float32
                ),
                "consumables": spaces.Box(
                    low=0, high=21, shape=(4, 2), dtype=np.int32
                ),
                "shop": spaces.Box(
                    low=0, high=149, shape=(8, 6), dtype=np.int32
                ),
                "game_state": spaces.Box(
                    low=-1e6, high=1e6, shape=(26,), dtype=np.float32
                ),
            }
        )
        self.action_space = spaces.Discrete(N_ACTIONS)

        # State — initialise so action_masks() never sees unset phase (Pitfall 3)
        self._current_phase: str = "playing"
        self._step_count: int = 0
        self._selected_cards: list[int] = []
        self._last_obs: FullObservation | None = None

        # Zero-padded observation dict (matches observation_space shape/dtype)
        self._current_obs: dict[str, np.ndarray] = self._zero_obs()

        logger.info(
            f"BalatroEnv initialised | deck={deck} stake={stake} port={port}"
        )

    # ------------------------------------------------------------------
    # gymnasium.Env interface
    # ------------------------------------------------------------------

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[dict[str, np.ndarray], dict]:
        super().reset(seed=seed)
        self._step_count = 0
        self._selected_cards = []

        # Wait for the game to (re)connect before issuing any action. The mod
        # reconnects every frame, but start() returns before the TCP handshake
        # completes — without this, the first reset() races the connection and
        # send_action() raises "No game connected".
        if not self._bridge.wait_for_connection(timeout=30.0):
            raise RuntimeError(
                "Balatro did not connect within 30s — is the game running "
                "with the BalatroML mod loaded?"
            )

        # Drain stale events from previous episode (Pitfall 2)
        while True:
            try:
                self._bridge._incoming.get_nowait()
            except queue.Empty:
                break

        # Tell Lua to start a new run
        self._bridge.send_action(
            {"action": "start_run", "deck": self._deck, "stake": self._stake}
        )

        # Block until blind_start or draw arrives (up to 30 s)
        raw = self._bridge.get_state(timeout=30.0)
        obs = parse_observation(raw)
        self._last_obs = obs
        self._current_phase = obs.phase
        self._current_obs = self._obs_to_dict(obs)
        return self._current_obs, {}

    def step(
        self, action: int
    ) -> tuple[dict[str, np.ndarray], float, bool, bool, dict]:
        self._step_count += 1
        action_dict = decode_action(action)
        logger.debug(f"step action={action} ({action_dict.get('action', '?')})")

        self._bridge.send_action(action_dict)

        # Track toggle_card selections locally
        if action_dict.get("action") == "toggle_card":
            idx = action_dict["index"]
            if idx in self._selected_cards:
                self._selected_cards.remove(idx)
            else:
                self._selected_cards.append(idx)

        # Drain until we receive an actionable event (Pitfall 1)
        while True:
            try:
                raw = self._bridge.get_state(timeout=5.0)
            except queue.Empty:
                logger.warning("Socket timeout in step() — truncating episode")
                return self._current_obs, 0.0, False, True, {}
            if raw.get("event") in ACTIONABLE_EVENTS:
                break

        obs = parse_observation(raw)
        terminated = raw["event"] in TERMINAL_EVENTS
        reward = self._compute_reward(obs, terminated, raw["event"])

        self._last_obs = obs
        self._current_phase = obs.phase
        self._current_obs = self._obs_to_dict(obs)

        # Clear selected cards after commit actions
        if action_dict.get("action") in ("commit_play", "commit_discard"):
            self._selected_cards = []

        if self._step_count >= MAX_STEPS and not terminated:
            return self._current_obs, reward, False, True, {"event": raw["event"]}

        return self._current_obs, reward, terminated, False, {"event": raw["event"]}

    def action_masks(self) -> np.ndarray:
        """Return boolean mask shape (31,) — True = legal action.

        Safe to call before reset(): _current_phase defaults to 'playing',
        _last_obs defaults to None → build_mask receives empty lists and 0 counts.
        """
        if self._last_obs is None:
            # Safe defaults before first reset()
            return build_mask(
                phase=self._current_phase,
                hand_size=0,
                n_selected=0,
                discards_remaining=0,
                shop_items=[],
                jokers=[],
                consumables=[],
                money=0,
                reroll_cost=0,
            )

        gs = self._last_obs.game_state
        return build_mask(
            phase=self._current_phase,
            hand_size=gs.hand_size,
            n_selected=len(self._selected_cards),
            discards_remaining=gs.discards_remaining,
            shop_items=self._last_obs.shop.items[:8],
            jokers=self._last_obs.jokers[:5],
            consumables=self._last_obs.consumables[:4],
            money=gs.money,
            reroll_cost=self._last_obs.shop.reroll_cost,
        )

    def close(self) -> None:
        self._bridge.stop()
        logger.info("BalatroEnv closed")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _zero_obs(self) -> dict[str, np.ndarray]:
        """Return a zero-padded observation dict matching observation_space."""
        return {
            "cards": np.zeros((64, 9), dtype=np.int32),
            "jokers": np.zeros((10, 8), dtype=np.float32),
            "consumables": np.zeros((4, 2), dtype=np.int32),
            "shop": np.zeros((8, 6), dtype=np.int32),
            "game_state": np.zeros((26,), dtype=np.float32),
        }

    def _obs_to_dict(self, obs: FullObservation) -> dict[str, np.ndarray]:
        """Convert a FullObservation to a padded numpy dict."""
        result = self._zero_obs()

        # cards: (64, 9) int32 — [suit, value, enhancement, edition, seal,
        #                          debuffed, selected, in_hand, in_deck]
        for i, card in enumerate(obs.cards[:64]):
            result["cards"][i] = [
                card.suit,
                card.value,
                card.enhancement,
                card.edition,
                card.seal,
                int(card.debuffed),
                int(card.selected),
                int(card.in_hand),
                int(card.in_deck),
            ]

        # jokers: (10, 8) float32 — [id, edition, eternal, perishable, rental,
        #                             sell_value, counter, target_id]
        for i, joker in enumerate(obs.jokers[:10]):
            result["jokers"][i] = [
                joker.id,
                joker.edition,
                float(joker.eternal),
                float(joker.perishable),
                float(joker.rental),
                joker.sell_value,
                joker.counter,
                joker.target_id,
            ]

        # consumables: (4, 2) int32 — [id, type]
        for i, cons in enumerate(obs.consumables[:4]):
            result["consumables"][i] = [cons.id, cons.type]

        # shop: (8, 6) int32 — [type, id, cost, edition, enhancement, seal]
        for i, item in enumerate(obs.shop.items[:8]):
            result["shop"][i] = [
                item.type,
                item.id,
                item.cost,
                item.edition,
                item.enhancement,
                item.seal,
            ]

        # game_state: (26,) float32
        # [0]   ante
        # [1]   blind (0/1/2)
        # [2]   log(chips_needed + 1)
        # [3]   log(chips_scored + 1)
        # [4]   hands_remaining
        # [5]   discards_remaining
        # [6]   log(money + 1)
        # [7]   hand_size
        # [8]   joker_slots
        # [9]   consumable_slots
        # [10-22] hand_levels for 13 types (HAND_LEVEL_ORDER)
        # [23-25] phase one-hot [playing, shop, blind_select]
        # NOTE: reroll_cost is NOT encoded here (Pitfall 6)
        gs = obs.game_state
        gv = result["game_state"]
        gv[0] = gs.ante
        gv[1] = gs.blind
        gv[2] = math.log(gs.chips_needed + 1)
        gv[3] = math.log(gs.chips_scored + 1)
        gv[4] = gs.hands_remaining
        gv[5] = gs.discards_remaining
        gv[6] = math.log(max(0, gs.money) + 1)
        gv[7] = gs.hand_size
        gv[8] = gs.joker_slots
        gv[9] = gs.consumable_slots
        for j, hand_name in enumerate(HAND_LEVEL_ORDER):
            gv[10 + j] = gs.hand_levels.get(hand_name, 1)
        # phase one-hot
        phase_idx = {"playing": 0, "shop": 1, "blind_select": 2}.get(obs.phase, 0)
        gv[23 + phase_idx] = 1.0

        return result

    def _compute_reward(
        self,
        obs: FullObservation,
        terminated: bool,
        event: str,
    ) -> float:
        """Compute scalar reward from the observation after an env step."""
        gs = obs.game_state
        final_score: int | None = gs.chips_scored if terminated else None

        return compute_reward(
            chips_scored=gs.chips_scored,
            margin_over_blind=gs.chips_scored - gs.chips_needed,
            hand_type_level_gain=0.0,
            deck_size_reduction=0.0,
            final_score=final_score,
        )
