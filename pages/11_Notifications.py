"""
pages/11_Notifications.py
-----------------------------
Notifications

Shows alerts for:
    - Target achieved
    - Bonus unlocked
    - Promotion eligibility
    - Pending targets
"""

import streamlit as st
import pandas as pd

from database.db import init_db
from utils.auth import init_session_state, require_login, get_promotion_level_order
from utils.styling import apply_custom_css, page_header, section_header, notification
from utils.data_access import get_sales_entries, get_promotion_config
from utils.calculations import (
    get_kpis, calculate_performance_score, calculate_growth_percentage,
    calculate_bonus, recommend_promotion
)

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Notifications | Metrax", page_icon="🔔", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("🔔 Notifications", "Measure. Monitor. Maximize.")
st.divider()

MONTHLY_TARGET_SALES = 50  # Same default used on Home Dashboard

# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
sales_df = get_sales_entries(employee_id=user["employee_id"])

if sales_df.empty:
    notification("No sales data yet — log activity to start receiving alerts.", "info")
    st.stop()

sales_df["entry_date"] = pd.to_datetime(sales_df["entry_date"])
current_period = pd.Timestamp.now().to_period("M")
prev_period = current_period - 1

month_df = sales_df[sales_df["entry_date"].dt.to_period("M") == current_period]
prev_df = sales_df[sales_df["entry_date"].dt.to_period("M") == prev_period]

month_sales = int(month_df["sales_closed"].sum())
month_customers = int(month_df["customers_visited"].sum())
prev_sales = int(prev_df["sales_closed"].sum())

kpis = get_kpis(sales_df, monthly_target_sales=MONTHLY_TARGET_SALES)
score = calculate_performance_score(month_sales, month_customers)
growth_pct = calculate_growth_percentage(month_sales, prev_sales)
bonus = calculate_bonus(growth_pct)

promo_config = get_promotion_config()
current_level_order = get_promotion_level_order(user["role"])
promo_info = recommend_promotion(month_sales, score, current_level_order, promo_config)

# ------------------------------------------------------------------
# 1. TARGET ACHIEVED / PENDING
# ------------------------------------------------------------------
section_header("🎯 Target Status")

if kpis["target_pct"] >= 100:
    notification(
        f"✅ <b>Target Achieved!</b> You've reached {kpis['target_pct']}% of your "
        f"monthly sales target ({MONTHLY_TARGET_SALES} sales).", "success"
    )
else:
    remaining = max(MONTHLY_TARGET_SALES - month_sales, 0)
    notification(
        f"⏳ <b>Pending Target:</b> You're at {kpis['target_pct']}% "
        f"({month_sales}/{MONTHLY_TARGET_SALES} sales). "
        f"{remaining} more sales needed to hit your monthly target.", "warning"
    )

# ------------------------------------------------------------------
# 2. BONUS UNLOCKED
# ------------------------------------------------------------------
section_header("💰 Bonus Alerts")

if bonus > 0:
    notification(
        f"🎉 <b>Bonus Unlocked:</b> ₹{bonus:,.0f} based on {growth_pct:.1f}% monthly growth!",
        "success"
    )
else:
    notification(
        f"No bonus unlocked yet. Current growth: {growth_pct:.1f}% "
        f"(needs to reach 5% for a ₹2,000 bonus).", "info"
    )

# ------------------------------------------------------------------
# 3. PROMOTION ELIGIBILITY
# ------------------------------------------------------------------
section_header("🚀 Promotion Alerts")

if promo_info is None:
    notification("You are at the highest promotion level. 🎉", "success")
elif promo_info["eligible"]:
    notification(
        f"🚀 <b>Promotion Eligible!</b> You qualify for promotion to "
        f"<b>{promo_info['title']}</b>. Reach out to your manager!", "success"
    )
else:
    notification(
        f"Promotion to <b>{promo_info['title']}</b> requires "
        f"{promo_info['required_sales']} monthly sales and a score of "
        f"{promo_info['required_score']}+. "
        f"(Currently: {month_sales} sales, score {score})", "info"
    )

# ------------------------------------------------------------------
# 4. PENDING TARGETS - WEEKLY VIEW
# ------------------------------------------------------------------
section_header("📅 Weekly Activity Check")

WEEKLY_TARGET_SALES = 12  # Example weekly target derived from monthly target

if kpis["week_sales"] >= WEEKLY_TARGET_SALES:
    notification(
        f"✅ Weekly target on track: {kpis['week_sales']} sales this week "
        f"(target: {WEEKLY_TARGET_SALES}).", "success"
    )
else:
    notification(
        f"⏳ Weekly sales: {kpis['week_sales']} / {WEEKLY_TARGET_SALES}. "
        f"Keep up the momentum to stay on pace for your monthly target.", "warning"
    )