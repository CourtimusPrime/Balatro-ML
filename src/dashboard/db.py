"""Dashboard SQLite data layer (DASH-01).

The single source of truth for the dashboard's persistence + read layer:

  * SCHEMA_DDL          — the 4-table schema (runs, ante_events, hand_events,
                          joker_events) plus 5 indexes.
  * DB_PATH             — canonical on-disk DB location (locked decision D1).
  * connect / init_db   — connection helper (WAL + busy_timeout + foreign_keys,
                          sqlite3.Row factory) and idempotent initializer.
  * insert_* / flush_batch
                        — writer-side helpers, called ONLY from the recorder's
                          single writer thread (03-02).
  * get_* query methods — read-side methods, one per dashboard panel (03-03).

Security (locked decision V5 / threat T-03-01): every dynamic value is bound via
`?` placeholders. SQL strings are never f-string/`.format()`-built from inputs.

Durability/locking (T-03-02, T-03-03): WAL journal mode + synchronous=NORMAL are
set once at init; readers/writers use busy_timeout=5000 to ride out contention.
"""

from __future__ import annotations

import os
import sqlite3

import pandas as pd

# Locked decision D1: canonical DB path. Single source of truth — reference
# db.DB_PATH everywhere, never hard-code "data/runs.db" or "data/balatro.db".
DB_PATH: str = "data/runs.db"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    deck          TEXT    NOT NULL,
    stake         INTEGER NOT NULL,
    started_at    TEXT    NOT NULL,
    ended_at      TEXT,
    final_score   INTEGER,
    won           INTEGER,
    ante_reached  INTEGER,
    num_jokers    INTEGER
);

CREATE TABLE IF NOT EXISTS ante_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    ante          INTEGER NOT NULL,
    blind_chips   INTEGER,
    chips_scored  INTEGER,
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS hand_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    ante          INTEGER NOT NULL,
    hand_index    INTEGER NOT NULL,
    hand_type     TEXT,
    chips         INTEGER,
    mult          INTEGER,
    n_cards       INTEGER,
    score         INTEGER NOT NULL,
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS joker_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    joker_id      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_started_at   ON runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_final_score  ON runs(final_score);
CREATE INDEX IF NOT EXISTS idx_ante_run          ON ante_events(run_id);
CREATE INDEX IF NOT EXISTS idx_hand_run          ON hand_events(run_id);
CREATE INDEX IF NOT EXISTS idx_joker_run         ON joker_events(run_id);
"""


# ---------------------------------------------------------------------------
# Connection / init
# ---------------------------------------------------------------------------


def connect(path: str = DB_PATH, *, read_only: bool = False) -> sqlite3.Connection:
    """Open a connection with the dashboard's standard pragmas.

    Sets busy_timeout=5000, foreign_keys=ON, and row_factory=sqlite3.Row.
    When read_only=True, opens the file via a `file:...?mode=ro` URI so the
    Streamlit reader (03-03) cannot mutate the DB.
    """
    if read_only:
        uri = f"file:{path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str = DB_PATH) -> None:
    """Create the schema and set durable pragmas. Idempotent.

    journal_mode=WAL and synchronous=NORMAL are set here (once, at init); the
    schema uses CREATE ... IF NOT EXISTS so re-running is a no-op.
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.executescript(SCHEMA_DDL)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Writer-side helpers (recorder writer thread only — 03-02)
# ---------------------------------------------------------------------------


def insert_run(conn: sqlite3.Connection, deck: str, stake: int, started_at: str) -> int:
    """Insert a new run row; return its autoincrement id."""
    cur = conn.execute(
        "INSERT INTO runs (deck, stake, started_at) VALUES (?, ?, ?)",
        (deck, stake, started_at),
    )
    return int(cur.lastrowid)


def finalize_run(
    conn: sqlite3.Connection,
    run_id: int,
    final_score: int,
    won: int,
    ante_reached: int,
    num_jokers: int,
    ended_at: str,
) -> None:
    """Fill in the end-of-run columns for an existing run row."""
    conn.execute(
        "UPDATE runs SET final_score=?, won=?, ante_reached=?, num_jokers=?, "
        "ended_at=? WHERE id=?",
        (final_score, won, ante_reached, num_jokers, ended_at, run_id),
    )


