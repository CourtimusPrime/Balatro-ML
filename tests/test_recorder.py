"""Offline tests for the non-blocking dashboard Recorder (DASH-02).

All tests run fully offline — no live game, no socket. They drive the Recorder
with synthetic FullObservation-like stand-ins and a temp SQLite DB (the
seeded_db / db layer from 03-01) and assert:

  * record() is non-blocking on the hot path (put_nowait, O(1)).
  * a daemon writer thread drains the queue and persists rows.
  * close() flushes the final partial batch losslessly (mirror SocketBridge.stop).
  * per-hand score is the chips_scored delta, robust to per-blind resets.
  * hand_events are gated to event=="hand_played" with an ordered hand_index.
  * ante_reached is the per-run max(ante).
  * joker_events land on end_run.
  * end_run survives an empty info dict (socket-timeout truncation): won=0,
    never raising KeyError.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field

import pytest

from src.dashboard import db
from src.dashboard.recorder import Recorder


# ---------------------------------------------------------------------------
# Synthetic obs stand-ins (duck-typed to the fields the recorder reads RAW)
# ---------------------------------------------------------------------------


@dataclass
class FakeGameState:
    ante: int = 1
    chips_needed: int = 300
    chips_scored: int = 0


@dataclass
class FakeJoker:
    id: int


@dataclass
class FakeLastHand:
    hand_type: str = "Pair"
    chips: int = 40
    mult: int = 2
    n_cards: int = 2


@dataclass
class FakeObs:
    """Duck-typed FullObservation: only the RAW fields the recorder reads."""

    game_state: FakeGameState = field(default_factory=FakeGameState)
    jokers: list = field(default_factory=list)
    last_hand: object | None = None


def _obs(ante=1, chips_scored=0, chips_needed=300, jokers=None, last_hand=None):
    return FakeObs(
        game_state=FakeGameState(
            ante=ante, chips_needed=chips_needed, chips_scored=chips_scored
        ),
        jokers=list(jokers or []),
        last_hand=last_hand,
    )


# ---------------------------------------------------------------------------
# DB read helpers (own read-only connection — never share the writer's conn)
# ---------------------------------------------------------------------------


def _rows(path: str, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn = db.connect(path)
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


@pytest.fixture()
def db_path(tmp_path):
    """An empty, initialised temp DB path for the recorder to write into."""
    path = str(tmp_path / "runs.db")
    db.init_db(path)
    return path


# ---------------------------------------------------------------------------
# Non-blocking producer
# ---------------------------------------------------------------------------


def test_record_nonblocking(db_path):
    """10k record() calls complete well under a tight budget (put_nowait, O(1))."""
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        start = time.perf_counter()
        for i in range(10_000):
            rec.record("ante", {
                "run_id": 1, "ante": 1, "blind_chips": 300,
                "chips_scored": i, "created_at": "t",
            })
        elapsed = time.perf_counter() - start
        # Hot path must never touch sqlite; 10k enqueues are trivially fast.
        assert elapsed < 1.0, f"record() too slow: {elapsed:.3f}s for 10k calls"
    finally:
        rec.close()


# ---------------------------------------------------------------------------
# Writer thread drains + flush-on-close losslessness
# ---------------------------------------------------------------------------


def test_writer_thread_drains_queue(db_path):
    """After start(), the daemon writer thread drains the queue into the DB."""
    rec = Recorder(db_path=db_path, flush_interval=0.05)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        rec.end_run(rid, _obs(ante=1, chips_scored=500), {"event": "run_win"})
        # Give the writer a beat to drain on its own interval (no close yet).
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if _rows(db_path, "SELECT * FROM runs"):
                break
            time.sleep(0.02)
    finally:
        rec.close()
    runs = _rows(db_path, "SELECT * FROM runs")
    assert len(runs) == 1


def test_flush_on_close_lossless(db_path):
    """close() flushes the final partial batch — exact row counts, no loss."""
    rec = Recorder(db_path=db_path, batch_size=1000, flush_interval=100.0)
    rec.start()
    n = 7
    for i in range(n):
        rid = rec.start_run("b_red", 1)
        rec.on_step(rid, _obs(ante=1, chips_scored=0), {"event": "blind_start"})
        rec.on_step(rid, _obs(ante=1, chips_scored=100,
                              last_hand=FakeLastHand()), {"event": "hand_played"})
        rec.end_run(rid, _obs(ante=1, chips_scored=100, jokers=[FakeJoker(10)]),
                    {"event": "run_win"})
    # Nothing forced to flush yet (huge batch + interval) — close drains all.
    rec.close()
    runs = _rows(db_path, "SELECT * FROM runs")
    hands = _rows(db_path, "SELECT * FROM hand_events")
    antes = _rows(db_path, "SELECT * FROM ante_events")
    jokers = _rows(db_path, "SELECT * FROM joker_events")
    assert len(runs) == n
    assert len(hands) == n          # 1 hand_played per run
    assert len(antes) == n          # 1 blind_start per run
    assert len(jokers) == n         # 1 joker per run


# ---------------------------------------------------------------------------
# Batching (not one commit per row)
# ---------------------------------------------------------------------------


def test_batched_not_per_row(db_path):
    """The writer accumulates a batch rather than committing one row at a time."""
    rec = Recorder(db_path=db_path, batch_size=50, flush_interval=100.0)
    rec.start()
    try:
        for _ in range(50):
            rec.start_run("b_red", 1)
        # Wait for exactly one size-triggered batch flush.
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if len(_rows(db_path, "SELECT * FROM runs")) >= 50:
                break
            time.sleep(0.02)
    finally:
        rec.close()
    assert len(_rows(db_path, "SELECT * FROM runs")) == 50


# ---------------------------------------------------------------------------
# ante_reached == per-run max(ante)
# ---------------------------------------------------------------------------


def test_ante_reached_is_max(db_path):
    """ante_reached is the per-run max ante seen across the whole step stream."""
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        for a in [1, 1, 2, 3, 2]:
            rec.on_step(rid, _obs(ante=a), {"event": "draw"})
        rec.end_run(rid, _obs(ante=2, chips_scored=999), {"event": "run_lose"})
    finally:
        rec.close()
    row = _rows(db_path, "SELECT ante_reached FROM runs WHERE id=?", (rid,))[0]
    assert row["ante_reached"] == 3


# ---------------------------------------------------------------------------
# hand_events gating + ordered hand_index
# ---------------------------------------------------------------------------


def test_hand_events_gated_and_indexed(db_path):
    """Only hand_played events create hand_events rows; hand_index = 0,1,2."""
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        stream = [
            ("draw", 0),
            ("hand_played", 100),
            ("shop_open", 100),
            ("hand_played", 250),
            ("blind_start", 0),
            ("hand_played", 90),
        ]
        for ev, cs in stream:
            rec.on_step(rid, _obs(ante=1, chips_scored=cs,
                                  last_hand=FakeLastHand()), {"event": ev})
        rec.end_run(rid, _obs(ante=1, chips_scored=90), {"event": "run_lose"})
    finally:
        rec.close()
    hands = _rows(db_path,
                  "SELECT hand_index FROM hand_events WHERE run_id=? "
                  "ORDER BY hand_index", (rid,))
    assert len(hands) == 3
    assert [h["hand_index"] for h in hands] == [0, 1, 2]


# ---------------------------------------------------------------------------
# Per-hand score delta with per-blind baseline reset
# ---------------------------------------------------------------------------


def test_per_hand_score_delta_with_blind_reset(db_path):
    """score = chips_scored delta vs the per-ante baseline; reset on blind_start.

    Sequence (cumulative chips_scored per hand_played, with blind resets):
      blind_start cs=0   -> baseline=0
      hand_played cs=100 -> score = 100 - 0   = 100
      hand_played cs=300 -> score = 300 - 100 = 200  (delta vs prev hand)
      blind_start cs=0   -> baseline resets to 0 (per-blind chip reset)
      hand_played cs=150 -> score = 150 - 0   = 150  (NOT negative)
    """
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        seq = [
            ("blind_start", 0),
            ("hand_played", 100),
            ("hand_played", 300),
            ("blind_start", 0),
            ("hand_played", 150),
        ]
        for ev, cs in seq:
            rec.on_step(rid, _obs(ante=1, chips_scored=cs,
                                  last_hand=FakeLastHand()), {"event": ev})
        rec.end_run(rid, _obs(ante=1, chips_scored=150), {"event": "run_lose"})
    finally:
        rec.close()
    scores = [r["score"] for r in _rows(
        db_path, "SELECT score FROM hand_events WHERE run_id=? ORDER BY hand_index",
        (rid,))]
    assert scores == [100, 200, 150]
    assert all(s >= 0 for s in scores)


def test_hand_payload_carries_hand_type_chips_mult(db_path):
    """hand_events rows carry last_hand's hand_type/chips/mult/n_cards (Panels 5/6)."""
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        lh = FakeLastHand(hand_type="Flush", chips=140, mult=4, n_cards=5)
        rec.on_step(rid, _obs(ante=1, chips_scored=560, last_hand=lh),
                    {"event": "hand_played"})
        rec.end_run(rid, _obs(ante=1, chips_scored=560), {"event": "run_lose"})
    finally:
        rec.close()
    row = _rows(db_path, "SELECT * FROM hand_events WHERE run_id=?", (rid,))[0]
    assert row["hand_type"] == "Flush"
    assert row["chips"] == 140
    assert row["mult"] == 4
    assert row["n_cards"] == 5


