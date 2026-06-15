"""
pages/4_Customer_Interactions.py
-----------------------------------
Customer Interaction Log (CRM)

Fields:
    - Customer Name
    - Company
    - Phone
    - Interaction Type
    - Outcome
    - Notes
    - Next Follow-Up Date

Stores entries in `customer_interactions` and shows a filterable history,
plus a highlighted list of upcoming follow-ups due soon.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database.db import init_db
from utils.auth import init_session_state, require_login
from utils.styling import apply_custom_css, page_header, section_header, notification
from utils.data_access import add_customer_interaction, get_customer_interactions

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Customer Interactions | Metrax", page_icon="🤝", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("🤝 Customer Interaction Log", "Measure. Monitor. Maximize.")
st.divider()

INTERACTION_TYPES = ["Call", "Email", "In-Person Visit", "Video Meeting", "WhatsApp/Chat"]
OUTCOMES = ["Interested", "Not Interested", "Deal Closed", "Follow-Up Required", "No Response"]

tab_log, tab_history, tab_followups = st.tabs(
    ["➕ Log Interaction", "📜 History", "⏰ Upcoming Follow-Ups"]
)

# ------------------------------------------------------------------
# LOG NEW INTERACTION
# ------------------------------------------------------------------
with tab_log:
    section_header("Log a Customer Interaction")

    with st.form("interaction_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            customer_name = st.text_input("Customer Name *")
            company = st.text_input("Company")
            phone = st.text_input("Phone", placeholder="+91XXXXXXXXXX")
            interaction_type = st.selectbox("Interaction Type *", INTERACTION_TYPES)
        with c2:
            outcome = st.selectbox("Outcome *", OUTCOMES)
            notes = st.text_area("Notes", placeholder="Additional details about the interaction...")
            next_followup_date = st.date_input(
                "Next Follow-Up Date",
                value=date.today() + timedelta(days=3)
            )

        submitted = st.form_submit_button("Save Interaction", use_container_width=True)

    if submitted:
        if not customer_name.strip():
            notification("Customer Name is required.", "danger")
        else:
            add_customer_interaction(
                employee_id=user["employee_id"],
                customer_name=customer_name.strip(),
                company=company.strip(),
                phone=phone.strip(),
                interaction_type=interaction_type,
                outcome=outcome,
                notes=notes.strip(),
                next_followup_date=next_followup_date,
            )
            notification("✅ Interaction logged successfully!", "success")
            st.rerun()

# ------------------------------------------------------------------
# HISTORY
# ------------------------------------------------------------------
with tab_history:
    section_header("Interaction History")

    interactions_df = get_customer_interactions(employee_id=user["employee_id"])

    if interactions_df.empty:
        notification("No customer interactions logged yet.", "info")
    else:
        display_df = interactions_df[
            ["customer_name", "company", "phone", "interaction_type",
             "outcome", "notes", "next_followup_date", "created_at"]
        ].rename(columns={
            "customer_name": "Customer Name",
            "company": "Company",
            "phone": "Phone",
            "interaction_type": "Interaction Type",
            "outcome": "Outcome",
            "notes": "Notes",
            "next_followup_date": "Next Follow-Up",
            "created_at": "Logged At",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------
# UPCOMING FOLLOW-UPS
# ------------------------------------------------------------------
with tab_followups:
    section_header("Upcoming Follow-Ups (Next 7 Days)")

    interactions_df = get_customer_interactions(employee_id=user["employee_id"])

    if interactions_df.empty:
        notification("No follow-ups scheduled.", "info")
    else:
        df = interactions_df.copy()
        df["next_followup_date"] = pd.to_datetime(df["next_followup_date"], errors="coerce")
        today = pd.Timestamp(date.today())
        upcoming = df[
            (df["next_followup_date"] >= today) &
            (df["next_followup_date"] <= today + pd.Timedelta(days=7))
        ].sort_values("next_followup_date")

        if upcoming.empty:
            notification("No follow-ups due in the next 7 days. 🎉", "success")
        else:
            for _, row in upcoming.iterrows():
                days_left = (row["next_followup_date"] - today).days
                urgency = "danger" if days_left <= 1 else ("warning" if days_left <= 3 else "info")
                notification(
                    f"📅 <b>{row['customer_name']}</b> ({row['company']}) — "
                    f"Follow up on <b>{row['next_followup_date'].date()}</b> "
                    f"({days_left} day(s) left) · Last outcome: {row['outcome']}",
                    urgency
                )