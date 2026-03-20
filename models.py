import sqlite3
import os
from datetime import datetime
from flask import g

DB_PATH = os.path.join(os.path.dirname(__file__), 'testwatch.db')


def get_db():
    """Get a database connection from Flask's per-request context."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database schema. Safe to call repeatedly — uses IF NOT EXISTS."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS activity_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS workstreams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ranks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER NOT NULL,
        rank_id TEXT NOT NULL,
        description TEXT DEFAULT '',
        workstream_id INTEGER,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
        FOREIGN KEY (workstream_id) REFERENCES workstreams(id) ON DELETE SET NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER NOT NULL,
        name TEXT DEFAULT '',
        started_at TEXT NOT NULL,
        ended_at TEXT,
        FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS time_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        rank_id INTEGER NOT NULL,
        activity_type_id INTEGER NOT NULL,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        duration_seconds REAL DEFAULT 0,
        seq_order INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (rank_id) REFERENCES ranks(id) ON DELETE CASCADE,
        FOREIGN KEY (activity_type_id) REFERENCES activity_types(id) ON DELETE CASCADE
    )''')

    # Migrate: add display_name column to scenarios if missing
    scols = [row[1] for row in c.execute("PRAGMA table_info(scenarios)").fetchall()]
    if 'display_name' not in scols:
        c.execute("ALTER TABLE scenarios ADD COLUMN display_name TEXT DEFAULT ''")

    # Migrate: add jira_key column to ranks if missing
    cols = [row[1] for row in c.execute("PRAGMA table_info(ranks)").fetchall()]
    if 'jira_key' not in cols:
        c.execute("ALTER TABLE ranks ADD COLUMN jira_key TEXT DEFAULT ''")

    # Seed default activity types if empty
    existing = c.execute("SELECT COUNT(*) FROM activity_types").fetchone()[0]
    if existing == 0:
        defaults = [
            ("Waiting for tester to join", "#FF6B6B", 1),
            ("Waiting for tester to be ready", "#FFA07A", 2),
            ("Test execution", "#4CAF50", 3),
            ("Creating a defect", "#FF9800", 4),
            ("Getting an expert", "#9C27B0", 5),
            ("Waiting for blocking defect", "#F44336", 6),
            ("Planned break", "#2196F3", 7),
            ("Unplanned break", "#607D8B", 8),
        ]
        c.executemany("INSERT INTO activity_types (name, color, sort_order) VALUES (?, ?, ?)", defaults)

    conn.commit()
    conn.close()
