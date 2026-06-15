"""
pages/7_Bonus_Tracker.py
---------------------------
Bonus Tracker

Calculates monthly growth percentage (current month vs previous month
sales closed) and assigns a bonus:
    <5%      = ₹0
    5-10%    = ₹2,000
    10-20%   = ₹5,000
    20-30%   = ₹10,000
    30%+     = ₹15,000
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database.db import init_db
from utils.auth import init_session_state, require_login
from utils.styling import apply_custom_css, page_header, section_header, notification, badge
from utils.data_access import get_sales_entries
from utils.calculations import calculate_growth_percentage, calculate_bonus

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Bonus Tracker | Metrax", page_icon="💰", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("💰 Bonus Tracker", "Measure. Monitor. Maximize.")
st.divider()

# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
sales_df = get_sales_entries(employee_id=user["employee_id"])

if sales_df.empty:
    notification("No sales data yet. Add entries in the <b>Sales Entry</b> page.", "info")
    st.stop()

sales_df["entry_date"] = pd.to_datetime(sales_df["entry_date"])
sales_df["month"] = sales_df["entry_date"].dt.to_period("M")

monthly_agg = sales_df.groupby("month", as_index=False).agg(
    sales_closed=("sales_closed", "sum"),
    revenue_generated=("revenue_generated", "sum"),
).sort_values("month")

# ------------------------------------------------------------------
# CURRENT MONTH BONUS
# ------------------------------------------------------------------
current_period = pd.Timestamp.now().to_period("M")
prev_period = current_period - 1

current_sales = int(monthly_agg.loc[monthly_agg["month"] == current_period, "sales_closed"].sum())
prev_sales = int(monthly_agg.loc[monthly_agg["month"] == prev_period, "sales_closed"].sum())

growth_pct = calculate_growth_percentage(current_sales, prev_sales)
bonus_amount = calculate_bonus(growth_pct)

section_header("This Month's Bonus")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Current Month Sales", current_sales)
with c2:
    st.metric("Previous Month Sales", prev_sales)
with c3:
    st.metric("Growth %", f"{growth_pct:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

if bonus_amount > 0:
    notification(
        f"🎉 <b>Bonus Unlocked:</b> ₹{bonus_amount:,.0f} "
        f"(based on {growth_pct:.1f}% growth)", "success"
    )
else:
    notification(
        f"No bonus this month. Growth is {growth_pct:.1f}% — "
        f"reach 5% growth to unlock a ₹2,000 bonus.", "warning"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# BONUS SLAB REFERENCE TABLE
# ------------------------------------------------------------------
section_header("Bonus Slabs")

slab_df = pd.DataFrame({
    "Growth Range": ["< 5%", "5% - 10%", "10% - 20%", "20% - 30%", "30%+"],
    "Bonus (₹)": ["₹0", "₹2,000", "₹5,000", "₹10,000", "₹15,000"],
})
st.dataframe(slab_df, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# HISTORICAL BONUS TABLE
# ------------------------------------------------------------------
section_header("Bonus History")

monthly_agg = monthly_agg.reset_index(drop=True)
growth_list = [0.0]
bonus_list = [0]
for i in range(1, len(monthly_agg)):
    g = calculate_growth_percentage(
        monthly_agg.loc[i, "sales_closed"], monthly_agg.loc[i - 1, "sales_closed"]
    )
    growth_list.append(g)
    bonus_list.append(calculate_bonus(g))

monthly_agg["growth_pct"] = growth_list
monthly_agg["bonus"] = bonus_list
monthly_agg["month_str"] = monthly_agg["month"].astype(str)

display_df = monthly_agg[["month_str", "sales_closed", "growth_pct", "bonus"]].rename(columns={
    "month_str": "Month",
    "sales_closed": "Sales Closed",
    "growth_pct": "Growth (%)",
    "bonus": "Bonus (₹)",
})
display_df["Growth (%)"] = display_df["Growth (%)"].round(1)
st.dataframe(display_df, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------
# BONUS CHART
# ------------------------------------------------------------------
fig = px.bar(
    monthly_agg, x="month_str", y="bonus",
    title="Monthly Bonus History (₹)",
    labels={"month_str": "Month", "bonus": "Bonus (₹)"},
    color_discrete_sequence=["#22C55E"]
)
fig.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig, use_container_width=True)

total_bonus = sum(bonus_list)
st.metric("Total Bonus Earned (All-Time)", f"₹{total_bonus:,.0f}")