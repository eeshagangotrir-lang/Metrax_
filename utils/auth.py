"""
utils/auth.py
--------------
Authentication helpers: user registration, login validation, and
Streamlit session-state management.

All database interaction goes through `database.db.get_connection()`.
Passwords are stored as SHA-256 hashes (see db.hash_password).
"""

import sqlite3
import pandas as pd
import streamlit as st

from database.db import get_connection, hash_password, now_str


# ----------------------------------------------------------------------
# REGISTRATION
# ----------------------------------------------------------------------
def register_user(full_name, age, gender, date_of_joining, work_email,
                   employee_id, role, password):
    """Insert a new user record.

    Returns (success: bool, message: str)
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users
                (full_name, age, gender, date_of_joining, work_email,
                 employee_id, role, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name.strip(),
            int(age),
            gender,
            str(date_of_joining),
            work_email.strip().lower(),
            employee_id.strip(),
            role,
            hash_password(password),
            now_str(),
        ))
        conn.commit()
        return True, "Registration successful! Please log in."
    except sqlite3.IntegrityError as e:
        # Likely a UNIQUE constraint violation on email or employee_id
        msg = str(e)
        if "work_email" in msg:
            return False, "An account with this work email already exists."
        if "employee_id" in msg:
            return False, "An account with this Employee ID already exists."
        return False, f"Registration failed: {msg}"
    except Exception as e:
        return False, f"Unexpected error: {e}"
    finally:
        conn.close()


# ----------------------------------------------------------------------
# LOGIN
# ----------------------------------------------------------------------
def authenticate_user(work_email: str, password: str):
    """Validate login credentials.

    Returns (success: bool, user_row: dict or None, message: str)
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM users WHERE work_email = ?",
            conn,
            params=(work_email.strip().lower(),),
        )
    finally:
        conn.close()

    if df.empty:
        return False, None, "No account found with this email."

    user = df.iloc[0]
    if user["password_hash"] != hash_password(password):
        return False, None, "Incorrect password."

    return True, user.to_dict(), "Login successful!"


# ----------------------------------------------------------------------
# SESSION STATE HELPERS
# ----------------------------------------------------------------------
def init_session_state():
    """Initialize keys used for authentication / navigation in session_state."""
    defaults = {
        "logged_in": False,
        "user": None,            # dict of the logged-in user's row
        "auth_mode": "login",    # "login" or "register"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login_user(user_dict: dict):
    """Mark the session as authenticated for the given user."""
    st.session_state["logged_in"] = True
    st.session_state["user"] = user_dict


def logout_user():
    """Clear the session's authentication state."""
    st.session_state["logged_in"] = False
    st.session_state["user"] = None


def require_login():
    """Stop page execution with a friendly message if not logged in."""
    if not st.session_state.get("logged_in"):
        st.warning("Please log in to access this page.")
        st.stop()


def get_promotion_level_order(role: str, conn=None) -> int:
    """Return the level_order in promotion_config matching a user's role.

    If the role string doesn't directly match a promotion_config title
    (e.g. registration roles vs promotion-ladder titles differ), a
    sensible default mapping is applied.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    role_map = {
        "Sales Representative": "Sales Executive",
        "Team Lead": "Team Lead",
        "Manager": "Manager",
        "Admin": "Manager",
    }
    lookup_title = role_map.get(role, role)

    try:
        df = pd.read_sql_query(
            "SELECT level_order FROM promotion_config WHERE title = ?",
            conn, params=(lookup_title,)
        )
    finally:
        if close_conn:
            conn.close()

    if df.empty:
        return 1
    return int(df.iloc[0]["level_order"])