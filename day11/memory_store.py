import os
import sqlite3
from typing import Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


def store_memory(key: str, value: str) -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "REPLACE INTO memory (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
        conn.close()
        return {"ok": True, "key": key, "value": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read_memory(key: str) -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute(
            "SELECT value FROM memory WHERE key = ?",
            (key,),
        )
        row = cur.fetchone()
        conn.close()

        if row is None:
            return {"ok": True, "key": key, "value": None, "found": False}

        return {"ok": True, "key": key, "value": row[0], "found": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_memory() -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("SELECT key FROM memory ORDER BY key ASC")
        keys = [row[0] for row in cur.fetchall()]
        conn.close()

        return {"ok": True, "keys": keys}
    except Exception as e:
        return {"ok": False, "error": str(e)}

