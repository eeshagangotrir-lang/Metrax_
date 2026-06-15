"""
pages/8_Promotion_Tracker.py
-------------------------------
Promotion Tracker

Shows the configurable promotion ladder:
    Junior Sales Rep -> Sales Executive -> Senior Executive ->
    Team Lead -> Assistant Manager -> Manager

Automatically recommends promotions based on the current month's sales
performance and performance score. Admins/Managers can edit the
thresholds for each level (configurable promotion levels).
"""

import streamlit as st
import pandas as pd

from database.db import init_db
from utils.auth import init_session_state, require_login, get_promotion_level_order
from utils.styling import apply_custom_css, page_header, section_header, notification, badge
from utils.data_access import get_sales_entries, get_promotion_config, update_promotion_config
from utils.calculations import calculate_performance_score, recommend_promotion

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Promotion Tracker | Metrax", page_icon="🚀", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("🚀 Promotion Tracker", "Measure. Monitor. Maximize.")
st.divider()

# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
sales_df = get_sales_entries(employee_id=user["employee_id"])
promo_config = get_promotion_config()

if sales_df.empty:
    month_sales, month_customers = 0, 0
else:
    sales_df["entry_date"] = pd.to_datetime(sales_df["entry_date"])
    current_period = pd.Timestamp.now().to_period("M")
    month_df = sales_df[sales_df["entry_date"].dt.to_period("M") == current_period]
    month_sales = int(month_df["sales_closed"].sum())
    month_customers = int(month_df["customers_visited"].sum())

score = calculate_performance_score(month_sales, month_customers)
current_level_order = get_promotion_level_order(user["role"])

# ------------------------------------------------------------------
# PROMOTION LADDER VISUALIZATION
# ------------------------------------------------------------------
section_header("Promotion Ladder")

for _, row in promo_config.iterrows():
    is_current = row["level_order"] == current_level_order
    is_passed = row["level_order"] < current_level_order

    if is_current:
        marker = badge("YOU ARE HERE", "#4F46E5")
    elif is_passed:
        marker = badge("COMPLETED", "#9CA3AF")
    else:
        marker = ""

    st.markdown(
        f"**{row['level_order']}. {row['title']}** "
        f"— requires {row['min_monthly_sales']} sales/month, "
        f"score {row['min_performance_score']}+  {marker}",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# CURRENT ELIGIBILITY
# ------------------------------------------------------------------
section_header("Your Promotion Eligibility")

c1, c2 = st.columns(2)
with c1:
    st.metric("This Month's Sales", month_sales)
with c2:
    st.metric("Performance Score", score)

promo_info = recommend_promotion(month_sales, score, current_level_order, promo_config)

if promo_info is None:
    notification("You are already at the highest promotion level. 🎉", "success")
else:
    progress_sales = min(month_sales / promo_info["required_sales"], 1.0) if promo_info["required_sales"] else 1.0
    progress_score = min(score / promo_info["required_score"], 1.0) if promo_info["required_score"] else 1.0

    st.progress(progress_sales, text=f"Sales: {month_sales} / {promo_info['required_sales']}")
    st.progress(progress_score, text=f"Score: {score} / {promo_info['required_score']}")

    if promo_info["eligible"]:
        notification(
            f"🚀 <b>Promotion Eligible!</b> You meet the requirements for "
            f"<b>{promo_info['title']}</b>.", "success"
        )
    else:
        notification(
            f"Keep going! You need {promo_info['required_sales']} monthly sales "
            f"and a performance score of {promo_info['required_score']}+ "
            f"to be promoted to <b>{promo_info['title']}</b>.", "info"
        )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# ADMIN/MANAGER: EDIT PROMOTION LEVELS
# ------------------------------------------------------------------
if user["role"] in ["Manager", "Admin"]:
    section_header("⚙️ Configure Promotion Levels (Manager/Admin)")

    with st.form("promo_config_form"):
        edited_rows = {}
        for _, row in promo_config.iterrows():
            st.markdown(f"**Level {row['level_order']}**")
            c1, c2, c3 = st.columns(3)
            with c1:
                title = st.text_input(f"Title #{row['id']}", value=row["title"], key=f"title_{row['id']}")
            with c2:
                min_sales = st.number_input(
                    f"Min Monthly Sales #{row['id']}", min_value=0,
                    value=int(row["min_monthly_sales"]), key=f"sales_{row['id']}"
                )
            with c3:
                min_score = st.number_input(
                    f"Min Performance Score #{row['id']}", min_value=0,
                    value=int(row["min_performance_score"]), key=f"score_{row['id']}"
                )
            edited_rows[row["id"]] = (title, min_sales, min_score)
            st.markdown("---")

        save = st.form_submit_button("Save Configuration", use_container_width=True)

    if save:
        for row_id, (title, min_sales, min_score) in edited_rows.items():
            update_promotion_config(row_id, title, min_sales, min_score)
        notification("✅ Promotion configuration updated.", "success")
        st.rerun()