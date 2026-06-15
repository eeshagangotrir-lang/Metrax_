"""
pages/2_Profile.py
--------------------
Profile Page

Displays:
    - All employee registration information entered at sign-up
      (Full Name, Age, Gender, Date of Joining, Work Email, Employee ID, Role)
    - Total sales (all-time and this month)
    - Performance score & level
    - Promotion status (eligible / not eligible + next level)
    - Bonus eligibility (this month's growth-based bonus)

This page reads directly from the `users` table (registration data) and
`sales_entries` table (activity data), so everything the user entered at
login/registration time is reflected here.
"""

import streamlit as st
import pandas as pd

from database.db import init_db, get_connection
from utils.auth import init_session_state, require_login, get_promotion_level_order
from utils.styling import apply_custom_css, page_header, section_header, badge, notification
from utils.data_access import get_sales_entries, get_promotion_config
from utils.calculations import (
    calculate_performance_score, performance_level, performance_color,
    calculate_growth_percentage, calculate_bonus, recommend_promotion,
)

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Profile | Metrax", page_icon="👤", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("👤 Profile", "Measure. Monitor. Maximize.")
st.divider()

# ------------------------------------------------------------------
# RE-FETCH LATEST USER ROW (in case of future edits)
# ------------------------------------------------------------------
conn = get_connection()
user_df = pd.read_sql_query(
    "SELECT * FROM users WHERE employee_id = ?", conn, params=(user["employee_id"],)
)
conn.close()

if user_df.empty:
    notification("User record not found.", "danger")
    st.stop()

user_row = user_df.iloc[0]

# ------------------------------------------------------------------
# REGISTRATION / LOGIN DETAILS CARD
# ------------------------------------------------------------------
section_header("Employee Information (as entered at Registration)")

st.markdown('<div class="profile-card">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="profile-field-label">Full Name</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="profile-field-value">{user_row["full_name"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="profile-field-label">Age</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="profile-field-value">{user_row["age"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="profile-field-label">Gender</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="profile-field-value">{user_row["gender"]}</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="profile-field-label">Date of Joining</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="profile-field-value">{user_row["date_of_joining"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="profile-field-label">Work Email</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="profile-field-value">{user_row["work_email"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="profile-field-label">Employee ID</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="profile-field-value">{user_row["employee_id"]}</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="profile-field-label">Role</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="profile-field-value">{user_row["role"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="profile-field-label">Account Created</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="profile-field-value">{user_row["created_at"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# LOAD SALES DATA FOR THIS EMPLOYEE
# ------------------------------------------------------------------
sales_df = get_sales_entries(employee_id=user_row["employee_id"])

total_sales_all_time = int(sales_df["sales_closed"].sum()) if not sales_df.empty else 0
total_revenue_all_time = float(sales_df["revenue_generated"].sum()) if not sales_df.empty else 0.0
total_customers_visited = int(sales_df["customers_visited"].sum()) if not sales_df.empty else 0

# Current month figures
if not sales_df.empty:
    sales_df["entry_date"] = pd.to_datetime(sales_df["entry_date"])
    current_month = pd.Timestamp.now().to_period("M")
    month_df = sales_df[sales_df["entry_date"].dt.to_period("M") == current_month]
    month_sales = int(month_df["sales_closed"].sum())
    month_customers = int(month_df["customers_visited"].sum())
    month_revenue = float(month_df["revenue_generated"].sum())

    # Previous month for growth calc
    prev_month = current_month - 1
    prev_df = sales_df[sales_df["entry_date"].dt.to_period("M") == prev_month]
    prev_month_sales = int(prev_df["sales_closed"].sum())
else:
    month_sales = month_customers = 0
    month_revenue = 0.0
    prev_month_sales = 0

# ------------------------------------------------------------------
# TOTAL SALES SUMMARY
# ------------------------------------------------------------------
section_header("Sales Summary")
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.metric("Total Sales (All-Time)", total_sales_all_time)
with s2:
    st.metric("Total Revenue (All-Time)", f"₹{total_revenue_all_time:,.0f}")
with s3:
    st.metric("This Month's Sales", month_sales)
with s4:
    st.metric("This Month's Revenue", f"₹{month_revenue:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# PERFORMANCE SCORE
# ------------------------------------------------------------------
section_header("Performance Score")

score = calculate_performance_score(month_sales, month_customers)
level = performance_level(score)
color = performance_color(level)

p1, p2 = st.columns([1, 2])
with p1:
    st.markdown(f"**Score:** {score}")
    st.markdown(f"**Level:** {badge(level, color)}", unsafe_allow_html=True)
with p2:
    st.progress(min(score / 150, 1.0), text=f"Performance Score: {score} / 150 (Star Performer at 120+)")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# PROMOTION STATUS
# ------------------------------------------------------------------
section_header("Promotion Status")

promo_config = get_promotion_config()
current_level_order = get_promotion_level_order(user_row["role"])

promo_info = recommend_promotion(month_sales, score, current_level_order, promo_config)

if promo_info is None:
    notification("You are at the highest promotion level. 🎉", "success")
else:
    if promo_info["eligible"]:
        notification(
            f"🚀 You are <b>eligible for promotion</b> to "
            f"<b>{promo_info['title']}</b>!",
            "success"
        )
    else:
        notification(
            f"Next level: <b>{promo_info['title']}</b> — "
            f"requires {promo_info['required_sales']} monthly sales "
            f"and a performance score of {promo_info['required_score']}+. "
            f"(Current: {month_sales} sales, score {score})",
            "info"
        )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# BONUS ELIGIBILITY
# ------------------------------------------------------------------
section_header("Bonus Eligibility (This Month)")

growth_pct = calculate_growth_percentage(month_sales, prev_month_sales)
bonus = calculate_bonus(growth_pct)

b1, b2 = st.columns(2)
with b1:
    st.metric("Monthly Growth", f"{growth_pct:.1f}%")
with b2:
    st.metric("Bonus Eligibility", f"₹{bonus:,.0f}")

if bonus > 0:
    notification(f"🎉 Bonus unlocked: ₹{bonus:,.0f} based on {growth_pct:.1f}% monthly growth!", "success")
else:
    notification("No bonus unlocked this month yet — growth needs to reach 5% or more.", "warning")