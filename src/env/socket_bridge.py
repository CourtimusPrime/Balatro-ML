"""
Async TCP socket bridge between the Balatro mod (Lua/Steamodded) and the Python gym env.

Protocol: newline-delimited JSON over TCP.
  Game → Python : one JSON object per game event (draw, hand_played, shop_open, …)
  Python → Game : one JSON object per action (play_cards, discard, buy, …)

Ports:
  12345  RL agent
  12346  Human gameplay recording
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from typing import Any

from loguru import logger

AGENT_PORT: int = 12345
HUMAN_PORT: int = 12346


class SocketBridge:
    """
    Thread-safe bridge between the synchronous Gymnasium env and an async TCP server.

    The gym env calls the public methods (get_state, send_action) from its own thread.
    The asyncio event loop runs in a background daemon thread and handles all I/O.
    """

    def __init__(self, port: int = AGENT_PORT) -> None:
        self._port = port
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._server: asyncio.Server | None = None
        self._writer: asyncio.StreamWriter | None = None
        # Queue shared between the asyncio callback and the gym env thread.
        self._incoming: queue.Queue[dict[str, Any]] = queue.Queue()
        self._connected = threading.Event()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the async TCP server in a background daemon thread."""
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name=f"socket-bridge-{self._port}",
        )
        self._thread.start()
        logger.info(f"SocketBridge listening on 127.0.0.1:{self._port}")

    def stop(self) -> None:
        """Signal the event loop to stop and join the background thread."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("SocketBridge stopped")

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        assert self._loop is not None
        self._loop.run_until_complete(self._start_server())
        self._loop.run_forever()
        # run_forever() returns after loop.stop() — clean up before the thread exits.
        self._loop.run_until_complete(self._shutdown_server())
        # Cancel any in-flight tasks (e.g. _handle_client parked on the reader) and
        # let them unwind, otherwise loop.close() destroys them mid-await and asyncio
        # logs "Task was destroyed but it is pending!".
        self._loop.run_until_complete(self._cancel_pending_tasks())
        self._loop.close()

    async def _cancel_pending_tasks(self) -> None:
        pending = [t for t in asyncio.all_tasks(self._loop) if t is not asyncio.current_task()]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    async def _start_server(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            host="127.0.0.1",
            port=self._port,
            reuse_address=True,
        )

    async def _shutdown_server(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    # ------------------------------------------------------------------
    # Connection handler (runs on the asyncio thread)
    # ------------------------------------------------------------------

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        addr = writer.get_extra_info("peername")
        logger.info(f"Game connected from {addr}")

        # Only one client at a time; drop any previous connection.
        if self._writer is not None:
            logger.warning("New connection while one was active — closing old writer")
            self._writer.close()

        self._writer = writer
        self._connected.set()

        try:
            # asyncio.StreamReader async-iterates line by line (splits on \n).
            async for raw in reader:
                line = raw.strip()
                if not line:
                    continue
                try:
                    msg: dict[str, Any] = json.loads(line)
                    self._incoming.put_nowait(msg)
                    logger.debug(f"← {msg.get('event', '?')}")
                except json.JSONDecodeError as exc:
                    logger.warning(f"Bad JSON from game: {exc} | raw={line!r}")
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        finally:
            logger.info("Game disconnected")
            self._writer = None
            self._connected.clear()
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public interface — called from the gym env thread (synchronous)
    # ------------------------------------------------------------------

    def wait_for_connection(self, timeout: float = 60.0) -> bool:
        """Block until the game connects. Returns False if timeout expires."""
        return self._connected.wait(timeout=timeout)

    def get_state(self, timeout: float = 30.0) -> dict[str, Any]:
        """
        Block until the next game event arrives and return it.

        Raises:
            queue.Empty: if no message arrives within `timeout` seconds.
        """
        return self._incoming.get(timeout=timeout)

    def send_action(self, action: dict[str, Any], timeout: float = 5.0) -> None:
        """
        Send an action dict to the game as a newline-terminated JSON string.

        Thread-safe: schedules the write on the event loop and waits for it.

        Raises:
            RuntimeError: if the bridge is not running or no game is connected.
        """
        if self._loop is None or not self._loop.is_running():
            raise RuntimeError("SocketBridge is not started")
        if self._writer is None:
            raise RuntimeError("No game connected")
        future = asyncio.run_coroutine_threadsafe(self._write(action), self._loop)
        future.result(timeout=timeout)

    async def _write(self, action: dict[str, Any]) -> None:
        if self._writer is None:
            raise RuntimeError("No game connected")
        payload = json.dumps(action, separators=(",", ":")) + "\n"
        self._writer.write(payload.encode())
        await self._writer.drain()
        logger.debug(f"→ {action.get('action', '?')}")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    @property
    def port(self) -> int:
        return self._port

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "waiting"
        return f"SocketBridge(port={self._port}, {status})"
