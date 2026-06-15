"""
utils/data_access.py
---------------------
CRUD helper functions for sales_entries and customer_interactions tables.
Returns pandas DataFrames for easy use with Plotly / Streamlit widgets.
"""

import pandas as pd
from database.db import get_connection, now_str


# ----------------------------------------------------------------------
# SALES ENTRIES
# ----------------------------------------------------------------------
def add_sales_entry(employee_id, entry_date, customers_visited, sales_closed,
                     revenue_generated, product_category, location):
    """Insert a new sales entry row."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sales_entries
            (employee_id, entry_date, customers_visited, sales_closed,
             revenue_generated, product_category, location, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        employee_id, str(entry_date), int(customers_visited), int(sales_closed),
        float(revenue_generated), product_category, location, now_str()
    ))
    conn.commit()
    conn.close()


def get_sales_entries(employee_id=None) -> pd.DataFrame:
    """Return all sales entries, optionally filtered by employee_id."""
    conn = get_connection()
    try:
        if employee_id:
            df = pd.read_sql_query(
                "SELECT * FROM sales_entries WHERE employee_id = ? ORDER BY entry_date",
                conn, params=(employee_id,)
            )
        else:
            df = pd.read_sql_query(
                "SELECT * FROM sales_entries ORDER BY entry_date", conn
            )
    finally:
        conn.close()

    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"])
    return df


# ----------------------------------------------------------------------
# CUSTOMER INTERACTIONS
# ----------------------------------------------------------------------
def add_customer_interaction(employee_id, customer_name, company, phone,
                              interaction_type, outcome, notes, next_followup_date):
    """Insert a new customer interaction row."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customer_interactions
            (employee_id, customer_name, company, phone, interaction_type,
             outcome, notes, next_followup_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        employee_id, customer_name, company, phone, interaction_type,
        outcome, notes, str(next_followup_date) if next_followup_date else None,
        now_str()
    ))
    conn.commit()
    conn.close()


def get_customer_interactions(employee_id=None) -> pd.DataFrame:
    """Return all customer interactions, optionally filtered by employee_id."""
    conn = get_connection()
    try:
        if employee_id:
            df = pd.read_sql_query(
                "SELECT * FROM customer_interactions WHERE employee_id = ? "
                "ORDER BY created_at DESC",
                conn, params=(employee_id,)
            )
        else:
            df = pd.read_sql_query(
                "SELECT * FROM customer_interactions ORDER BY created_at DESC", conn
            )
    finally:
        conn.close()
    return df


# ----------------------------------------------------------------------
# USERS (for manager dashboard / leaderboard)
# ----------------------------------------------------------------------
def get_all_users() -> pd.DataFrame:
    """Return all registered users (without password hashes)."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT id, full_name, age, gender, date_of_joining, work_email, "
            "employee_id, role, created_at FROM users", conn
        )
    finally:
        conn.close()
    return df


# ----------------------------------------------------------------------
# PROMOTION CONFIG
# ----------------------------------------------------------------------
def get_promotion_config() -> pd.DataFrame:
    """Return the promotion ladder, sorted by level_order."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM promotion_config ORDER BY level_order", conn
        )
    finally:
        conn.close()
    return df


def update_promotion_config(row_id, title, min_monthly_sales, min_performance_score):
    """Update a single promotion level's thresholds / title."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE promotion_config
        SET title = ?, min_monthly_sales = ?, min_performance_score = ?
        WHERE id = ?
    """, (title, int(min_monthly_sales), int(min_performance_score), row_id))
    conn.commit()
    conn.close()