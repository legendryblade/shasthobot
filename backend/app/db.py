import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "shasthobot.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS investigations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            report_text TEXT,
            tests_found INTEGER,
            abnormal_count INTEGER,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS investigation_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investigation_id INTEGER,
            tool_name TEXT,
            tool_input TEXT,
            tool_output TEXT,
            step_order INTEGER,
            FOREIGN KEY (investigation_id) REFERENCES investigations (id)
        );
        """
    )
    conn.commit()
    conn.close()
