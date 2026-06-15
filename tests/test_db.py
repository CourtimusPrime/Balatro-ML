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


# ---------------------------------------------------------------------------
# Task 2 — panel query methods + flush_batch (seeded + empty DBs)
# ---------------------------------------------------------------------------


@pytest.fixture()
def empty_db(tmp_path):
    """An initialized but unseeded runs.db — exercises empty-state paths."""
    p = str(tmp_path / "runs.db")
    db.init_db(p)
    return p


# --- get_all_runs ----------------------------------------------------------


def test_get_all_runs_columns_and_order(seeded_db):
    conn = db.connect(seeded_db)
    df = db.get_all_runs(conn)
    conn.close()
    assert list(df.columns) == ["id", "final_score", "started_at"]
    assert len(df) == 3
    # ordered by started_at ascending
    assert list(df["started_at"]) == sorted(df["started_at"])


def test_get_all_runs_empty(empty_db):
    conn = db.connect(empty_db)
    df = db.get_all_runs(conn)
    conn.close()
    assert list(df.columns) == ["id", "final_score", "started_at"]
    assert len(df) == 0


# --- get_deck_stake_stats --------------------------------------------------


def test_get_deck_stake_stats(seeded_db):
    conn = db.connect(seeded_db)
    df = db.get_deck_stake_stats(conn)
    conn.close()
    assert set(["deck", "stake", "avg_score", "n"]) <= set(df.columns)
    # (b_red,1) has runs A(90000) and C(10000) -> avg 50000, n=2
    red1 = df[(df["deck"] == "b_red") & (df["stake"] == 1)].iloc[0]
    assert red1["n"] == 2
    assert red1["avg_score"] == pytest.approx(50000.0)
    # (b_blue,2) has run B only
    blue2 = df[(df["deck"] == "b_blue") & (df["stake"] == 2)].iloc[0]
    assert blue2["n"] == 1
    assert blue2["avg_score"] == pytest.approx(45000.0)


def test_get_deck_stake_stats_empty(empty_db):
    conn = db.connect(empty_db)
    df = db.get_deck_stake_stats(conn)
    conn.close()
    assert len(df) == 0


# --- get_hand_type_counts --------------------------------------------------


def test_get_hand_type_counts_excludes_null(seeded_db):
    conn = db.connect(seeded_db)
    df = db.get_hand_type_counts(conn)
    conn.close()
    assert list(df.columns) == ["hand_type", "n"]
    assert df["hand_type"].notna().all()
    assert "Pair" in set(df["hand_type"])
    # ordered by n descending
    assert list(df["n"]) == sorted(df["n"], reverse=True)
    # Pair appears in run A and run B -> n=2 (the NULL hand row is excluded)
    pair_n = int(df[df["hand_type"] == "Pair"].iloc[0]["n"])
    assert pair_n == 2


def test_get_hand_type_counts_empty(empty_db):
    conn = db.connect(empty_db)
    df = db.get_hand_type_counts(conn)
    conn.close()
    assert len(df) == 0


# --- get_best_run ----------------------------------------------------------


def test_get_best_run(seeded_db):
    conn = db.connect(seeded_db)
    best, hands = db.get_best_run(conn)
    conn.close()
    assert best is not None
    assert best["final_score"] == 90000  # run A wins
    assert best["deck"] == "b_red"
    # its hand_events ordered by hand_index
    assert list(hands["hand_index"]) == sorted(hands["hand_index"])
    assert len(hands) == 4  # 3 scored + 1 NULL-type hand all belong to run A


def test_get_best_run_empty(empty_db):
    conn = db.connect(empty_db)
    best, hands = db.get_best_run(conn)
    conn.close()
    assert best is None
    assert isinstance(hands, pd.DataFrame)
    assert hands.empty


# --- get_joker_cooccurrence ------------------------------------------------


def test_get_joker_cooccurrence(seeded_db):
    conn = db.connect(seeded_db)
    df = db.get_joker_cooccurrence(conn, top_pct=1.0)  # all runs
    conn.close()
    assert list(df.columns) == ["j1", "j2", "cooccur"]
    assert (df["j1"] < df["j2"]).all()
    # Across all runs, (10,20) co-occur in run A and run B -> cooccur 2.
    pair = df[(df["j1"] == 10) & (df["j2"] == 20)].iloc[0]
    assert int(pair["cooccur"]) == 2


def test_get_joker_cooccurrence_top_pct_restricts(seeded_db):
    conn = db.connect(seeded_db)
    # top 25% of 3 finalized runs -> 1 run (run A, jokers 10,20,30).
    df = db.get_joker_cooccurrence(conn, top_pct=0.25)
    conn.close()
    pairs = {(int(r.j1), int(r.j2)) for r in df.itertuples()}
    assert (10, 20) in pairs
    assert (10, 30) in pairs
    assert (20, 30) in pairs
    # run A only -> each pair co-occurs exactly once
    assert all(int(r.cooccur) == 1 for r in df.itertuples())


def test_get_joker_cooccurrence_empty(empty_db):
    conn = db.connect(empty_db)
    df = db.get_joker_cooccurrence(conn)
    conn.close()
    assert list(df.columns) == ["j1", "j2", "cooccur"]
    assert df.empty


# --- get_throughput --------------------------------------------------------


def test_get_throughput(seeded_db):
    conn = db.connect(seeded_db)
    t = db.get_throughput(conn)
    conn.close()
    assert t["games"] == 3
    assert t["best_score"] == 90000
    # 1 of 3 runs won
    assert t["win_rate"] == pytest.approx(1 / 3)
    assert t["games_per_hr"] is not None and t["games_per_hr"] > 0


