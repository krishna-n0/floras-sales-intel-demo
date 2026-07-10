"""Log who researched which companies — lightweight team activity (no auth)."""

import sqlite3
from typing import Any, Dict, List, Optional

from research_store import DATA_DIR, DB_PATH, _utc_now_iso


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_activity_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS research_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rep_name TEXT NOT NULL,
                company_name TEXT NOT NULL,
                industry TEXT NOT NULL DEFAULT '',
                website TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                fit_score INTEGER,
                fit_level TEXT NOT NULL DEFAULT '',
                entity_type_id TEXT NOT NULL DEFAULT '',
                entity_type_label TEXT NOT NULL DEFAULT '',
                matched_case_title TEXT NOT NULL DEFAULT '',
                research_source TEXT NOT NULL DEFAULT '',
                research_from_cache INTEGER NOT NULL DEFAULT 0,
                research_cache_key TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_created ON research_activity(created_at DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_rep ON research_activity(rep_name)"
        )
        conn.commit()


def _normalize_rep_name(rep_name: str) -> str:
    name = (rep_name or "").strip()
    return name if name else "Anonymous"


def log_research_activity(
    rep_name: str,
    company_name: str,
    industry: str,
    website: str,
    notes: str,
    report: Dict[str, Any],
) -> int:
    """Record one analyze-company run; returns row id."""
    init_activity_db()
    now = _utc_now_iso()

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO research_activity (
                rep_name, company_name, industry, website, notes,
                fit_score, fit_level, entity_type_id, entity_type_label,
                matched_case_title, research_source, research_from_cache,
                research_cache_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _normalize_rep_name(rep_name),
                (company_name or "").strip(),
                (industry or "").strip(),
                (website or "").strip(),
                (notes or "").strip(),
                report.get("fit_score"),
                str(report.get("fit_level") or ""),
                str(report.get("entity_type_id") or ""),
                str(report.get("entity_type_label") or ""),
                str(report.get("matched_case_title") or ""),
                str(report.get("research_source") or ""),
                1 if report.get("research_from_cache") else 0,
                str(report.get("research_cache_key") or ""),
                now,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid or 0)


def list_activity(
    limit: int = 50,
    rep_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Recent team research activity, optionally filtered by rep."""
    init_activity_db()
    limit = max(1, min(limit, 200))

    with _connect() as conn:
        if rep_name and rep_name.strip():
            rows = conn.execute(
                """
                SELECT id, rep_name, company_name, industry, website, notes,
                       fit_score, fit_level, entity_type_id, entity_type_label,
                       matched_case_title, research_source, research_from_cache,
                       research_cache_key, created_at
                FROM research_activity
                WHERE rep_name = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (_normalize_rep_name(rep_name), limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, rep_name, company_name, industry, website, notes,
                       fit_score, fit_level, entity_type_id, entity_type_label,
                       matched_case_title, research_source, research_from_cache,
                       research_cache_key, created_at
                FROM research_activity
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return [_row_to_dict(row) for row in rows]


def list_reps() -> List[str]:
    """Distinct rep names for filter dropdown."""
    init_activity_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT rep_name FROM research_activity
            ORDER BY rep_name COLLATE NOCASE
            """
        ).fetchall()
    return [row["rep_name"] for row in rows]


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "rep_name": row["rep_name"],
        "company_name": row["company_name"],
        "industry": row["industry"],
        "website": row["website"],
        "notes": row["notes"],
        "fit_score": row["fit_score"],
        "fit_level": row["fit_level"],
        "entity_type_id": row["entity_type_id"],
        "entity_type_label": row["entity_type_label"],
        "matched_case_title": row["matched_case_title"],
        "research_source": row["research_source"],
        "research_from_cache": bool(row["research_from_cache"]),
        "research_cache_key": row["research_cache_key"],
        "created_at": row["created_at"],
    }
