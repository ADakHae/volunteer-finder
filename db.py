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
            fetched_at      TEXT NOT NULL,
            description     TEXT,
            recruit_count   TEXT,
            apply_count     TEXT,
            target          TEXT,
            active_days     TEXT,
            volunteer_type  TEXT,
            register_org    TEXT,
            detail_fetched  INTEGER DEFAULT 0
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
    # 기존 DB 마이그레이션: 새 컬럼 추가
    existing = {row[1] for row in conn.execute("PRAGMA table_info(activities)").fetchall()}
    new_cols = [
        ("description", "TEXT"),
        ("recruit_count", "TEXT"),
        ("apply_count", "TEXT"),
        ("target", "TEXT"),
        ("active_days", "TEXT"),
        ("volunteer_type", "TEXT"),
        ("register_org", "TEXT"),
        ("detail_fetched", "INTEGER DEFAULT 0"),
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE activities ADD COLUMN {col_name} {col_type}")


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


def update_activity_detail(conn, detail):
    """상세 페이지에서 가져온 정보로 활동 업데이트."""
    conn.execute("""
        UPDATE activities SET
            description = ?, recruit_count = ?, apply_count = ?,
            target = ?, active_days = ?, volunteer_type = ?,
            register_org = ?, location = ?, organization = ?,
            recruit_status = ?, volunteer_time = ?, recognized_hours = ?,
            period_start = ?, period_end = ?, recruit_start = ?, recruit_end = ?,
            category = ?, activity_type = ?, detail_fetched = 1
        WHERE program_id = ?
    """, (
        detail.get("description", ""), detail.get("recruit_count", ""),
        detail.get("apply_count", ""), detail.get("target", ""),
        detail.get("active_days", ""), detail.get("volunteer_type", ""),
        detail.get("register_org", ""), detail.get("location", ""),
        detail.get("organization", ""), detail.get("recruit_status", ""),
        detail.get("volunteer_time", ""), detail.get("recognized_hours", ""),
        detail.get("period_start", ""), detail.get("period_end", ""),
        detail.get("recruit_start", ""), detail.get("recruit_end", ""),
        detail.get("category", ""), detail.get("activity_type", ""),
        detail["program_id"],
    ))
    conn.commit()


def ensure_activity_exists(conn, program_id, fetched_at):
    """목록에서 클릭했지만 DB에 없을 경우 빈 레코드 생성."""
    existing = conn.execute(
        "SELECT program_id FROM activities WHERE program_id = ?", (program_id,)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO activities (program_id, title, fetched_at) VALUES (?, '', ?)",
            (program_id, fetched_at)
        )
        conn.commit()


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
