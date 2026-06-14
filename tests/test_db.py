"""Offline tests for the dashboard SQLite data layer (DASH-01).

Covers schema creation, WAL pragmas, the connection helper, writer-side
insert_* helpers, and (Task 2) the seven panel query methods + flush_batch.

All tests run without a live game: they build temp DBs and a shared
`seeded_db` fixture (see tests/conftest.py).
"""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from src.dashboard import db


# ---------------------------------------------------------------------------
# Task 1 — schema + connection + writers
# ---------------------------------------------------------------------------


def test_db_path_constant():
    assert db.DB_PATH == "data/runs.db"


def test_init_db_creates_all_tables(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    names = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()
    assert {"runs", "ante_events", "hand_events", "joker_events"} <= names


def test_init_db_creates_indexes(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    idx = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    }
    conn.close()
    # 5 named indexes are expected.
    named = {n for n in idx if n.startswith("idx_")}
    assert len(named) >= 5


def test_init_db_is_idempotent(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    db.init_db(p)  # must not raise
    conn = db.connect(p)
    n = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    conn.close()
    assert n == 0


def test_journal_mode_is_wal(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"


def test_connect_pragmas(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    assert conn.row_factory is sqlite3.Row
    assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()


def test_connect_read_only_blocks_writes(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    ro = db.connect(p, read_only=True)
    with pytest.raises(sqlite3.OperationalError):
        ro.execute(
            "INSERT INTO runs (deck, stake, started_at) VALUES (?, ?, ?)",
            ("b_red", 1, "2026-01-01T00:00:00"),
        )
        ro.commit()
    ro.close()


def test_insert_run_returns_autoincrement_id(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    rid1 = db.insert_run(conn, "b_red", 1, "2026-01-01T00:00:00")
    rid2 = db.insert_run(conn, "b_blue", 2, "2026-01-01T01:00:00")
    conn.commit()
    assert isinstance(rid1, int)
    assert rid2 == rid1 + 1
    conn.close()


def test_finalize_run_updates_row(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    rid = db.insert_run(conn, "b_red", 1, "2026-01-01T00:00:00")
    db.finalize_run(conn, rid, final_score=12345, won=1, ante_reached=8,
                    num_jokers=4, ended_at="2026-01-01T00:30:00")
    conn.commit()
    row = conn.execute(
        "SELECT final_score, won, ante_reached, num_jokers, ended_at "
        "FROM runs WHERE id=?",
        (rid,),
    ).fetchone()
    conn.close()
    assert row["final_score"] == 12345
    assert row["won"] == 1
    assert row["ante_reached"] == 8
    assert row["num_jokers"] == 4
    assert row["ended_at"] == "2026-01-01T00:30:00"


def test_insert_ante_persists_linked_row(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    rid = db.insert_run(conn, "b_red", 1, "2026-01-01T00:00:00")
    db.insert_ante(conn, rid, ante=1, blind_chips=300, chips_scored=420,
                   created_at="2026-01-01T00:05:00")
    conn.commit()
    row = conn.execute(
        "SELECT run_id, ante, blind_chips, chips_scored FROM ante_events"
    ).fetchone()
    conn.close()
    assert row["run_id"] == rid
    assert row["ante"] == 1
    assert row["blind_chips"] == 300
    assert row["chips_scored"] == 420


def test_insert_hand_persists_linked_row(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    rid = db.insert_run(conn, "b_red", 1, "2026-01-01T00:00:00")
    db.insert_hand(conn, rid, ante=1, hand_index=0, hand_type="Pair",
                   chips=40, mult=2, n_cards=2, score=80,
                   created_at="2026-01-01T00:06:00")
    conn.commit()
    row = conn.execute("SELECT * FROM hand_events").fetchone()
    conn.close()
    assert row["run_id"] == rid
    assert row["hand_type"] == "Pair"
    assert row["score"] == 80


def test_insert_hand_accepts_nulls(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    rid = db.insert_run(conn, "b_red", 1, "2026-01-01T00:00:00")
    db.insert_hand(conn, rid, ante=1, hand_index=0, hand_type=None,
                   chips=None, mult=None, n_cards=None, score=0,
                   created_at="2026-01-01T00:06:00")
    conn.commit()
    row = conn.execute("SELECT hand_type, chips, mult FROM hand_events").fetchone()
    conn.close()
    assert row["hand_type"] is None
    assert row["chips"] is None


def test_insert_jokers_persists_rows(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    rid = db.insert_run(conn, "b_red", 1, "2026-01-01T00:00:00")
    db.insert_jokers(conn, rid, [10, 20, 30])
    conn.commit()
    rows = conn.execute(
        "SELECT joker_id FROM joker_events WHERE run_id=? ORDER BY joker_id",
        (rid,),
    ).fetchall()
    conn.close()
    assert [r["joker_id"] for r in rows] == [10, 20, 30]


def test_foreign_keys_enforced(tmp_path):
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    conn = db.connect(p)
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_ante(conn, 999, ante=1, blind_chips=300, chips_scored=10,
                       created_at="2026-01-01T00:05:00")
        conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# seeded_db fixture sanity
# ---------------------------------------------------------------------------


def test_seeded_db_has_runs(seeded_db):
    conn = db.connect(seeded_db)
    n = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    conn.close()
    assert n >= 3