def test_get_throughput_empty(empty_db):
    conn = db.connect(empty_db)
    t = db.get_throughput(conn)  # must not raise
    conn.close()
    assert t["games"] == 0
    assert t["win_rate"] is None
    assert t["best_score"] is None
    assert t["games_per_hr"] is None


# --- flush_batch -----------------------------------------------------------


def test_flush_batch_single_transaction(empty_db):
    conn = db.connect(empty_db)
    rid = db.insert_run(conn, "b_red", 1, "2026-02-01T00:00:00")
    conn.commit()
    batch = [
        ("ante", {"run_id": rid, "ante": 1, "blind_chips": 300,
                  "chips_scored": 420, "created_at": "2026-02-01T00:05:00"}),
        ("hand", {"run_id": rid, "ante": 1, "hand_index": 0, "hand_type": "Pair",
                  "chips": 40, "mult": 2, "n_cards": 2, "score": 80,
                  "created_at": "2026-02-01T00:05:10"}),
        ("hand", {"run_id": rid, "ante": 1, "hand_index": 1, "hand_type": None,
                  "score": 0, "created_at": "2026-02-01T00:05:20"}),
        ("jokers", {"run_id": rid, "joker_ids": [1, 2]}),
        ("run_end", {"run_id": rid, "final_score": 5000, "won": 0,
                     "ante_reached": 3, "num_jokers": 2,
                     "ended_at": "2026-02-01T00:10:00"}),
    ]
    db.flush_batch(conn, batch)
    n_ante = conn.execute("SELECT COUNT(*) FROM ante_events").fetchone()[0]
    n_hand = conn.execute("SELECT COUNT(*) FROM hand_events").fetchone()[0]
    n_jok = conn.execute("SELECT COUNT(*) FROM joker_events").fetchone()[0]
    score = conn.execute("SELECT final_score FROM runs WHERE id=?", (rid,)).fetchone()[0]
    conn.close()
    assert n_ante == 1
    assert n_hand == 2
    assert n_jok == 2
    assert score == 5000


def test_flush_batch_run_start(empty_db):
    conn = db.connect(empty_db)
    db.flush_batch(conn, [
        ("run_start", {"deck": "b_blue", "stake": 4,
                       "started_at": "2026-02-01T00:00:00"}),
    ])
    n = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    conn.close()
    assert n == 1


def test_flush_batch_unknown_kind_rolls_back(empty_db):
    conn = db.connect(empty_db)
    rid = db.insert_run(conn, "b_red", 1, "2026-02-01T00:00:00")
    conn.commit()
    with pytest.raises(ValueError):
        db.flush_batch(conn, [
            ("ante", {"run_id": rid, "ante": 1, "blind_chips": 300,
                      "chips_scored": 1, "created_at": "2026-02-01T00:05:00"}),
            ("bogus", {"foo": "bar"}),
        ])
    # the good ante row in the same batch was rolled back
    n_ante = conn.execute("SELECT COUNT(*) FROM ante_events").fetchone()[0]
    conn.close()
    assert n_ante == 0


# ---------------------------------------------------------------------------
# Post-seed live assertion (DASH-04) — run AFTER scripts/seed_dashboard.py.
#
# Select with `pytest tests/test_db.py -k seeded`. This asserts against the REAL
# on-disk db.DB_PATH that the live seed run wrote, so it can only succeed once a
# live 50-game seed has populated it. The offline suite must stay green, so the
# test SELF-SKIPS when db.DB_PATH is absent or empty — it never requires a live
# game just to collect/run the offline tests.
# ---------------------------------------------------------------------------


def _live_db_has_runs() -> bool:
    """True iff db.DB_PATH exists and holds >=1 run; False otherwise (no raise)."""
    import os

    if not os.path.exists(db.DB_PATH):
        return False
    try:
        conn = db.connect(db.DB_PATH, read_only=True)
    except Exception:
        return False
    try:
        n = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    except Exception:
        return False
    finally:
        conn.close()
    return n > 0


def test_seeded_db_every_query_nonempty():
    """After a live seed, every dashboard query method returns non-empty data.

    Self-skips on an empty/absent db.DB_PATH so the offline suite stays green.
    """
    if not _live_db_has_runs():
        pytest.skip("db.DB_PATH empty/absent — run scripts/seed_dashboard.py first")

    conn = db.connect(db.DB_PATH, read_only=True)
    try:
        assert not db.get_all_runs(conn).empty, "get_all_runs returned no rows"
        assert not db.get_deck_stake_stats(conn).empty, "get_deck_stake_stats empty"
        assert not db.get_hand_type_counts(conn).empty, "get_hand_type_counts empty"

        best, hands = db.get_best_run(conn)
        assert best is not None, "get_best_run found no finalized run"
        assert not hands.empty, "get_best_run returned no hand_events"

        thr = db.get_throughput(conn)
        assert thr["games"] > 0, "get_throughput reported zero games"

        # At least one hand carries a non-NULL hand_type -> the mod's live
        # last_hand payload landed (proves Panels 5 & 6 are populated).
        n_typed = conn.execute(
            "SELECT COUNT(*) FROM hand_events WHERE hand_type IS NOT NULL"
        ).fetchone()[0]
        assert n_typed > 0, "no hand_events with a non-NULL hand_type"
    finally:
        conn.close()
