"""
Hot-reload the BalatroML mod logic in a running game — no game restart.

The mod's bridge.lua bootstrap loads logic.lua (and state.lua) via SMODS.load_file
and wraps love.update once. This script starts a SocketBridge server, waits for the
running game's mod to connect, sends {"action":"reload"}, and waits for the mod's
reload_ok ack. The mod re-runs state.lua + logic.lua, redefining BML_State.* and
BML_Bridge.* in place; the TCP connection and persistent BML state survive.

Dev loop:
    # edit mod/logic.lua, then:
    cp mod/logic.lua mod/state.lua ~/.config/Balatro/Mods/BalatroML/
    uv run python scripts/reload_mod.py
    # ~seconds instead of a 60-90s game restart.

Usage:
    uv run python scripts/reload_mod.py [--port N]   (default port from AGENT_PORT / 12345)
"""

from __future__ import annotations

import argparse
import queue
import sys
from pathlib import Path

from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.env.socket_bridge import AGENT_PORT, SocketBridge

CONNECT_TIMEOUT: float = 30.0
ACK_TIMEOUT: float = 10.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Hot-reload the BalatroML mod logic.")
    parser.add_argument("--port", type=int, default=AGENT_PORT, help="bridge port")
    args = parser.parse_args()

    bridge = SocketBridge(port=args.port)
    bridge.start()
    logger.info(f"Waiting for Balatro to connect on port {args.port} ...")

    if not bridge.wait_for_connection(timeout=CONNECT_TIMEOUT):
        logger.error(
            f"No connection within {CONNECT_TIMEOUT}s. Is the game running with "
            "the updated BalatroML mod (bridge.lua bootstrap)?"
        )
        bridge.stop()
        sys.exit(1)

    bridge.send_action({"action": "reload"})
    logger.info("Sent reload — awaiting reload_ok ...")

    # Read events until the mod acks (ignore any unrelated snapshots in flight).
    while True:
        try:
            msg = bridge.get_state(timeout=ACK_TIMEOUT)
        except queue.Empty:
            logger.error(
                f"No reload_ok within {ACK_TIMEOUT}s — the mod may predate hot-reload "
                "support (re-launch the game once to load the new bridge.lua), or "
                "logic.lua failed to load (check the Balatro console for [BML] errors)."
            )
            bridge.stop()
            sys.exit(1)
        event = msg.get("event")
        if event == "reload_ok":
            logger.info("✅ Mod reloaded (state.lua + logic.lua).")
            break
        if event == "reload_error":
            logger.error("Mod reported reload_error — check the Balatro console for [BML] reload error.")
            bridge.stop()
            sys.exit(1)
        logger.debug(f"(ignoring in-flight event: {event!r})")

    bridge.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
