"""
app.py
------
Main entry point for the Metrax Streamlit application.

Responsibilities:
    1. Initialize the SQLite database (creates tables on first run).
    2. Apply global custom CSS styling.
    3. Manage authentication state via st.session_state.
    4. If not logged in -> show Login / Registration forms.
    5. If logged in -> show a welcome screen + sidebar navigation hint
       (actual feature pages live under /pages and are auto-discovered
       by Streamlit's multipage app mechanism).

Run with:
    streamlit run app.py
"""

import streamlit as st
from datetime import date

from database.db import init_db
from utils.auth import (
    init_session_state, register_user, authenticate_user,
    login_user, logout_user,
)
from utils.styling import apply_custom_css, page_header, notification, section_header


# ------------------------------------------------------------------
# PAGE CONFIG - must be the first Streamlit call
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Metrax | Sales Performance Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# INITIALIZE DATABASE & SESSION STATE
# ------------------------------------------------------------------
init_db()
init_session_state()
apply_custom_css()


# ------------------------------------------------------------------
# HEADER (shown on every state)
# ------------------------------------------------------------------
page_header("📈 Metrax", "Measure. Monitor. Maximize.")
st.divider()


# ------------------------------------------------------------------
# LOGIN / REGISTRATION VIEW
# ------------------------------------------------------------------
def show_login_form():
    """Render the login form and handle authentication."""
    with st.form("login_form", clear_on_submit=False):
        st.subheader("🔐 Log In")
        email = st.text_input("Work Email", placeholder="you@company.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", use_container_width=True)

    if submitted:
        if not email or not password:
            notification("Please enter both email and password.", "warning")
        else:
            success, user, message = authenticate_user(email, password)
            if success:
                login_user(user)
                notification(message, "success")
                st.rerun()
            else:
                notification(message, "danger")


def show_register_form():
    """Render the registration form and handle new user creation."""
    with st.form("register_form", clear_on_submit=True):
        st.subheader("📝 Create an Account")

        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *")
            age = st.number_input("Age *", min_value=18, max_value=70, value=25, step=1)
            gender = st.selectbox("Gender *", ["Male", "Female", "Other", "Prefer not to say"])
            date_of_joining = st.date_input("Date of Joining *", value=date.today())
        with col2:
            work_email = st.text_input("Work Email *", placeholder="you@company.com")
            employee_id = st.text_input("Employee ID *", placeholder="e.g. EMP1001")
            role = st.selectbox(
                "Role *",
                ["Sales Representative", "Team Lead", "Manager", "Admin"]
            )
            password = st.text_input("Password *", type="password")
            confirm_password = st.text_input("Confirm Password *", type="password")

        submitted = st.form_submit_button("Register", use_container_width=True)

    if submitted:
        # ---- Validation ----
        errors = []
        if not full_name.strip():
            errors.append("Full Name is required.")
        if not work_email.strip() or "@" not in work_email:
            errors.append("A valid Work Email is required.")
        if not employee_id.strip():
            errors.append("Employee ID is required.")
        if not password:
            errors.append("Password is required.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                notification(e, "danger")
            return

        success, message = register_user(
            full_name, age, gender, date_of_joining, work_email,
            employee_id, role, password
        )
        if success:
            notification(message, "success")
            st.session_state["auth_mode"] = "login"
            st.rerun()
        else:
            notification(message, "danger")


def show_auth_screen():
    """Top-level auth screen: toggle between Login and Register."""
    notification(
        "Welcome to <b>Metrax</b> — your field sales performance companion. "
        "Please log in or create an account to continue.",
        "info"
    )

    tab_login, tab_register = st.tabs(["🔐 Log In", "📝 Register"])

    with tab_login:
        show_login_form()

    with tab_register:
        show_register_form()


# ------------------------------------------------------------------
# AUTHENTICATED HOME / WELCOME VIEW
# ------------------------------------------------------------------
def show_welcome_screen():
    """Shown immediately after login - quick overview + navigation hint."""
    user = st.session_state["user"]

    notification(
        f"Welcome back, <b>{user['full_name']}</b> "
        f"({user['role']} · {user['employee_id']}) 👋",
        "success"
    )

    section_header("Get Started")
    st.markdown("""
    Use the **sidebar navigation** on the left to explore Metrax:

    - **🏠 Home Dashboard** — KPI overview of your sales performance
    - **👤 Profile** — your registration details, performance score & status
    - **🧾 Sales Entry** — log daily sales activity
    - **🤝 Customer Interactions** — manage your CRM follow-ups
    - **📊 Analytics** — trends, revenue, conversion & forecasts
    - **🏆 Performance Tracker** — score, level, and progress
    - **💰 Bonus Tracker** — monthly growth-based bonus calculation
    - **🚀 Promotion Tracker** — promotion eligibility & ladder
    - **🧑‍💼 Manager Dashboard** — team leaderboard & comparisons (Managers/Admins)
    - **📑 Reports** — download CSV / Excel / PDF reports
    - **🔔 Notifications** — alerts on targets, bonuses & promotions
    """)

    st.divider()
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Log Out", use_container_width=True):
            logout_user()
            st.rerun()


# ------------------------------------------------------------------
# MAIN ROUTING LOGIC
# ------------------------------------------------------------------
if st.session_state.get("logged_in"):
    show_welcome_screen()
else:
    show_auth_screen()