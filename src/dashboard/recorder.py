"""Non-blocking dashboard write pipeline (DASH-02).

The ``Recorder`` mirrors :class:`src.env.socket_bridge.SocketBridge`'s async
pattern: producers on the simulation hot path enqueue rows with ``put_nowait``
(O(1), never blocking), and a single daemon **writer thread** drains the queue
in short, batched transactions onto its OWN sqlite3 connection (created inside
``_run`` — never shared across threads; 03-RESEARCH Pitfall 2).

Decoupling (locked decision A4): the recorder is a driver-loop callback, NOT a
gym Wrapper. ``BalatroEnv`` imports nothing from ``src/dashboard`` — the seed
script (03-04) owns a ``Recorder`` and feeds it ``start_run`` / ``on_step`` /
``end_run`` calls.

Raw-obs contract (locked decision D-raw / Pitfall 6): the recorder reads RAW
typed observation fields (``obs.game_state.chips_scored``, ``obs.last_hand``,
``obs.jokers``) — never the log-transformed numpy ``obs["game_state"]``. Raw
ints land in the DB; the dashboard applies the log scale itself.

Per-hand score (locked decision D3 / Pitfall 4): a hand's ``score`` is the
delta in cumulative ``chips_scored`` between consecutive ``hand_played`` events,
with the per-ante baseline reset on ``blind_start`` so a per-blind chip reset
never yields a negative score.

Truncation safety (Pitfall 5 / 7, gymnasium_env.py:210): ``step()`` returns
``info={}`` on a socket-timeout truncation, so the event is read everywhere via
``info.get("event")`` — never ``info["event"]`` — with a ``won=0`` / no-row
fallback when the key is absent.
"""

from __future__ import annotations

import queue
import threading
from datetime import datetime, timezone

from loguru import logger

from src.dashboard import db

# Poison pill: enqueued by close() to tell the writer thread to flush + exit.
_SENTINEL = object()


def _now() -> str:
    """UTC ISO-8601 timestamp string for the created_at / *_at columns."""
    return datetime.now(timezone.utc).isoformat()


class _RunState:
    """Per-run bookkeeping held on the recorder (producer side, hot path)."""

    __slots__ = ("hand_index", "max_ante", "baseline")

    def __init__(self, start_ante: int) -> None:
        self.hand_index = 0          # per-run incrementing hand counter (0-based)
        self.max_ante = start_ante   # per-run max(ante) -> runs.ante_reached
        self.baseline = 0            # per-ante chips_scored baseline (D3 delta)


