"""
database/db.py
----------------
Centralized SQLite connection handling and schema initialization for Metrax.

All tables used by the application are created here:
    - users               : registration & login data
    - sales_entries       : daily sales records entered by reps
    - customer_interactions : CRM-style interaction logs
    - promotion_config    : configurable promotion levels & thresholds

A single helper `get_connection()` returns a SQLite connection with
`check_same_thread=False` so it can be safely reused inside Streamlit's
re-run model.
"""

import sqlite3
import os
import hashlib
from datetime import datetime

# Path to the SQLite database file (created on first run)
DB_PATH = os.path.join(os.path.dirname(__file__), "metrax.db")


def get_connection():
    """Return a SQLite connection object.

    `check_same_thread=False` is required because Streamlit may access the
    connection from different threads across reruns.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    """Return a SHA-256 hash of the given password.

    NOTE: For a production system, use a salted hashing scheme such as
    bcrypt or argon2. SHA-256 is used here for simplicity / zero extra
    dependencies, but the function is isolated so it can be swapped easily.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    """Create all required tables if they do not already exist.

    Called once at application startup (see app.py).
    """
    conn = get_connection()
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # USERS TABLE - stores registration & login information
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            date_of_joining TEXT NOT NULL,
            work_email TEXT UNIQUE NOT NULL,
            employee_id TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # ------------------------------------------------------------------
    # SALES ENTRIES TABLE - daily sales activity per employee
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            customers_visited INTEGER NOT NULL,
            sales_closed INTEGER NOT NULL,
            revenue_generated REAL NOT NULL,
            product_category TEXT NOT NULL,
            location TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES users (employee_id)
        )
    """)

    # ------------------------------------------------------------------
    # CUSTOMER INTERACTIONS TABLE - CRM log
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customer_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            company TEXT,
            phone TEXT,
            interaction_type TEXT NOT NULL,
            outcome TEXT NOT NULL,
            notes TEXT,
            next_followup_date TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES users (employee_id)
        )
    """)

    # ------------------------------------------------------------------
    # PROMOTION CONFIG TABLE - configurable promotion ladder
    # ------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promotion_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_order INTEGER NOT NULL,
            title TEXT NOT NULL UNIQUE,
            min_monthly_sales INTEGER NOT NULL,
            min_performance_score INTEGER NOT NULL
        )
    """)

    conn.commit()

    # Seed default promotion ladder if table is empty
    cur.execute("SELECT COUNT(*) FROM promotion_config")
    if cur.fetchone()[0] == 0:
        default_levels = [
            (1, "Junior Sales Rep", 0, 0),
            (2, "Sales Executive", 20, 31),
            (3, "Senior Executive", 40, 61),
            (4, "Team Lead", 60, 91),
            (5, "Assistant Manager", 80, 110),
            (6, "Manager", 100, 120),
        ]
        cur.executemany("""
            INSERT INTO promotion_config
                (level_order, title, min_monthly_sales, min_performance_score)
            VALUES (?, ?, ?, ?)
        """, default_levels)
        conn.commit()

    conn.close()


def now_str() -> str:
    """Return current timestamp as ISO formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")