def insert_ante(
    conn: sqlite3.Connection,
    run_id: int,
    ante: int,
    blind_chips: int,
    chips_scored: int,
    created_at: str,
) -> None:
    """Persist one ante (blind) event for a run."""
    conn.execute(
        "INSERT INTO ante_events (run_id, ante, blind_chips, chips_scored, "
        "created_at) VALUES (?, ?, ?, ?, ?)",
        (run_id, ante, blind_chips, chips_scored, created_at),
    )


def insert_hand(
    conn: sqlite3.Connection,
    run_id: int,
    ante: int,
    hand_index: int,
    hand_type: str | None,
    chips: int | None,
    mult: int | None,
    n_cards: int | None,
    score: int,
    created_at: str,
) -> None:
    """Persist one played-hand event for a run (hand_type/chips/mult may be NULL)."""
    conn.execute(
        "INSERT INTO hand_events (run_id, ante, hand_index, hand_type, chips, "
        "mult, n_cards, score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (run_id, ante, hand_index, hand_type, chips, mult, n_cards, score, created_at),
    )


def insert_jokers(conn: sqlite3.Connection, run_id: int, joker_ids: list[int]) -> None:
    """Persist the set of joker ids held during a run."""
    conn.executemany(
        "INSERT INTO joker_events (run_id, joker_id) VALUES (?, ?)",
        [(run_id, jid) for jid in joker_ids],
    )


# Dispatch table for flush_batch: kind -> handler(conn, row dict).
def _dispatch_run_start(conn: sqlite3.Connection, row: dict) -> None:
    insert_run(conn, row["deck"], row["stake"], row["started_at"])


def _dispatch_run_end(conn: sqlite3.Connection, row: dict) -> None:
    finalize_run(
        conn,
        row["run_id"],
        row["final_score"],
        row["won"],
        row["ante_reached"],
        row["num_jokers"],
        row["ended_at"],
    )


def _dispatch_ante(conn: sqlite3.Connection, row: dict) -> None:
    insert_ante(
        conn,
        row["run_id"],
        row["ante"],
        row["blind_chips"],
        row["chips_scored"],
        row["created_at"],
    )


def _dispatch_hand(conn: sqlite3.Connection, row: dict) -> None:
    insert_hand(
        conn,
        row["run_id"],
        row["ante"],
        row["hand_index"],
        row.get("hand_type"),
        row.get("chips"),
        row.get("mult"),
        row.get("n_cards"),
        row["score"],
        row["created_at"],
    )


def _dispatch_jokers(conn: sqlite3.Connection, row: dict) -> None:
    insert_jokers(conn, row["run_id"], row["joker_ids"])


_BATCH_DISPATCH = {
    "run_start": _dispatch_run_start,
    "run_end": _dispatch_run_end,
    "ante": _dispatch_ante,
    "hand": _dispatch_hand,
    "jokers": _dispatch_jokers,
}


def flush_batch(conn: sqlite3.Connection, batch: list[tuple[str, dict]]) -> None:
    """Write a mixed batch of (kind, row) tuples in ONE transaction, one commit.

    `kind` is one of run_start / run_end / ante / hand / jokers. Committing once
    per batch (not once per row) avoids fsync-per-hand throttling under WAL.
    Raises ValueError on an unknown kind (and rolls back the whole batch).
    """
    try:
        for kind, row in batch:
            handler = _BATCH_DISPATCH.get(kind)
            if handler is None:
                raise ValueError(f"flush_batch: unknown kind {kind!r}")
            handler(conn, row)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ---------------------------------------------------------------------------
# Read-side query methods (one per panel — 03-03)
# ---------------------------------------------------------------------------


def get_all_runs(conn: sqlite3.Connection) -> pd.DataFrame:
    """Panels 1 & 2: id, final_score, started_at for every run, by start time."""
    return pd.read_sql_query(
        "SELECT id, final_score, started_at FROM runs ORDER BY started_at",
        conn,
    )


