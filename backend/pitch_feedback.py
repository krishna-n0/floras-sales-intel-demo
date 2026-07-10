"""Store rep feedback on outreach pitch quality and usefulness."""

import sqlite3
from typing import Any, Dict, List, Optional

from research_store import DATA_DIR, DB_PATH, _utc_now_iso


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_pitch_feedback_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pitch_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER,
                rep_name TEXT NOT NULL,
                company_name TEXT NOT NULL,
                used_pitch TEXT NOT NULL DEFAULT '',
                liked_pitch TEXT NOT NULL DEFAULT '',
                was_effective TEXT NOT NULL DEFAULT '',
                improvements TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pitch_feedback_created ON pitch_feedback(created_at DESC)"
        )
        conn.commit()


def save_pitch_feedback(
    rep_name: str,
    company_name: str,
    used_pitch: str,
    liked_pitch: str,
    was_effective: str,
    improvements: str = "",
    activity_id: Optional[int] = None,
) -> int:
    init_pitch_feedback_db()
    now = _utc_now_iso()
    rep = (rep_name or "").strip() or "Anonymous"
    company = (company_name or "").strip()

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pitch_feedback (
                activity_id, rep_name, company_name,
                used_pitch, liked_pitch, was_effective, improvements, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activity_id if activity_id else None,
                rep,
                company,
                (used_pitch or "").strip(),
                (liked_pitch or "").strip(),
                (was_effective or "").strip(),
                (improvements or "").strip(),
                now,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid or 0)


def list_pitch_feedback(limit: int = 50, rep_name: Optional[str] = None) -> List[Dict[str, Any]]:
    init_pitch_feedback_db()
    limit = max(1, min(limit, 200))

    with _connect() as conn:
        if rep_name and rep_name.strip():
            rows = conn.execute(
                """
                SELECT id, activity_id, rep_name, company_name,
                       used_pitch, liked_pitch, was_effective, improvements, created_at
                FROM pitch_feedback
                WHERE rep_name = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (rep_name.strip(), limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, activity_id, rep_name, company_name,
                       used_pitch, liked_pitch, was_effective, improvements, created_at
                FROM pitch_feedback
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return [
        {
            "id": row["id"],
            "activity_id": row["activity_id"],
            "rep_name": row["rep_name"],
            "company_name": row["company_name"],
            "used_pitch": row["used_pitch"],
            "liked_pitch": row["liked_pitch"],
            "was_effective": row["was_effective"],
            "improvements": row["improvements"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
