"""
pages/1_Home_Dashboard.py
---------------------------
Modern professional Home Dashboard showing KPI cards:
    - Today's Sales
    - Weekly Sales
    - Monthly Sales
    - Revenue
    - Target Achievement %

Also shows a quick sales trend chart and recent activity.
"""

import streamlit as st
import plotly.express as px

from database.db import init_db
from utils.auth import init_session_state, require_login
from utils.styling import apply_custom_css, page_header, kpi_card, section_header, notification
from utils.data_access import get_sales_entries
from utils.calculations import get_kpis

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Home Dashboard | Metrax", page_icon="🏠", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("🏠 Home Dashboard", "Measure. Monitor. Maximize.")
st.divider()

# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
sales_df = get_sales_entries(employee_id=user["employee_id"])

# Monthly target can be configured per role; default fallback = 50 sales/month
MONTHLY_TARGET_SALES = 50
kpis = get_kpis(sales_df, monthly_target_sales=MONTHLY_TARGET_SALES)

# ------------------------------------------------------------------
# KPI CARDS
# ------------------------------------------------------------------
section_header("Key Performance Indicators")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("Today's Sales", f"{kpis['today_sales']}")
with c2:
    kpi_card("Weekly Sales", f"{kpis['week_sales']}")
with c3:
    kpi_card("Monthly Sales", f"{kpis['month_sales']}")
with c4:
    kpi_card("Revenue (₹)", f"₹{kpis['revenue']:,.0f}")
with c5:
    kpi_card("Target Achievement", f"{kpis['target_pct']}%")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# TARGET PROGRESS BAR
# ------------------------------------------------------------------
section_header("Monthly Target Progress")
progress_value = min(kpis["target_pct"] / 100, 1.0)
st.progress(progress_value, text=f"{kpis['target_pct']}% of monthly target ({MONTHLY_TARGET_SALES} sales)")

if kpis["target_pct"] >= 100:
    notification("🎉 Congratulations! You've achieved your monthly sales target.", "success")
elif kpis["target_pct"] >= 75:
    notification("👏 You're close to your monthly target — keep pushing!", "info")
else:
    notification("⚠️ You're behind on your monthly target. Time to ramp up activity!", "warning")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# QUICK TREND CHART
# ------------------------------------------------------------------
section_header("Recent Sales Trend")

if sales_df.empty:
    notification("No sales entries yet. Go to <b>Sales Entry</b> to log your first activity!", "info")
else:
    daily = sales_df.groupby("entry_date", as_index=False).agg(
        sales_closed=("sales_closed", "sum"),
        revenue_generated=("revenue_generated", "sum"),
    ).sort_values("entry_date")

    fig = px.line(
        daily, x="entry_date", y="sales_closed",
        markers=True, title="Daily Sales Closed (All-Time)",
        labels={"entry_date": "Date", "sales_closed": "Sales Closed"},
    )
    fig.update_layout(template="plotly_white", height=380)
    st.plotly_chart(fig, use_container_width=True)

    # Recent entries table
    section_header("Recent Entries")
    st.dataframe(
        sales_df.sort_values("entry_date", ascending=False).head(10)[
            ["entry_date", "customers_visited", "sales_closed",
             "revenue_generated", "product_category", "location"]
        ],
        use_container_width=True,
        hide_index=True,
    )