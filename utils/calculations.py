"""
utils/calculations.py
----------------------
Pure business-logic functions used across the app:

    - Performance score & level
    - Monthly growth percentage & bonus mapping
    - Promotion recommendation engine
    - KPI aggregation helpers (today / week / month / revenue / target %)

Keeping these in one module makes them easy to unit-test and reuse from
multiple pages (Home, Performance, Bonus, Promotion, Manager Dashboard).
"""

import pandas as pd
from datetime import datetime, timedelta


# ----------------------------------------------------------------------
# PERFORMANCE SCORE
# ----------------------------------------------------------------------
def calculate_performance_score(sales_closed: int, customers_visited: int) -> int:
    """Score = (Sales Closed * 5) + Customers Visited."""
    return (sales_closed * 5) + customers_visited


def performance_level(score: float) -> str:
    """Map a numeric performance score to a qualitative level."""
    if score <= 30:
        return "Poor"
    elif score <= 60:
        return "Average"
    elif score <= 90:
        return "Good"
    elif score <= 120:
        return "Excellent"
    else:
        return "Star Performer"


def performance_color(level: str) -> str:
    """Return a color associated with a performance level (for badges/gauges)."""
    mapping = {
        "Poor": "#E74C3C",
        "Average": "#F39C12",
        "Good": "#3498DB",
        "Excellent": "#27AE60",
        "Star Performer": "#9B59B6",
    }
    return mapping.get(level, "#7F8C8D")


# ----------------------------------------------------------------------
# GROWTH % AND BONUS
# ----------------------------------------------------------------------
def calculate_growth_percentage(current_value: float, previous_value: float) -> float:
    """Percentage growth of current vs previous period.

    If previous_value is 0, growth is reported as 100% when current > 0,
    otherwise 0%, to avoid division-by-zero errors.
    """
    if previous_value == 0:
        return 100.0 if current_value > 0 else 0.0
    return ((current_value - previous_value) / previous_value) * 100.0


def calculate_bonus(growth_pct: float) -> int:
    """Map monthly growth percentage to a bonus amount (INR)."""
    if growth_pct < 5:
        return 0
    elif growth_pct < 10:
        return 2000
    elif growth_pct < 20:
        return 5000
    elif growth_pct < 30:
        return 10000
    else:
        return 15000


# ----------------------------------------------------------------------
# PROMOTION ENGINE
# ----------------------------------------------------------------------
def recommend_promotion(monthly_sales: int, performance_score: float,
                         current_role_order: int, promotion_levels: pd.DataFrame):
    """Recommend the next promotion level (if any) the employee qualifies for.

    Parameters
    ----------
    monthly_sales : int
        Total sales closed in the current month.
    performance_score : float
        Average / latest performance score.
    current_role_order : int
        `level_order` of the employee's current role in promotion_config.
    promotion_levels : pd.DataFrame
        Rows from promotion_config, sorted by level_order ascending.

    Returns
    -------
    dict or None
        Details of the next eligible level, or None if not eligible / at top.
    """
    # Levels strictly above the current one, sorted ascending
    candidates = promotion_levels[
        promotion_levels["level_order"] > current_role_order
    ].sort_values("level_order")

    if candidates.empty:
        return None  # Already at the top level

    next_level = candidates.iloc[0]

    eligible = (
        monthly_sales >= next_level["min_monthly_sales"]
        and performance_score >= next_level["min_performance_score"]
    )

    return {
        "title": next_level["title"],
        "level_order": int(next_level["level_order"]),
        "required_sales": int(next_level["min_monthly_sales"]),
        "required_score": int(next_level["min_performance_score"]),
        "eligible": eligible,
    }


# ----------------------------------------------------------------------
# KPI AGGREGATION HELPERS
# ----------------------------------------------------------------------
def get_kpis(sales_df: pd.DataFrame, monthly_target_sales: int = 50):
    """Compute Today / Week / Month / Revenue / Target % KPIs.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Must contain columns: entry_date (datetime), sales_closed, revenue_generated
    monthly_target_sales : int
        Target number of sales for the month (used for Target Achievement %).

    Returns
    -------
    dict with keys: today_sales, week_sales, month_sales, revenue, target_pct
    """
    if sales_df.empty:
        return {
            "today_sales": 0,
            "week_sales": 0,
            "month_sales": 0,
            "revenue": 0.0,
            "target_pct": 0.0,
        }

    df = sales_df.copy()
    df["entry_date"] = pd.to_datetime(df["entry_date"])

    today = pd.Timestamp(datetime.now().date())
    week_start = today - timedelta(days=today.weekday())  # Monday of this week
    month_start = today.replace(day=1)

    today_sales = df.loc[df["entry_date"] == today, "sales_closed"].sum()
    week_sales = df.loc[df["entry_date"] >= week_start, "sales_closed"].sum()
    month_df = df.loc[df["entry_date"] >= month_start]
    month_sales = month_df["sales_closed"].sum()
    revenue = month_df["revenue_generated"].sum()

    target_pct = (month_sales / monthly_target_sales * 100) if monthly_target_sales else 0.0

    return {
        "today_sales": int(today_sales),
        "week_sales": int(week_sales),
        "month_sales": int(month_sales),
        "revenue": float(revenue),
        "target_pct": round(float(target_pct), 1),
    }


def monthly_sales_series(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with one row per month: total sales_closed and revenue."""
    if sales_df.empty:
        return pd.DataFrame(columns=["month", "sales_closed", "revenue_generated"])

    df = sales_df.copy()
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["month"] = df["entry_date"].dt.to_period("M").astype(str)

    grouped = df.groupby("month").agg(
        sales_closed=("sales_closed", "sum"),
        revenue_generated=("revenue_generated", "sum"),
        customers_visited=("customers_visited", "sum"),
    ).reset_index()

    return grouped.sort_values("month")


def simple_forecast(values: pd.Series, periods_ahead: int = 3):
    """Very simple linear-trend forecast for the next N periods.

    Uses a least-squares linear fit over the index positions; returns a
    list of forecasted values (not clipped to be non-negative is fine for
    sales, but we clip at 0 for realism).
    """
    if len(values) < 2:
        # Not enough data to fit a trend - repeat last value (or 0)
        last = values.iloc[-1] if len(values) else 0
        return [max(0, last) for _ in range(periods_ahead)]

    import numpy as np
    x = np.arange(len(values))
    y = values.values.astype(float)
    coeffs = np.polyfit(x, y, 1)  # slope, intercept
    forecast_x = np.arange(len(values), len(values) + periods_ahead)
    forecast_y = np.polyval(coeffs, forecast_x)
    return [max(0, round(v, 2)) for v in forecast_y]