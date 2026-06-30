import os
import sqlite3
import datetime
from pathlib import Path

from rootmatrix.engine.config import load_config

# Setup local storage directory for the budget DB
DB_DIR = Path.home() / ".rootmatrix"
DB_DIR = Path.home() / ".rootmatrix"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "budget.db"

def get_connection():
    """Returns a SQLite connection to the budget database."""
    conn = sqlite3.connect(DB_PATH)
    # Ensure the usage table exists
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tokens INTEGER NOT NULL,
            path TEXT NOT NULL
        )
        """
    )
    
    # Example migration pattern as specified in CLAUDE.md
    try:
        conn.execute("ALTER TABLE usage ADD COLUMN source TEXT DEFAULT 'unknown'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists — safe to ignore

    return conn

def get_budget_status(file_path: str = None) -> dict:
    """Returns the current daily usage and limits."""
    config = load_config(file_path)
    daily_limit = config.get("daily_limit", 200000)
    
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(tokens) FROM usage WHERE timestamp LIKE ?", 
            (f"{today}%",)
        )
        result = cursor.fetchone()
        tokens_used = result[0] if result[0] else 0
        return {
            "tokens_used": tokens_used,
            "daily_limit": daily_limit,
            "remaining": max(0, daily_limit - tokens_used),
            "percentage": (tokens_used / daily_limit) * 100 if daily_limit else 0
        }
    finally:
        conn.close()

def check_budget(file_path: str = None) -> dict:
    """
    Checks if we have exceeded the budget.
    Returns a dict that can be used by MCP tools.
    """
    status = get_budget_status(file_path)
    if status["tokens_used"] >= status["daily_limit"]:
        return {
            "error": f"Daily token limit reached ({status['tokens_used']} / {status['daily_limit']}).",
            "blocked": True,
            "status": status
        }
    return {"blocked": False, "status": status}

def record_usage(tokens: int, path: str, source: str = "mcp_tool"):
    """Records token usage for a given file read."""
    if tokens <= 0:
        return
        
    conn = get_connection()
    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO usage (timestamp, tokens, path, source) VALUES (?, ?, ?, ?)",
            (now, tokens, path, source)
        )
        conn.commit()
    finally:
        conn.close()
