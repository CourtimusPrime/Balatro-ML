"""
probe_lua_funcs.py — diagnostic probe for G.FUNCS key verification (Phase 02-04).

Connects to the BalatroML socket bridge, sends a {"action": "probe_funcs"} request,
receives the response dict that contains the sorted list of all G.FUNCS keys from the
running Balatro instance, and checks whether the 5 assumed G.FUNCS names used by the
dispatcher are present.

Usage (with Balatro running and mod loaded):
    uv run python scripts/probe_lua_funcs.py

Exit codes:
    0 — probe_funcs_result received (regardless of CONFIRMED/MISSING outcome)
    1 — connection timeout or no response within timeout window

The 5 ASSUMED names this script validates:
    sell_card       (used in sell_joker branch)
    use_card        (used in use_consumable branch)
    reroll_shop     (used in reroll branch)
    select_blind    (used in select_blind branch)
    skip_blind      (used in skip_blind branch)

If any show MISSING, note the correct name from the printed key list and update
the matching branch in mod/bridge.lua before proceeding to Plan 05.
"""

from __future__ import annotations

import argparse
import queue
import sys
from pathlib import Path

# Make `src.*` importable when this script is run directly (not under pytest).
# Repo root is this file's parent's parent.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

from src.env.socket_bridge import AGENT_PORT, SocketBridge

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONNECTION_TIMEOUT: float = 30.0   # seconds to wait for Balatro to connect
RESPONSE_TIMEOUT: float = 10.0    # seconds to wait for probe_funcs_result

# The 5 assumed G.FUNCS names used in BML_Bridge.dispatch (mod/bridge.lua).
# These are ASSUMED based on balatrobot community research — not yet live-verified.
# Run this script against a live Balatro session to confirm or correct them.
ASSUMED_FUNCS: list[str] = [
    "sell_card",      # used in sell_joker branch  — ASSUMED (02-04 checkpoint)
    "use_card",       # used in use_consumable branch — ASSUMED (02-04 checkpoint)
    "reroll_shop",    # used in reroll branch — ASSUMED (02-04 checkpoint)
    "select_blind",   # used in select_blind branch — ASSUMED (02-04 checkpoint)
    "skip_blind",     # used in skip_blind branch — ASSUMED (02-04 checkpoint)
]

# ---------------------------------------------------------------------------
# Probe function
# ---------------------------------------------------------------------------


def probe_lua_funcs(port: int = AGENT_PORT) -> int:
    """Connect to SocketBridge, send probe_funcs action, print G.FUNCS keys.

    Returns:
        0 on success (probe_funcs_result received).
        1 on timeout or missing result.
    """
    bridge = SocketBridge(port=port)
    bridge.start()

    logger.info(f"Waiting for Balatro to connect on port {port} ...")
    connected = bridge.wait_for_connection(timeout=CONNECTION_TIMEOUT)
    if not connected:
        logger.error(
            f"No connection within {CONNECTION_TIMEOUT}s. "
            "Is Balatro running with the BalatroML mod loaded?"
        )
        bridge.stop()
        return 1

    logger.info("Game connected — sending probe_funcs action ...")
    bridge.send_action({"action": "probe_funcs"})

    # Poll for the probe_funcs_result event; may receive other events first.
    deadline = RESPONSE_TIMEOUT
    result: dict | None = None
    while deadline > 0:
        try:
            msg = bridge.get_state(timeout=min(deadline, RESPONSE_TIMEOUT))
            deadline -= RESPONSE_TIMEOUT
            if msg.get("event") == "probe_funcs_result":
                result = msg
                break
            else:
                logger.debug(f"Skipping non-probe event: {msg.get('event')!r}")
        except queue.Empty:
            break

    bridge.stop()

    if result is None:
        logger.warning(
            f"No probe_funcs_result received within {RESPONSE_TIMEOUT}s. "
            "Ensure the mod is updated and bridge.lua contains BML_Bridge.dispatch "
            "with the probe_funcs branch."
        )
        return 1

    funcs: list[str] = result.get("funcs", [])
    logger.info(f"G.FUNCS key count: {len(funcs)}")
    logger.info("=" * 60)
    logger.info("All G.FUNCS keys (sorted):")
    for key in sorted(funcs):
        logger.info(f"  {key}")
    logger.info("=" * 60)

    # Validate the 5 assumed names
    func_set = set(funcs)
    logger.info("Assumed G.FUNCS name verification:")
    all_confirmed = True
    for name in ASSUMED_FUNCS:
        if name in func_set:
            logger.info(f"  CONFIRMED  {name}")
        else:
            logger.warning(f"  MISSING    {name}  <-- update mod/bridge.lua before Plan 05")
            all_confirmed = False

    logger.info("=" * 60)
    if all_confirmed:
        logger.info("All 5 assumed G.FUNCS names CONFIRMED. Dispatcher is correct.")
    else:
        logger.warning(
            "One or more assumed names are MISSING. "
            "Check the full key list above for the correct spelling, "
            "then update the matching branch(es) in mod/bridge.lua."
        )

    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Probe G.FUNCS keys from a live Balatro session via the BalatroML socket bridge. "
            "Verifies the 5 assumed dispatcher names used in mod/bridge.lua."
        )
    )
    parser.add_argument(
        "--port",
        type=int,
        default=AGENT_PORT,
        help=f"TCP port the SocketBridge listens on (default: {AGENT_PORT})",
    )
    args = parser.parse_args()

    sys.exit(probe_lua_funcs(port=args.port))


if __name__ == "__main__":
    main()
