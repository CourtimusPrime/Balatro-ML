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
from pathlib import Path

# Make `src.*` importable when this script is run directly (python scripts/verify_bridge.py),
# not just under pytest. Repo root is this file's parent's parent.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

from src.env.socket_bridge import AGENT_PORT, SocketBridge
from src.env.observation import parse_observation

# ---------------------------------------------------------------------------
# Module-level timeout constants
# ---------------------------------------------------------------------------

CONNECTION_TIMEOUT: float = 300.0  # seconds to wait for Balatro to connect (manual-run friendly)
OBSERVATION_TIMEOUT: float = 300.0  # seconds to wait for each game event (manual-run friendly)

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

    logger.info("Game connected. Start a run / play a hand to trigger events.")
    logger.info("Each event prints a decoded snapshot below. Press Ctrl+C when done.")

    count = 0
    try:
        while True:
            try:
                raw = bridge.get_state(timeout=OBSERVATION_TIMEOUT)
            except queue.Empty:
                logger.error(
                    f"No observation within {OBSERVATION_TIMEOUT}s. "
                    "Start a run / play a hand in Balatro to trigger an event."
                )
                continue

            count += 1
            logger.info("-" * 60)
            logger.info(f"Observation #{count} | raw event={raw.get('event')!r}")
            if "debug_hand_names" in raw:
                logger.info(f"  debug_hand_names = {raw['debug_hand_names']}")

            # Validate with Pydantic — let ValidationError propagate so the full
            # error is printed; parse_observation logs the raw payload at ERROR.
            obs = parse_observation(raw)

            logger.info(f"  event={obs.event!r}  phase={obs.phase!r}")
            hand_cards = [c for c in obs.cards if c.in_hand]
            logger.info(f"  cards total={len(obs.cards)}  in hand={len(hand_cards)}")
            for i, card in enumerate(hand_cards):
                logger.info(
                    f"    hand[{i:>2}]: suit={card.suit} ({_suit_label(card.suit)})"
                    f"  value={card.value} ({_value_label(card.value)})"
                    f"  enhancement={card.enhancement}"
                    f"  edition={card.edition}"
                    f"  seal={card.seal}"
                    f"  debuffed={card.debuffed}"
                )

            if obs.jokers:
                logger.info(f"  jokers={len(obs.jokers)}")
                for i, joker in enumerate(obs.jokers):
                    logger.info(
                        f"    joker[{i:>2}]: id={joker.id}"
                        f"  edition={joker.edition}"
                        f"  eternal={joker.eternal}"
                        f"  sell_value={joker.sell_value}"
                    )

            gs = obs.game_state
            logger.info(
                f"  game_state: ante={gs.ante}"
                f"  chips_scored={gs.chips_scored}"
                f"  hands_remaining={gs.hands_remaining}"
                f"  money={gs.money}"
            )
    except KeyboardInterrupt:
        logger.info(f"\nBRIDGE-05 probe stopped — {count} observation(s) decoded.")
    finally:
        bridge.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