class Recorder:
    """Queue-backed, daemon-threaded recorder for the dashboard DB.

    Public surface (driver-loop callback shape):
      start()                       -- init_db + spawn the daemon writer thread
      start_run(deck, stake) -> id  -- enqueue run_start; return a tracked run_id
      on_step(run_id, obs, info)    -- gate hand/ante rows; track max-ante + delta
      end_run(run_id, obs, info)    -- finalize run + enqueue joker_events
      record(kind, row)             -- put_nowait; O(1), never blocks
      flush()                       -- wait for the queue to fully drain
      close()                       -- enqueue sentinel + join the writer thread
    """

    def __init__(
        self,
        db_path: str = db.DB_PATH,
        batch_size: int = 50,
        flush_interval: float = 1.0,
    ) -> None:
        self._db_path = db_path
        self._batch_size = batch_size
        self._flush_interval = flush_interval

        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None

        # Producer-side per-run state. Keyed by the recorder-tracked run_id.
        self._runs: dict[int, _RunState] = {}
        # Recorder-local monotonic run_id counter (the DB autoincrements its own
        # PK; this id is what we thread through the queue rows and on_step calls).
        self._next_run_id = 1

    # ------------------------------------------------------------------
    # Lifecycle (mirror SocketBridge.start / stop)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Initialise the schema and spawn the background daemon writer thread."""
        db.init_db(self._db_path)
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="dashboard-recorder",
        )
        self._thread.start()
        logger.info(f"Recorder writer thread started (db={self._db_path})")

    def close(self) -> None:
        """Enqueue the sentinel and join the writer thread (lossless flush).

        Mirrors SocketBridge.stop join semantics: the writer drains everything
        already queued, flushes the final partial batch, then exits on the
        poison pill. join(timeout=5) bounds the wait.
        """
        if self._thread is None:
            return
        self._queue.put_nowait(_SENTINEL)
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            logger.warning("Recorder writer thread did not exit within 5s")
        else:
            logger.info("Recorder writer thread stopped")
        self._thread = None

    def flush(self) -> None:
        """Block until the writer has drained everything currently queued."""
        self._queue.join()

    # ------------------------------------------------------------------
    # Producer hot path (O(1), put_nowait — NEVER touches sqlite)
    # ------------------------------------------------------------------

    def record(self, kind: str, row: dict) -> None:
        """Enqueue one (kind, row) for the writer thread. O(1), never blocks."""
        self._queue.put_nowait((kind, row))

    def start_run(self, deck: str, stake: int) -> int:
        """Enqueue a run_start row; return the recorder-tracked run_id.

        The DB autoincrements its own ``runs.id``; the seed script drives a
        single run at a time, so the recorder-local id is kept in lockstep with
        the DB PK by inserting rows in submission order.
        """
        run_id = self._next_run_id
        self._next_run_id += 1
        self._runs[run_id] = _RunState(start_ante=0)
        self.record("run_start", {
            "run_id": run_id,
            "deck": deck,
            "stake": stake,
            "started_at": _now(),
        })
        return run_id

    def on_step(self, run_id: int, obs, info: dict, played: bool = False) -> None:
        """Process one env step: track max-ante, gate hand/ante rows, derive score.

        ``info`` may be ``{}`` on a socket-timeout truncation — the event is read
        via ``info.get("event")`` and a missing event produces no row.

        ``played`` signals the caller's action WAS a hand play (``commit_play``).
        The bridge protocol emits no distinct "hand_played" event — a play resolves
        to a ``draw``/``shop_open``/``run_*`` snapshot — so the caller, which knows
        the action it sent, tells the recorder when to record a hand_events row
        (from ``obs.last_hand`` + the per-blind chips delta).
        """
        state = self._runs.get(run_id)
        if state is None:
            # Defensive: an on_step before start_run shouldn't happen, but never
            # crash the seed loop — bootstrap a state so tracking still works.
            state = self._runs[run_id] = _RunState(start_ante=0)

        gs = obs.game_state
        # ante_reached tracking: update the per-run max on EVERY step (Pitfall 5).
        if gs.ante > state.max_ante:
            state.max_ante = gs.ante

        event = info.get("event")  # NOT info["event"] — info is {} on truncation

        if event == "blind_start":
            # New blind: capture the ante boundary and reset the delta baseline
            # (per-blind chip reset, D3) so the next hand's score isn't negative.
            self.record("ante", {
                "run_id": run_id,
                "ante": gs.ante,
                "blind_chips": gs.chips_needed,
                "chips_scored": gs.chips_scored,
                "created_at": _now(),
            })
            state.baseline = gs.chips_scored

        elif played:
            # A hand was played (caller's action == commit_play). The protocol has
            # no "hand_played" event, so we gate on the action, not info["event"].
            # Per-hand score = chips_scored delta vs the per-ante baseline.
            score = gs.chips_scored - state.baseline
            if score < 0:
                # Defensive against an unobserved blind reset: treat as a fresh
                # baseline rather than recording a negative score.
                score = gs.chips_scored
            state.baseline = gs.chips_scored

            last_hand = getattr(obs, "last_hand", None)
            hand_type = last_hand.hand_type if last_hand is not None else None
            chips = last_hand.chips if last_hand is not None else None
            mult = last_hand.mult if last_hand is not None else None
            n_cards = last_hand.n_cards if last_hand is not None else None

            self.record("hand", {
                "run_id": run_id,
                "ante": gs.ante,
                "hand_index": state.hand_index,
                "hand_type": hand_type,
                "chips": chips,
                "mult": mult,
                "n_cards": n_cards,
                "score": score,
                "created_at": _now(),
            })
            state.hand_index += 1

    def end_run(self, run_id: int, obs, info: dict) -> None:
        """Finalize the run and enqueue its joker_events.

        ``won = 1`` only when ``info.get("event") == "run_win"``; the event is
        ``None`` on a socket-timeout truncation (empty info) -> ``won = 0``,
        never raising KeyError (Pitfall 7).
        """
        state = self._runs.get(run_id) or _RunState(start_ante=0)
        gs = obs.game_state

        # Keep max-ante coherent with the terminal obs too.
        max_ante = max(state.max_ante, gs.ante)

        event = info.get("event")  # NOT info["event"] — empty info on truncation
        won = 1 if event == "run_win" else 0

        joker_ids = [j.id for j in getattr(obs, "jokers", [])]

        self.record("run_end", {
            "run_id": run_id,
            "final_score": gs.chips_scored,
            "won": won,
            "ante_reached": max_ante,
            "num_jokers": len(joker_ids),
            "ended_at": _now(),
        })
        # Always enqueue a joker_events row (executemany no-ops on an empty list).
        self.record("jokers", {
            "run_id": run_id,
            "joker_ids": joker_ids,
        })

        # Drop the per-run producer state — the run is done.
        self._runs.pop(run_id, None)

    # ------------------------------------------------------------------
    # Consumer (writer thread — owns its OWN connection; Pitfall 2)
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Drain the queue in batched transactions on a private connection.

        Blocks on ``queue.get(timeout=flush_interval)``; flushes the accumulated
        batch on size, on the interval timeout, and on the ``_SENTINEL`` poison
        pill (after which it drains anything still queued, then exits).
        """
        conn = db.connect(self._db_path)
        batch: list[tuple[str, dict]] = []
        try:
            while True:
                try:
                    item = self._queue.get(timeout=self._flush_interval)
                except queue.Empty:
                    # Interval elapsed with nothing new — flush what we have.
                    if batch:
                        self._flush(conn, batch)
                        batch = []
                    continue

                if item is _SENTINEL:
                    # Poison pill: mark it done, flush, then exit cleanly.
                    self._queue.task_done()
                    if batch:
                        self._flush(conn, batch)
                        batch = []
                    break

                batch.append(item)
                self._queue.task_done()
                if len(batch) >= self._batch_size:
                    self._flush(conn, batch)
                    batch = []
        finally:
            # Best-effort: never leak the writer's connection.
            try:
                if batch:
                    self._flush(conn, batch)
            finally:
                conn.close()

    def _flush(self, conn, batch: list[tuple[str, dict]]) -> None:
        """Write one batch in a single transaction; log + drop on failure."""
        try:
            db.flush_batch(conn, batch)
        except Exception:  # noqa: BLE001 — never let the writer thread die.
            logger.exception(f"Recorder flush_batch failed | n={len(batch)}")
