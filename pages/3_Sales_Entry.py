"""
pages/3_Sales_Entry.py
------------------------
Sales Entry Module

Allows the logged-in user to log daily sales activity:
    - Date
    - Customers Visited
    - Sales Closed
    - Revenue Generated
    - Product Category
    - Location

Data is stored in the `sales_entries` SQLite table and displayed back to
the user in a "My Entries" tab (so they can review what they've submitted).
"""

import streamlit as st
from datetime import date

from database.db import init_db
from utils.auth import init_session_state, require_login
from utils.styling import apply_custom_css, page_header, section_header, notification
from utils.data_access import add_sales_entry, get_sales_entries

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Sales Entry | Metrax", page_icon="🧾", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("🧾 Sales Entry", "Measure. Monitor. Maximize.")
st.divider()

PRODUCT_CATEGORIES = [
    "Electronics", "Apparel", "FMCG", "Home Appliances",
    "Pharmaceuticals", "Automotive Parts", "Software/Subscriptions", "Other"
]

tab_entry, tab_history = st.tabs(["➕ New Entry", "📜 My Entries"])

# ------------------------------------------------------------------
# NEW ENTRY FORM
# ------------------------------------------------------------------
with tab_entry:
    section_header("Log Today's Sales Activity")

    with st.form("sales_entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date *", value=date.today())
            customers_visited = st.number_input("Customers Visited *", min_value=0, step=1)
            sales_closed = st.number_input("Sales Closed *", min_value=0, step=1)
        with c2:
            revenue_generated = st.number_input("Revenue Generated (₹) *", min_value=0.0, step=100.0, format="%.2f")
            product_category = st.selectbox("Product Category *", PRODUCT_CATEGORIES)
            location = st.text_input("Location *", placeholder="e.g. Hyderabad - Banjara Hills")

        submitted = st.form_submit_button("Submit Entry", use_container_width=True)

    if submitted:
        if sales_closed > customers_visited:
            notification("Sales Closed cannot exceed Customers Visited.", "danger")
        elif not location.strip():
            notification("Location is required.", "danger")
        else:
            add_sales_entry(
                employee_id=user["employee_id"],
                entry_date=entry_date,
                customers_visited=customers_visited,
                sales_closed=sales_closed,
                revenue_generated=revenue_generated,
                product_category=product_category,
                location=location.strip(),
            )
            notification("✅ Sales entry recorded successfully!", "success")
            st.rerun()

# ------------------------------------------------------------------
# HISTORY / MY ENTRIES
# ------------------------------------------------------------------
with tab_history:
    section_header("My Sales Entries")

    sales_df = get_sales_entries(employee_id=user["employee_id"])

    if sales_df.empty:
        notification("You haven't logged any sales entries yet.", "info")
    else:
        display_df = sales_df.sort_values("entry_date", ascending=False)[
            ["entry_date", "customers_visited", "sales_closed",
             "revenue_generated", "product_category", "location"]
        ].rename(columns={
            "entry_date": "Date",
            "customers_visited": "Customers Visited",
            "sales_closed": "Sales Closed",
            "revenue_generated": "Revenue (₹)",
            "product_category": "Product Category",
            "location": "Location",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Entries", len(sales_df))
        with c2:
            st.metric("Total Sales Closed", int(sales_df["sales_closed"].sum()))
        with c3:
            st.metric("Total Revenue", f"₹{sales_df['revenue_generated'].sum():,.0f}")