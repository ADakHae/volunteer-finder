import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "volunteer.db")


def get_conn(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS activities (
            program_id      TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            location        TEXT,
            organization    TEXT,
            category        TEXT,
            activity_type   TEXT,
            recruit_status  TEXT,
            recognized_hours TEXT,
            period_start    TEXT,
            period_end      TEXT,
            volunteer_time  TEXT,
            recruit_start   TEXT,
            recruit_end     TEXT,
            group_key       TEXT,
            fetched_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id      TEXT NOT NULL,
            rating          INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            content         TEXT NOT NULL,
            author_name     TEXT DEFAULT '익명',
            created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (program_id) REFERENCES activities(program_id)
        );

        CREATE TABLE IF NOT EXISTS saved_activities (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id      TEXT NOT NULL UNIQUE,
            saved_at        TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            notes           TEXT,
            FOREIGN KEY (program_id) REFERENCES activities(program_id)
        );

        CREATE INDEX IF NOT EXISTS idx_activities_group_key ON activities(group_key);
        CREATE INDEX IF NOT EXISTS idx_reviews_program_id ON reviews(program_id);
    """)


def upsert_activities(conn, activities):
    conn.executemany("""
        INSERT OR REPLACE INTO activities
            (program_id, title, location, organization, category,
             activity_type, recruit_status, recognized_hours,
             period_start, period_end, volunteer_time,
             recruit_start, recruit_end, group_key, fetched_at)
        VALUES
            (:program_id, :title, :location, :organization, :category,
             :activity_type, :recruit_status, :recognized_hours,
             :period_start, :period_end, :volunteer_time,
             :recruit_start, :recruit_end, :group_key, :fetched_at)
    """, activities)
    conn.commit()


def get_activities(conn, filters=None, page=1, per_page=20):
    where = []
    params = []
    if filters:
        if filters.get("category"):
            where.append("category = ?")
            params.append(filters["category"])
        if filters.get("activity_type"):
            where.append("activity_type = ?")
            params.append(filters["activity_type"])
        if filters.get("recruit_status"):
            where.append("recruit_status = ?")
            params.append(filters["recruit_status"])
        if filters.get("location"):
            where.append("location LIKE ?")
            params.append(f"%{filters['location']}%")
        if filters.get("group_key"):
            where.append("group_key = ?")
            params.append(filters["group_key"])

    where_clause = " WHERE " + " AND ".join(where) if where else ""
    offset = (page - 1) * per_page

    count = conn.execute(
        f"SELECT COUNT(*) FROM activities{where_clause}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"SELECT * FROM activities{where_clause} ORDER BY period_start DESC LIMIT ? OFFSET ?",
        params + [per_page, offset]
    ).fetchall()

    return {"items": [dict(r) for r in rows], "total": count, "page": page, "per_page": per_page}


def get_activity(conn, program_id):
    row = conn.execute(
        "SELECT * FROM activities WHERE program_id = ?", (program_id,)
    ).fetchone()
    return dict(row) if row else None


def get_reviews(conn, program_id):
    rows = conn.execute(
        "SELECT * FROM reviews WHERE program_id = ? ORDER BY created_at DESC",
        (program_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def add_review(conn, program_id, rating, content, author_name="익명"):
    conn.execute(
        "INSERT INTO reviews (program_id, rating, content, author_name) VALUES (?, ?, ?, ?)",
        (program_id, rating, content, author_name or "익명")
    )
    conn.commit()


def save_activity(conn, program_id, notes=""):
    existing = conn.execute(
        "SELECT id FROM saved_activities WHERE program_id = ?", (program_id,)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM saved_activities WHERE program_id = ?", (program_id,))
        conn.commit()
        return False  # unsaved
    else:
        conn.execute(
            "INSERT INTO saved_activities (program_id, notes) VALUES (?, ?)",
            (program_id, notes)
        )
        conn.commit()
        return True  # saved


def is_saved(conn, program_id):
    row = conn.execute(
        "SELECT id FROM saved_activities WHERE program_id = ?", (program_id,)
    ).fetchone()
    return row is not None


def get_saved_activities(conn):
    rows = conn.execute("""
        SELECT a.*, s.saved_at, s.notes AS save_notes
        FROM saved_activities s
        JOIN activities a ON a.program_id = s.program_id
        ORDER BY s.saved_at DESC
    """).fetchall()
    return [dict(r) for r in rows]


def get_grouped_activities(conn, group_key):
    rows = conn.execute(
        "SELECT * FROM activities WHERE group_key = ? ORDER BY period_start",
        (group_key,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_review_stats(conn, program_id):
    row = conn.execute(
        "SELECT COUNT(*) as cnt, COALESCE(AVG(rating), 0) as avg_rating FROM reviews WHERE program_id = ?",
        (program_id,)
    ).fetchone()
    return {"count": row["cnt"], "avg_rating": round(row["avg_rating"], 1)}


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    init_db(conn)
    print(f"DB initialized at {DB_PATH}")
    conn.close()
