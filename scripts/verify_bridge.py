"""
BRIDGE-05 probe script: connect to SocketBridge, receive one full observation,
decode it with parse_observation(), and print all field values for manual
comparison against the on-screen Balatro board.

Usage (in one terminal, before launching Balatro):
    uv run python scripts/verify_bridge.py

Then launch Balatro via Steam and start a new run. The script will print decoded
card/joker/game-state values and exit 0 on success.

Manual checklist (printed at start):
  [ ] Compare suit/value/enhancement/edition/seal for >= 3 cards on screen
      suit: 1=Spades  2=Clubs  3=Hearts  4=Diamonds  (0=stone)
      value: 2-10 as-is, 11=Jack, 12=Queen, 13=King, 14=Ace  (0=stone)
  [ ] After verifying values, quit Balatro and relaunch — confirm the script
      reconnects without crashing and prints a second set of observations.
"""

from __future__ import annotations

import queue
import sys

from loguru import logger

from src.env.socket_bridge import AGENT_PORT, SocketBridge
from src.env.observation import parse_observation

# ---------------------------------------------------------------------------
# Module-level timeout constants
# ---------------------------------------------------------------------------

CONNECTION_TIMEOUT: float = 60.0   # seconds to wait for Balatro to connect
OBSERVATION_TIMEOUT: float = 30.0  # seconds to wait for the first game event

# ---------------------------------------------------------------------------
# Suit/value human-readable references (for the manual checklist log)
# ---------------------------------------------------------------------------

_SUIT_LABELS = {0: "stone/absent", 1: "Spades", 2: "Clubs", 3: "Hearts", 4: "Diamonds"}
_VALUE_LABELS = {
    0: "stone/absent", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
    8: "8", 9: "9", 10: "10", 11: "Jack", 12: "Queen", 13: "King", 14: "Ace",
}


def _suit_label(v: int) -> str:
    return _SUIT_LABELS.get(v, str(v))


def _value_label(v: int) -> str:
    return _VALUE_LABELS.get(v, str(v))


# ---------------------------------------------------------------------------
# Main probe function
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("=" * 60)
    logger.info("BRIDGE-05 probe — manual verification checklist:")
    logger.info("  [ ] Compare suit/value/enhancement/edition/seal for >= 3 cards")
    logger.info("      suit  : 1=Spades 2=Clubs 3=Hearts 4=Diamonds (0=stone)")
    logger.info("      value : 2-10 as-is, 11=J 12=Q 13=K 14=A (0=stone)")
    logger.info("  [ ] After verifying, quit Balatro, relaunch, confirm reconnect")
    logger.info("=" * 60)

    bridge = SocketBridge(port=AGENT_PORT)
    bridge.start()

    logger.info(f"Waiting for Balatro to connect on port {AGENT_PORT} ...")

    connected = bridge.wait_for_connection(timeout=CONNECTION_TIMEOUT)
    if not connected:
        logger.error(
            f"No connection within {CONNECTION_TIMEOUT}s. "
            "Is Balatro running with the BalatroML mod loaded?"
        )
        bridge.stop()
        sys.exit(1)

    logger.info("Game connected. Waiting for first observation ...")

    try:
        raw = bridge.get_state(timeout=OBSERVATION_TIMEOUT)
    except queue.Empty:
        logger.error(
            f"No observation received within {OBSERVATION_TIMEOUT}s. "
            "Start a new run in Balatro to trigger a game-state event."
        )
        bridge.stop()
        sys.exit(1)

    logger.info(f"Raw payload received | event={raw.get('event')!r}")

    # Validate with Pydantic — let ValidationError propagate so the full error
    # is printed; it will also log the raw payload at ERROR level inside
    # parse_observation().
    obs = parse_observation(raw)

    # ------------------------------------------------------------------
    # Decoded field dump — compare against on-screen board
    # ------------------------------------------------------------------

    logger.info(f"Observation | event={obs.event!r}  phase={obs.phase!r}")

    logger.info(f"Cards in observation: {len(obs.cards)}")
    for i, card in enumerate(obs.cards):
        logger.info(
            f"  Card {i:>2}: suit={card.suit} ({_suit_label(card.suit)})"
            f"  value={card.value} ({_value_label(card.value)})"
            f"  enhancement={card.enhancement}"
            f"  edition={card.edition}"
            f"  seal={card.seal}"
            f"  debuffed={card.debuffed}"
            f"  in_hand={card.in_hand}"
        )

    logger.info(f"Jokers in observation: {len(obs.jokers)}")
    for i, joker in enumerate(obs.jokers):
        logger.info(
            f"  Joker {i:>2}: id={joker.id}"
            f"  edition={joker.edition}"
            f"  eternal={joker.eternal}"
            f"  sell_value={joker.sell_value}"
        )

    gs = obs.game_state
    logger.info(
        f"Game state: ante={gs.ante}"
        f"  chips_scored={gs.chips_scored}"
        f"  hands_remaining={gs.hands_remaining}"
        f"  money={gs.money}"
    )

    bridge.stop()
    logger.info("BRIDGE-05 probe complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()
