"""
Tests for SocketBridge.

Each test spins up the bridge, connects a mock TCP client, and exercises the
get_state / send_action interface. No mocking of the bridge internals — we
test the real asyncio server against real sockets.
"""

from __future__ import annotations

import asyncio
import gc
import json
import logging
import queue
import socket
import time

import pytest

from src.env.socket_bridge import AGENT_PORT, SocketBridge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _free_port() -> int:
    """Return an unused ephemeral TCP port on localhost.

    Tests bind this instead of AGENT_PORT (12345) so a live Balatro instance —
    whose mod auto-dials 12345 every frame — can't connect to the test server
    and make connection-state assertions non-deterministic.
    """
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


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
    """Start a SocketBridge on an ephemeral port and stop it after the test."""
    b = SocketBridge(port=_free_port())
    b.start()
    yield b
    b.stop()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_bridge_starts_and_stops():
    b = SocketBridge(port=_free_port())
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
        # Assert while the connection is still open — closing first races the
        # bridge's disconnect cleanup, which clears the _connected flag.
        loop = asyncio.get_event_loop()
        connected = await loop.run_in_executor(
            None, lambda: bridge.wait_for_connection(timeout=2.0)
        )
        assert connected
        writer.close()
        await writer.wait_closed()

    asyncio.run(go())


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
    assert str(bridge.port) in r


def test_stop_leaves_no_pending_tasks():
    """Regression: stop() while a client is connected must not destroy the
    in-flight _handle_client task mid-await ("Task was destroyed but it is
    pending!").

    Uses a raw blocking socket (not asyncio) so the connection stays genuinely
    open across stop() — _handle_client must be parked on the reader at teardown
    for the scenario to be exercised.

    Binds an ephemeral free port rather than AGENT_PORT so a live Balatro
    instance (which auto-dials 12345) can't connect to our server and make the
    assertion non-deterministic.
    """
    b = SocketBridge(port=_free_port())
    b.start()

    # The warning is emitted from Task.__del__ via the asyncio logger's exception
    # handler, which pytest's caplog doesn't reliably capture — attach a handler
    # to the "asyncio" logger directly.
    messages: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    handler = _Capture()
    asyncio_logger = logging.getLogger("asyncio")
    asyncio_logger.addHandler(handler)
    prev_level = asyncio_logger.level
    asyncio_logger.setLevel(logging.DEBUG)

    sock = socket.create_connection(("127.0.0.1", b.port), timeout=2.0)
    try:
        assert b.wait_for_connection(timeout=2.0)
        b.stop()
        # The warning fires from Task.__del__. The handler task stays reachable via
        # the bridge's event loop, so drop the bridge ref and force collection to
        # make __del__ run now (rather than at interpreter teardown).
        del b
        gc.collect()
        assert not any(
            "Task was destroyed but it is pending" in m for m in messages
        ), f"asyncio reported a destroyed pending task: {messages}"
    finally:
        sock.close()
        asyncio_logger.removeHandler(handler)
        asyncio_logger.setLevel(prev_level)
