"""
pages/9_Manager_Dashboard.py
-------------------------------
Manager Dashboard (visible to Manager / Admin / Team Lead roles)

Shows:
    - Team leaderboard
    - Top performers
    - Underperformers
    - Team KPIs
    - Employee comparison charts
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database.db import init_db
from utils.auth import init_session_state, require_login
from utils.styling import apply_custom_css, page_header, section_header, notification, badge
from utils.data_access import get_sales_entries, get_all_users
from utils.calculations import calculate_performance_score, performance_level, performance_color

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Manager Dashboard | Metrax", page_icon="🧑‍💼", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("🧑‍💼 Manager Dashboard", "Measure. Monitor. Maximize.")
st.divider()

# ------------------------------------------------------------------
# ROLE GUARD
# ------------------------------------------------------------------
ALLOWED_ROLES = ["Manager", "Admin", "Team Lead"]
if user["role"] not in ALLOWED_ROLES:
    notification(
        "This page is available only to <b>Team Lead, Manager, and Admin</b> roles.",
        "warning"
    )
    st.stop()

# ------------------------------------------------------------------
# LOAD DATA - ALL USERS + ALL SALES ENTRIES
# ------------------------------------------------------------------
all_users = get_all_users()
all_sales = get_sales_entries()  # all employees

if all_sales.empty:
    notification("No sales data has been logged by any team member yet.", "info")
    st.stop()

all_sales["entry_date"] = pd.to_datetime(all_sales["entry_date"])
current_period = pd.Timestamp.now().to_period("M")
month_sales_df = all_sales[all_sales["entry_date"].dt.to_period("M") == current_period]

# ------------------------------------------------------------------
# AGGREGATE PER EMPLOYEE (CURRENT MONTH)
# ------------------------------------------------------------------
agg = month_sales_df.groupby("employee_id", as_index=False).agg(
    sales_closed=("sales_closed", "sum"),
    customers_visited=("customers_visited", "sum"),
    revenue_generated=("revenue_generated", "sum"),
)

agg["performance_score"] = agg.apply(
    lambda r: calculate_performance_score(r["sales_closed"], r["customers_visited"]), axis=1
)
agg["level"] = agg["performance_score"].apply(performance_level)

# Merge with user names
agg = agg.merge(
    all_users[["employee_id", "full_name", "role"]],
    on="employee_id", how="left"
)

# ------------------------------------------------------------------
# TEAM KPIs
# ------------------------------------------------------------------
section_header("Team KPIs (This Month)")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Team Members Active", len(agg))
with c2:
    st.metric("Total Sales Closed", int(agg["sales_closed"].sum()))
with c3:
    st.metric("Total Revenue", f"₹{agg['revenue_generated'].sum():,.0f}")
with c4:
    st.metric("Avg Performance Score", f"{agg['performance_score'].mean():.1f}" if not agg.empty else "0")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# LEADERBOARD
# ------------------------------------------------------------------
section_header("🏆 Team Leaderboard (This Month)")

leaderboard = agg.sort_values("performance_score", ascending=False).reset_index(drop=True)
leaderboard.insert(0, "Rank", range(1, len(leaderboard) + 1))

display_lb = leaderboard[[
    "Rank", "full_name", "role", "sales_closed", "customers_visited",
    "revenue_generated", "performance_score", "level"
]].rename(columns={
    "full_name": "Name", "role": "Role", "sales_closed": "Sales Closed",
    "customers_visited": "Customers Visited", "revenue_generated": "Revenue (₹)",
    "performance_score": "Score", "level": "Level"
})
st.dataframe(display_lb, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# TOP PERFORMERS / UNDERPERFORMERS
# ------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    section_header("🌟 Top Performers")
    top = leaderboard.head(3)
    for _, row in top.iterrows():
        color = performance_color(row["level"])
        st.markdown(
            f"**{row['full_name']}** ({row['role']}) — Score: {row['performance_score']} "
            f"{badge(row['level'], color)}",
            unsafe_allow_html=True
        )

with col2:
    section_header("⚠️ Underperformers")
    bottom = leaderboard.tail(3).sort_values("performance_score")
    for _, row in bottom.iterrows():
        color = performance_color(row["level"])
        st.markdown(
            f"**{row['full_name']}** ({row['role']}) — Score: {row['performance_score']} "
            f"{badge(row['level'], color)}",
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# EMPLOYEE COMPARISON CHARTS
# ------------------------------------------------------------------
section_header("📊 Employee Comparison")

fig_sales = px.bar(
    leaderboard, x="full_name", y="sales_closed",
    title="Sales Closed by Employee (This Month)",
    labels={"full_name": "Employee", "sales_closed": "Sales Closed"},
    color="sales_closed", color_continuous_scale="Blues"
)
fig_sales.update_layout(template="plotly_white", height=400)
st.plotly_chart(fig_sales, use_container_width=True)

fig_score = px.bar(
    leaderboard, x="full_name", y="performance_score",
    title="Performance Score by Employee (This Month)",
    labels={"full_name": "Employee", "performance_score": "Performance Score"},
    color="level",
    color_discrete_map={
        "Poor": "#E74C3C", "Average": "#F39C12", "Good": "#3498DB",
        "Excellent": "#27AE60", "Star Performer": "#9B59B6"
    }
)
fig_score.update_layout(template="plotly_white", height=400)
st.plotly_chart(fig_score, use_container_width=True)

fig_revenue = px.pie(
    leaderboard, names="full_name", values="revenue_generated",
    title="Revenue Share by Employee (This Month)"
)
fig_revenue.update_layout(height=400)
st.plotly_chart(fig_revenue, use_container_width=True)