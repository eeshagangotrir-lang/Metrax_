"""
utils/styling.py
-----------------
Centralized custom CSS for Metrax. Imported and applied on every page via
`apply_custom_css()` to give a consistent, modern, professional look.
"""

import streamlit as st

PRIMARY_COLOR = "#4F46E5"   # Indigo
ACCENT_COLOR = "#22C55E"    # Green
WARNING_COLOR = "#F59E0B"   # Amber
DANGER_COLOR = "#EF4444"    # Red
DARK_BG = "#0F172A"


def apply_custom_css():
    """Inject custom CSS into the Streamlit app."""
    st.markdown(f"""
        <style>
            /* ---------- Global ---------- */
            .stApp {{
                background-color: #F4F6FB;
            }}

            /* ---------- Header / Title ---------- */
            .metrax-header {{
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                padding: 1rem 0 0.25rem 0;
            }}
            .metrax-title {{
                font-size: 2.4rem;
                font-weight: 800;
                color: {PRIMARY_COLOR};
                margin-bottom: 0;
                letter-spacing: 1px;
            }}
            .metrax-tagline {{
                font-size: 1rem;
                color: #6B7280;
                font-style: italic;
                margin-top: -0.3rem;
            }}

            /* ---------- KPI Cards ---------- */
            .kpi-card {{
                background: #FFFFFF;
                border-radius: 14px;
                padding: 1.1rem 1.2rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06);
                border-left: 6px solid {PRIMARY_COLOR};
                text-align: left;
            }}
            .kpi-label {{
                font-size: 0.85rem;
                color: #6B7280;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .kpi-value {{
                font-size: 1.8rem;
                font-weight: 800;
                color: #111827;
                margin-top: 0.2rem;
            }}

            /* ---------- Badges ---------- */
            .badge {{
                display: inline-block;
                padding: 0.25rem 0.7rem;
                border-radius: 999px;
                font-size: 0.8rem;
                font-weight: 700;
                color: white;
            }}

            /* ---------- Section Headers ---------- */
            .section-header {{
                font-size: 1.3rem;
                font-weight: 700;
                color: #1F2937;
                border-bottom: 2px solid {PRIMARY_COLOR};
                padding-bottom: 0.3rem;
                margin: 1.2rem 0 0.8rem 0;
            }}

            /* ---------- Notification boxes ---------- */
            .notif-success {{
                background:#ECFDF5; border-left:5px solid {ACCENT_COLOR};
                padding:0.7rem 1rem; border-radius:8px; margin-bottom:0.5rem;
                color:#065F46; font-weight:600;
            }}
            .notif-warning {{
                background:#FFFBEB; border-left:5px solid {WARNING_COLOR};
                padding:0.7rem 1rem; border-radius:8px; margin-bottom:0.5rem;
                color:#92400E; font-weight:600;
            }}
            .notif-danger {{
                background:#FEF2F2; border-left:5px solid {DANGER_COLOR};
                padding:0.7rem 1rem; border-radius:8px; margin-bottom:0.5rem;
                color:#991B1B; font-weight:600;
            }}
            .notif-info {{
                background:#EFF6FF; border-left:5px solid {PRIMARY_COLOR};
                padding:0.7rem 1rem; border-radius:8px; margin-bottom:0.5rem;
                color:#1E3A8A; font-weight:600;
            }}

            /* ---------- Sidebar ---------- */
            section[data-testid="stSidebar"] {{
                background-color: #111827;
            }}
            section[data-testid="stSidebar"] * {{
                color: #F9FAFB !important;
            }}

            /* ---------- Profile Card ---------- */
            .profile-card {{
                background:#FFFFFF; border-radius:16px; padding:1.5rem;
                box-shadow: 0 2px 12px rgba(0,0,0,0.07);
            }}
            .profile-field-label {{
                font-size:0.78rem; color:#6B7280; font-weight:700;
                text-transform: uppercase; letter-spacing:0.4px;
            }}
            .profile-field-value {{
                font-size:1.05rem; color:#111827; font-weight:600; margin-bottom:0.6rem;
            }}
        </style>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    """Render a consistent page header (title + optional subtitle)."""
    st.markdown(f"""
        <div class="metrax-header">
            <div class="metrax-title">{title}</div>
            {f'<div class="metrax-tagline">{subtitle}</div>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)


def kpi_card(label: str, value: str):
    """Render a single KPI card."""
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)


def badge(text: str, color: str):
    """Render an inline colored badge."""
    return f'<span class="badge" style="background-color:{color};">{text}</span>'


def section_header(text: str):
    """Render a styled section header."""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def notification(message: str, kind: str = "info"):
    """Render a styled notification banner.

    kind: one of 'success', 'warning', 'danger', 'info'
    """
    css_class = {
        "success": "notif-success",
        "warning": "notif-warning",
        "danger": "notif-danger",
        "info": "notif-info",
    }.get(kind, "notif-info")
    st.markdown(f'<div class="{css_class}">{message}</div>', unsafe_allow_html=True)