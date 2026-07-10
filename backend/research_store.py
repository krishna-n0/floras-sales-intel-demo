"""Persist lead research (scrapes, Tavily, SEC, etc.) for reuse and audit."""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local default: backend/data. On Render set FLORAS_DATA_DIR to the persistent disk path.
DATA_DIR = Path(os.getenv("FLORAS_DATA_DIR", str(Path(__file__).parent / "data")))
DB_PATH = DATA_DIR / "research_cache.db"

DEFAULT_TTL_HOURS = 168  # 7 days


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_field(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def cache_enabled() -> bool:
    flag = os.getenv("RESEARCH_CACHE_ENABLED", "true").strip().lower()
    return flag not in ("0", "false", "no", "off")


def cache_ttl_hours() -> int:
    raw = os.getenv("RESEARCH_CACHE_TTL_HOURS", str(DEFAULT_TTL_HOURS)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_TTL_HOURS


def make_cache_key(company_name: str, industry: str, website: str, notes: str) -> str:
    """Stable key from normalized form inputs (same inputs → same key)."""
    payload = {
        "company_name": _normalize_field(company_name),
        "industry": _normalize_field(industry),
        "website": _normalize_field(website),
        "notes": _normalize_field(notes),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return digest


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS research_cache (
                cache_key TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                industry TEXT NOT NULL DEFAULT '',
                website TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                research_json TEXT NOT NULL,
                source_label TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                hit_count INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_research_cache_updated ON research_cache(updated_at DESC)"
        )
        conn.commit()


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_fresh(updated_at: str) -> bool:
    parsed = _parse_iso(updated_at)
    if not parsed:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - parsed <= timedelta(hours=cache_ttl_hours())


def get_cached_research(
    company_name: str,
    industry: str,
    website: str,
    notes: str,
) -> Optional[Dict[str, Any]]:
    """Return stored research dict if key exists and TTL has not expired."""
    if not cache_enabled():
        return None

    init_db()
    cache_key = make_cache_key(company_name, industry, website, notes)

    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM research_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if not row:
            return None
        if not _is_fresh(row["created_at"]):
            conn.execute("DELETE FROM research_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
            return None

        try:
            research = json.loads(row["research_json"])
        except json.JSONDecodeError:
            return None

        conn.execute(
            """
            UPDATE research_cache
            SET hit_count = hit_count + 1, updated_at = ?
            WHERE cache_key = ?
            """,
            (_utc_now_iso(), cache_key),
        )
        conn.commit()

    entity = research.get("entity_classification") or {}
    return {
        "research": research,
        "cache_key": cache_key,
        "cached_at": row["created_at"],
        "last_used_at": _utc_now_iso(),
        "hit_count": int(row["hit_count"]) + 1,
        "company_name": row["company_name"],
        "industry": row["industry"],
        "website": row["website"],
        "notes": row["notes"],
        "source_label": row["source_label"],
        "entity_type_id": entity.get("entity_type_id", ""),
        "entity_type_label": entity.get("label", ""),
    }


def save_research(
    company_name: str,
    industry: str,
    website: str,
    notes: str,
    research: Dict[str, Any],
) -> str:
    """Persist research blob; returns cache_key."""
    if not cache_enabled():
        return make_cache_key(company_name, industry, website, notes)

    init_db()
    cache_key = make_cache_key(company_name, industry, website, notes)
    now = _utc_now_iso()
    source_label = str(research.get("source") or "")

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO research_cache (
                cache_key, company_name, industry, website, notes,
                research_json, source_label, created_at, updated_at, hit_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ON CONFLICT(cache_key) DO UPDATE SET
                research_json = excluded.research_json,
                source_label = excluded.source_label,
                created_at = excluded.created_at,
                updated_at = excluded.updated_at,
                hit_count = 0
            """,
            (
                cache_key,
                company_name.strip(),
                (industry or "").strip(),
                (website or "").strip(),
                (notes or "").strip(),
                json.dumps(research, ensure_ascii=False),
                source_label,
                now,
                now,
            ),
        )
        conn.commit()

    return cache_key


def list_research_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Recent cached research runs for manager / audit views."""
    init_db()
    limit = max(1, min(limit, 200))

    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT cache_key, company_name, industry, website, notes,
                   source_label, created_at, updated_at, hit_count
            FROM research_cache
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    results = []
    for row in rows:
        results.append(
            {
                "cache_key": row["cache_key"],
                "company_name": row["company_name"],
                "industry": row["industry"],
                "website": row["website"],
                "notes": row["notes"],
                "source_label": row["source_label"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "hit_count": row["hit_count"],
            }
        )
    return results


def get_research_by_key(cache_key: str) -> Optional[Dict[str, Any]]:
    """Fetch full stored research by cache_key (for reference / debug)."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM research_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    if not row:
        return None
    try:
        research = json.loads(row["research_json"])
    except json.JSONDecodeError:
        research = {}
    return {
        "cache_key": row["cache_key"],
        "company_name": row["company_name"],
        "industry": row["industry"],
        "website": row["website"],
        "notes": row["notes"],
        "source_label": row["source_label"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "hit_count": row["hit_count"],
        "research": research,
    }
