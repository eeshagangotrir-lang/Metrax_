"""
pages/6_Performance_Tracker.py
---------------------------------
Performance Tracker

Calculates: Score = (Sales Closed x 5) + Customers Visited
Levels:
    0-30      Poor
    31-60     Average
    61-90     Good
    91-120    Excellent
    120+      Star Performer

Displays progress bars and a gauge chart, plus a monthly history table.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from database.db import init_db
from utils.auth import init_session_state, require_login
from utils.styling import apply_custom_css, page_header, section_header, badge, notification
from utils.data_access import get_sales_entries
from utils.calculations import calculate_performance_score, performance_level, performance_color

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Performance Tracker | Metrax", page_icon="🏆", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("🏆 Performance Tracker", "Measure. Monitor. Maximize.")
st.divider()

# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
sales_df = get_sales_entries(employee_id=user["employee_id"])

if sales_df.empty:
    notification("No sales data yet. Add entries in the <b>Sales Entry</b> page.", "info")
    st.stop()

sales_df["entry_date"] = pd.to_datetime(sales_df["entry_date"])

# Current month aggregates
current_month = pd.Timestamp.now().to_period("M")
month_df = sales_df[sales_df["entry_date"].dt.to_period("M") == current_month]
month_sales = int(month_df["sales_closed"].sum())
month_customers = int(month_df["customers_visited"].sum())

score = calculate_performance_score(month_sales, month_customers)
level = performance_level(score)
color = performance_color(level)

# ------------------------------------------------------------------
# CURRENT SCORE GAUGE
# ------------------------------------------------------------------
section_header("Current Month Performance")

c1, c2 = st.columns([1, 1])

with c1:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": f"Performance Score — {level}"},
        gauge={
            "axis": {"range": [0, 150]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 30], "color": "#FEE2E2"},
                {"range": [30, 60], "color": "#FEF3C7"},
                {"range": [60, 90], "color": "#DBEAFE"},
                {"range": [90, 120], "color": "#D1FAE5"},
                {"range": [120, 150], "color": "#EDE9FE"},
            ],
        }
    ))
    fig_gauge.update_layout(height=350, template="plotly_white")
    st.plotly_chart(fig_gauge, use_container_width=True)

with c2:
    st.markdown(f"### Level: {badge(level, color)}", unsafe_allow_html=True)
    st.markdown(f"**Sales Closed (This Month):** {month_sales}")
    st.markdown(f"**Customers Visited (This Month):** {month_customers}")
    st.markdown(f"**Formula:** Score = (Sales Closed × 5) + Customers Visited")
    st.markdown(f"**Calculation:** ({month_sales} × 5) + {month_customers} = **{score}**")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Level Thresholds**")
    st.markdown("""
    - 0–30 → Poor
    - 31–60 → Average
    - 61–90 → Good
    - 91–120 → Excellent
    - 120+ → Star Performer
    """)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# PROGRESS BAR TOWARDS NEXT LEVEL
# ------------------------------------------------------------------
section_header("Progress to Next Level")

level_caps = {"Poor": 30, "Average": 60, "Good": 90, "Excellent": 120, "Star Performer": 150}
next_cap = level_caps.get(level, 150)
progress = min(score / next_cap, 1.0)
st.progress(progress, text=f"{score} / {next_cap} points toward next level")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# HISTORICAL PERFORMANCE TABLE
# ------------------------------------------------------------------
section_header("Monthly Performance History")

monthly = sales_df.copy()
monthly["month"] = monthly["entry_date"].dt.to_period("M").astype(str)
monthly_agg = monthly.groupby("month", as_index=False).agg(
    sales_closed=("sales_closed", "sum"),
    customers_visited=("customers_visited", "sum"),
).sort_values("month")

monthly_agg["performance_score"] = monthly_agg.apply(
    lambda r: calculate_performance_score(r["sales_closed"], r["customers_visited"]), axis=1
)
monthly_agg["level"] = monthly_agg["performance_score"].apply(performance_level)

display_df = monthly_agg.rename(columns={
    "month": "Month",
    "sales_closed": "Sales Closed",
    "customers_visited": "Customers Visited",
    "performance_score": "Performance Score",
    "level": "Level",
})
st.dataframe(display_df, use_container_width=True, hide_index=True)