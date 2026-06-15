"""
pages/10_Reports.py
----------------------
Reports

Generates downloadable reports in CSV, Excel, and PDF formats for:
    - Sales Entries
    - Customer Interactions
    - Performance Summary (monthly)

Managers/Admins can additionally download a full team report.
"""

import streamlit as st
import pandas as pd

from database.db import init_db
from utils.auth import init_session_state, require_login
from utils.styling import apply_custom_css, page_header, section_header, notification
from utils.data_access import get_sales_entries, get_customer_interactions, get_all_users
from utils.calculations import calculate_performance_score, performance_level
from utils.report_generator import (
    dataframe_to_csv_bytes, dataframe_to_excel_bytes, dataframe_to_pdf_bytes
)

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Reports | Metrax", page_icon="📑", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("📑 Reports", "Measure. Monitor. Maximize.")
st.divider()


def download_buttons(df: pd.DataFrame, base_filename: str, pdf_title: str):
    """Render CSV / Excel / PDF download buttons for a DataFrame."""
    if df.empty:
        notification("No data available for this report.", "info")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "⬇️ Download CSV", data=dataframe_to_csv_bytes(df),
            file_name=f"{base_filename}.csv", mime="text/csv",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "⬇️ Download Excel", data=dataframe_to_excel_bytes(df, sheet_name=base_filename[:30]),
            file_name=f"{base_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "⬇️ Download PDF", data=dataframe_to_pdf_bytes(df, title=pdf_title),
            file_name=f"{base_filename}.pdf", mime="application/pdf",
            use_container_width=True
        )


# ------------------------------------------------------------------
# TABS FOR DIFFERENT REPORT TYPES
# ------------------------------------------------------------------
tab_sales, tab_interactions, tab_performance, tab_team = st.tabs(
    ["🧾 Sales Report", "🤝 Interaction Report", "🏆 Performance Report", "👥 Team Report (Manager)"]
)

# ------------------------------------------------------------------
# SALES REPORT
# ------------------------------------------------------------------
with tab_sales:
    section_header("My Sales Entries Report")
    sales_df = get_sales_entries(employee_id=user["employee_id"])
    if not sales_df.empty:
        sales_df = sales_df.drop(columns=["id"], errors="ignore")
    st.dataframe(sales_df, use_container_width=True, hide_index=True)
    download_buttons(sales_df, f"metrax_sales_{user['employee_id']}", "Metrax Sales Report")

# ------------------------------------------------------------------
# INTERACTION REPORT
# ------------------------------------------------------------------
with tab_interactions:
    section_header("My Customer Interactions Report")
    interactions_df = get_customer_interactions(employee_id=user["employee_id"])
    if not interactions_df.empty:
        interactions_df = interactions_df.drop(columns=["id"], errors="ignore")
    st.dataframe(interactions_df, use_container_width=True, hide_index=True)
    download_buttons(interactions_df, f"metrax_interactions_{user['employee_id']}", "Metrax Customer Interaction Report")

# ------------------------------------------------------------------
# PERFORMANCE REPORT
# ------------------------------------------------------------------
with tab_performance:
    section_header("My Monthly Performance Report")
    sales_df = get_sales_entries(employee_id=user["employee_id"])

    if sales_df.empty:
        notification("No sales data available.", "info")
    else:
        sales_df["entry_date"] = pd.to_datetime(sales_df["entry_date"])
        sales_df["month"] = sales_df["entry_date"].dt.to_period("M").astype(str)

        perf_df = sales_df.groupby("month", as_index=False).agg(
            sales_closed=("sales_closed", "sum"),
            customers_visited=("customers_visited", "sum"),
            revenue_generated=("revenue_generated", "sum"),
        )
        perf_df["performance_score"] = perf_df.apply(
            lambda r: calculate_performance_score(r["sales_closed"], r["customers_visited"]), axis=1
        )
        perf_df["level"] = perf_df["performance_score"].apply(performance_level)

        st.dataframe(perf_df, use_container_width=True, hide_index=True)
        download_buttons(perf_df, f"metrax_performance_{user['employee_id']}", "Metrax Performance Report")

# ------------------------------------------------------------------
# TEAM REPORT (MANAGER / ADMIN ONLY)
# ------------------------------------------------------------------
with tab_team:
    section_header("Team-Wide Report")
    if user["role"] not in ["Manager", "Admin", "Team Lead"]:
        notification(
            "This report is available only to <b>Team Lead, Manager, and Admin</b> roles.",
            "warning"
        )
    else:
        all_sales = get_sales_entries()
        all_users = get_all_users()

        if all_sales.empty:
            notification("No team sales data available.", "info")
        else:
            all_sales["entry_date"] = pd.to_datetime(all_sales["entry_date"])
            merged = all_sales.merge(
                all_users[["employee_id", "full_name", "role"]],
                on="employee_id", how="left"
            )
            merged = merged.drop(columns=["id"], errors="ignore")
            st.dataframe(merged, use_container_width=True, hide_index=True)
            download_buttons(merged, "metrax_team_report", "Metrax Team Report")