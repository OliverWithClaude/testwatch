import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'testwatch.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
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