def get_deck_stake_stats(conn: sqlite3.Connection) -> pd.DataFrame:
    """Panel 3: one row per (deck, stake) with avg_score and run count n."""
    return pd.read_sql_query(
        "SELECT deck, stake, AVG(final_score) AS avg_score, COUNT(*) AS n "
        "FROM runs WHERE final_score IS NOT NULL "
        "GROUP BY deck, stake ORDER BY deck, stake",
        conn,
    )


def get_hand_type_counts(conn: sqlite3.Connection) -> pd.DataFrame:
    """Panel 6: hand_type + n, excluding NULL hand_type, ordered by n desc."""
    return pd.read_sql_query(
        "SELECT hand_type, COUNT(*) AS n FROM hand_events "
        "WHERE hand_type IS NOT NULL "
        "GROUP BY hand_type ORDER BY n DESC, hand_type",
        conn,
    )


def get_best_run(conn: sqlite3.Connection) -> tuple[dict | None, pd.DataFrame]:
    """Panel 5: the single highest-final_score run (dict) + its hand_events.

    Returns (None, empty DataFrame) when no finalized run exists.
    """
    row = conn.execute(
        "SELECT * FROM runs WHERE final_score IS NOT NULL "
        "ORDER BY final_score DESC, id ASC LIMIT 1"
    ).fetchone()
    if row is None:
        return None, pd.DataFrame()
    best = dict(row)
    hands = pd.read_sql_query(
        "SELECT * FROM hand_events WHERE run_id = ? ORDER BY hand_index",
        conn,
        params=(best["id"],),
    )
    return best, hands


def get_joker_cooccurrence(
    conn: sqlite3.Connection, top_pct: float = 0.25
) -> pd.DataFrame:
    """Panel 4: j1<j2 co-occurrence counts over the top-N% scoring runs.

    Restricts to runs whose final_score ranks in the top `top_pct` fraction,
    then self-joins joker_events within each such run to count distinct
    unordered joker pairs (j1 < j2).
    """
    n_runs = conn.execute(
        "SELECT COUNT(*) FROM runs WHERE final_score IS NOT NULL"
    ).fetchone()[0]
    if not n_runs:
        return pd.DataFrame(columns=["j1", "j2", "cooccur"])
    # At least 1 run kept; ceil so a tiny DB still has a top cohort.
    top_n = max(1, int(n_runs * top_pct + 0.999999))
    return pd.read_sql_query(
        """
        WITH top_runs AS (
            SELECT id FROM runs
            WHERE final_score IS NOT NULL
            ORDER BY final_score DESC, id ASC
            LIMIT ?
        )
        SELECT a.joker_id AS j1, b.joker_id AS j2, COUNT(*) AS cooccur
        FROM joker_events a
        JOIN joker_events b
          ON a.run_id = b.run_id AND a.joker_id < b.joker_id
        WHERE a.run_id IN (SELECT id FROM top_runs)
        GROUP BY a.joker_id, b.joker_id
        ORDER BY cooccur DESC, j1, j2
        """,
        conn,
        params=(top_n,),
    )


def get_throughput(conn: sqlite3.Connection) -> dict:
    """Panel 7: {games, win_rate, best_score, games_per_hr}.

    win_rate = AVG(won); best_score = MAX(final_score); games_per_hr derived
    from the started_at window. Empty DB yields zeros/None without raising.
    """
    row = conn.execute(
        "SELECT COUNT(*) AS games, AVG(won) AS win_rate, "
        "MAX(final_score) AS best_score, "
        "MIN(started_at) AS first_at, MAX(started_at) AS last_at "
        "FROM runs"
    ).fetchone()

    games = row["games"] or 0
    win_rate = row["win_rate"]
    best_score = row["best_score"]

    games_per_hr: float | None = None
    if games and row["first_at"] and row["last_at"]:
        first = pd.to_datetime(row["first_at"], errors="coerce")
        last = pd.to_datetime(row["last_at"], errors="coerce")
        if pd.notna(first) and pd.notna(last):
            hours = (last - first).total_seconds() / 3600.0
            # Single game (or all at the same instant): no rate window.
            games_per_hr = games / hours if hours > 0 else None

    return {
        "games": games,
        "win_rate": win_rate,
        "best_score": best_score,
        "games_per_hr": games_per_hr,
    }