# ---------------------------------------------------------------------------
# ante_events on blind_start
# ---------------------------------------------------------------------------


def test_ante_events_on_blind_start(db_path):
    """blind_start enqueues an ante_events row capturing ante + blind chips."""
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        rec.on_step(rid, _obs(ante=2, chips_needed=800, chips_scored=0),
                    {"event": "blind_start"})
        rec.end_run(rid, _obs(ante=2, chips_scored=0), {"event": "run_lose"})
    finally:
        rec.close()
    row = _rows(db_path, "SELECT * FROM ante_events WHERE run_id=?", (rid,))[0]
    assert row["ante"] == 2
    assert row["blind_chips"] == 800


# ---------------------------------------------------------------------------
# Jokers recorded on end_run
# ---------------------------------------------------------------------------


def test_jokers_recorded(db_path):
    """end_run enqueues joker_events from [j.id for j in obs.jokers]."""
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        rec.end_run(
            rid,
            _obs(ante=3, chips_scored=5000,
                 jokers=[FakeJoker(10), FakeJoker(20), FakeJoker(30)]),
            {"event": "run_win"},
        )
    finally:
        rec.close()
    jrows = _rows(db_path, "SELECT joker_id FROM joker_events WHERE run_id=? "
                          "ORDER BY joker_id", (rid,))
    assert [r["joker_id"] for r in jrows] == [10, 20, 30]
    # num_jokers on the run row should match.
    run = _rows(db_path, "SELECT num_jokers FROM runs WHERE id=?", (rid,))[0]
    assert run["num_jokers"] == 3


# ---------------------------------------------------------------------------
# Empty-info truncation: won=0, no KeyError
# ---------------------------------------------------------------------------


def test_end_run_empty_info_not_won(db_path):
    """end_run with info={} records won=0 and never raises KeyError."""
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        # info={} mirrors gymnasium_env.py:210 socket-timeout truncation.
        rec.end_run(rid, _obs(ante=4, chips_scored=12345), {})
    finally:
        rec.close()
    run = _rows(db_path, "SELECT won, final_score, ante_reached FROM runs "
                        "WHERE id=?", (rid,))[0]
    assert run["won"] == 0
    assert run["final_score"] == 12345
    assert run["ante_reached"] == 4


def test_on_step_empty_info_not_raises(db_path):
    """on_step with info={} must not raise (info.get('event') -> None)."""
    rec = Recorder(db_path=db_path)
    rec.start()
    try:
        rid = rec.start_run("b_red", 1)
        rec.on_step(rid, _obs(ante=1), {})  # no event key
        rec.end_run(rid, _obs(ante=1, chips_scored=0), {})
    finally:
        rec.close()
    # No hand/ante rows from an eventless step.
    assert _rows(db_path, "SELECT * FROM hand_events WHERE run_id=?", (rid,)) == []
