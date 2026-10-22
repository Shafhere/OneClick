"""Small SQLite store for research history; independent of the vector database."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "oneclick_history.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_history():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            company_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            pages_crawled INTEGER NOT NULL,
            report_json TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC)")


def save_report(url: str, result: dict) -> int:
    profile = result.get("profile", {})
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO reports(url, company_name, created_at, pages_crawled, report_json) VALUES (?, ?, ?, ?, ?)",
            (url, profile.get("company_name", "Unknown company"), created_at,
             int(result.get("pages_crawled", 0)), json.dumps(result, ensure_ascii=False)),
        )
        return int(cursor.lastrowid)


def list_reports(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, url, company_name, created_at, pages_crawled FROM reports ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 100)),),
        ).fetchall()
    return [dict(row) for row in rows]


def get_report(report_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT report_json FROM reports WHERE id = ?", (report_id,)).fetchone()
    return json.loads(row["report_json"]) if row else None


def delete_report(report_id: int) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        return cursor.rowcount > 0


initialize_history()
