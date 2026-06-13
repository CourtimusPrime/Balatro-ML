"""
Tests for SocketBridge.

Each test spins up the bridge, connects a mock TCP client, and exercises the
get_state / send_action interface. No mocking of the bridge internals — we
test the real asyncio server against real sockets.
"""

from __future__ import annotations

import asyncio
import json
import queue
import time

import pytest

from src.env.socket_bridge import AGENT_PORT, SocketBridge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _connect(port: int) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Open a connection to the bridge (retries for up to 2 s)."""
    deadline = time.monotonic() + 2.0
    while True:
        try:
            return await asyncio.open_connection("127.0.0.1", port)
        except ConnectionRefusedError:
            if time.monotonic() > deadline:
                raise
            await asyncio.sleep(0.05)


async def _send(writer: asyncio.StreamWriter, msg: dict) -> None:
    writer.write((json.dumps(msg) + "\n").encode())
    await writer.drain()


async def _recv_line(reader: asyncio.StreamReader, timeout: float = 2.0) -> dict:
    data = await asyncio.wait_for(reader.readline(), timeout=timeout)
    return json.loads(data.strip())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def bridge():
    """Start a SocketBridge on the default agent port and stop it after the test."""
    b = SocketBridge(port=AGENT_PORT)
    b.start()
    yield b
    b.stop()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_bridge_starts_and_stops():
    b = SocketBridge(port=AGENT_PORT)
    b.start()
    time.sleep(0.1)
    b.stop()
    # No exceptions → pass


def test_wait_for_connection_timeout(bridge: SocketBridge):
    connected = bridge.wait_for_connection(timeout=0.1)
    assert not connected


def test_connection_detected(bridge: SocketBridge):
    async def go():
        reader, writer = await _connect(bridge.port)
        writer.close()

    asyncio.run(go())
    assert bridge.wait_for_connection(timeout=2.0)


def test_get_state_receives_json_event(bridge: SocketBridge):
    event = {"event": "draw", "hand": [{"suit": 1, "value": 14}]}

    async def go():
        reader, writer = await _connect(bridge.port)
        await _send(writer, event)
        writer.close()

    asyncio.run(go())

    msg = bridge.get_state(timeout=2.0)
    assert msg == event


def test_get_state_multiple_events(bridge: SocketBridge):
    events = [
        {"event": "blind_start", "chips_needed": 300},
        {"event": "draw", "hand": []},
        {"event": "hand_played", "score": 450},
    ]

    async def go():
        reader, writer = await _connect(bridge.port)
        for e in events:
            await _send(writer, e)
        writer.close()

    asyncio.run(go())

    received = []
    for _ in events:
        received.append(bridge.get_state(timeout=2.0))

    assert received == events


def test_get_state_raises_on_timeout(bridge: SocketBridge):
    with pytest.raises(queue.Empty):
        bridge.get_state(timeout=0.05)


def test_send_action_delivers_to_game(bridge: SocketBridge):
    action = {"action": "play_cards", "indices": [0, 1, 2]}

    async def go() -> dict:
        reader, writer = await _connect(bridge.port)
        loop = asyncio.get_event_loop()
        # Offload blocking bridge calls to a thread so the event loop stays live.
        await loop.run_in_executor(None, lambda: bridge.wait_for_connection(timeout=2.0))
        await loop.run_in_executor(None, lambda: bridge.send_action(action))
        received = await _recv_line(reader)
        writer.close()
        await writer.wait_closed()
        return received

    received = asyncio.run(go())
    assert received == action


def test_send_action_before_connection_raises(bridge: SocketBridge):
    with pytest.raises(RuntimeError, match="No game connected"):
        bridge.send_action({"action": "play_cards", "indices": []})


def test_send_action_before_start_raises():
    b = SocketBridge(port=AGENT_PORT)
    with pytest.raises(RuntimeError, match="not started"):
        b.send_action({"action": "play_cards", "indices": []})


def test_bad_json_is_skipped(bridge: SocketBridge):
    good = {"event": "draw", "hand": []}

    async def go():
        reader, writer = await _connect(bridge.port)
        # Send garbage first, then a valid message.
        writer.write(b"this is not json\n")
        await writer.drain()
        await _send(writer, good)
        writer.close()

    asyncio.run(go())

    # Only the valid message should appear; garbage is silently dropped.
    msg = bridge.get_state(timeout=2.0)
    assert msg == good
    with pytest.raises(queue.Empty):
        bridge.get_state(timeout=0.05)


def test_reconnect_after_disconnect(bridge: SocketBridge):
    event1 = {"event": "run_lose"}
    event2 = {"event": "blind_start", "chips_needed": 100}

    async def go():
        # First connection.
        reader, writer = await _connect(bridge.port)
        await _send(writer, event1)
        writer.close()
        await asyncio.sleep(0.1)
        # Second connection.
        reader2, writer2 = await _connect(bridge.port)
        await _send(writer2, event2)
        writer2.close()

    asyncio.run(go())

    msg1 = bridge.get_state(timeout=2.0)
    msg2 = bridge.get_state(timeout=2.0)
    assert msg1 == event1
    assert msg2 == event2


def test_is_connected_reflects_state(bridge: SocketBridge):
    assert not bridge.is_connected

    async def go():
        reader, writer = await _connect(bridge.port)
        await asyncio.sleep(0.05)
        assert bridge.is_connected
        writer.close()
        await asyncio.sleep(0.1)

    asyncio.run(go())
    # After disconnect the flag should clear.
    time.sleep(0.1)
    assert not bridge.is_connected


def test_repr(bridge: SocketBridge):
    r = repr(bridge)
    assert str(AGENT_PORT) in r
