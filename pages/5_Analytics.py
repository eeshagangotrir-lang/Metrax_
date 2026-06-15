"""
pages/5_Analytics.py
-----------------------
Analytics Dashboard

Plotly charts:
    - Daily Sales Trend
    - Weekly Sales
    - Monthly Sales
    - Revenue Analysis
    - Conversion Rate
    - Growth Percentage
    - Sales Forecast
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database.db import init_db
from utils.auth import init_session_state, require_login
from utils.styling import apply_custom_css, page_header, section_header, notification
from utils.data_access import get_sales_entries
from utils.calculations import (
    monthly_sales_series, simple_forecast, calculate_growth_percentage
)

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------
st.set_page_config(page_title="Analytics | Metrax", page_icon="📊", layout="wide")
init_db()
init_session_state()
apply_custom_css()
require_login()

user = st.session_state["user"]
page_header("📊 Analytics Dashboard", "Measure. Monitor. Maximize.")
st.divider()

# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
sales_df = get_sales_entries(employee_id=user["employee_id"])

if sales_df.empty:
    notification("No sales data yet. Add entries in the <b>Sales Entry</b> page to unlock analytics.", "info")
    st.stop()

sales_df["entry_date"] = pd.to_datetime(sales_df["entry_date"])

# ------------------------------------------------------------------
# 1. DAILY SALES TREND
# ------------------------------------------------------------------
section_header("📈 Daily Sales Trend")

daily = sales_df.groupby("entry_date", as_index=False).agg(
    sales_closed=("sales_closed", "sum"),
    customers_visited=("customers_visited", "sum"),
    revenue_generated=("revenue_generated", "sum"),
).sort_values("entry_date")

fig_daily = px.line(
    daily, x="entry_date", y="sales_closed", markers=True,
    title="Daily Sales Closed", labels={"entry_date": "Date", "sales_closed": "Sales Closed"}
)
fig_daily.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_daily, use_container_width=True)

# ------------------------------------------------------------------
# 2. WEEKLY SALES
# ------------------------------------------------------------------
section_header("📅 Weekly Sales")

weekly = sales_df.copy()
weekly["week"] = weekly["entry_date"].dt.to_period("W").astype(str)
weekly_agg = weekly.groupby("week", as_index=False).agg(
    sales_closed=("sales_closed", "sum"),
    revenue_generated=("revenue_generated", "sum"),
).sort_values("week")

fig_weekly = px.bar(
    weekly_agg, x="week", y="sales_closed",
    title="Weekly Sales Closed", labels={"week": "Week", "sales_closed": "Sales Closed"},
    color_discrete_sequence=["#4F46E5"]
)
fig_weekly.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_weekly, use_container_width=True)

# ------------------------------------------------------------------
# 3. MONTHLY SALES
# ------------------------------------------------------------------
section_header("🗓️ Monthly Sales")

monthly = monthly_sales_series(sales_df)

fig_monthly = px.bar(
    monthly, x="month", y="sales_closed",
    title="Monthly Sales Closed", labels={"month": "Month", "sales_closed": "Sales Closed"},
    color_discrete_sequence=["#22C55E"]
)
fig_monthly.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_monthly, use_container_width=True)

# ------------------------------------------------------------------
# 4. REVENUE ANALYSIS
# ------------------------------------------------------------------
section_header("💰 Revenue Analysis")

fig_revenue = px.area(
    monthly, x="month", y="revenue_generated",
    title="Monthly Revenue (₹)", labels={"month": "Month", "revenue_generated": "Revenue (₹)"},
    color_discrete_sequence=["#F59E0B"]
)
fig_revenue.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_revenue, use_container_width=True)

# ------------------------------------------------------------------
# 5. CONVERSION RATE
# ------------------------------------------------------------------
section_header("🎯 Conversion Rate")

monthly["conversion_rate"] = monthly.apply(
    lambda row: (row["sales_closed"] / row["customers_visited"] * 100)
    if row["customers_visited"] > 0 else 0,
    axis=1
)

fig_conv = px.line(
    monthly, x="month", y="conversion_rate", markers=True,
    title="Monthly Conversion Rate (%)",
    labels={"month": "Month", "conversion_rate": "Conversion Rate (%)"},
    color_discrete_sequence=["#EF4444"]
)
fig_conv.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_conv, use_container_width=True)

avg_conversion = monthly["conversion_rate"].mean()
st.metric("Average Conversion Rate", f"{avg_conversion:.1f}%")

# ------------------------------------------------------------------
# 6. GROWTH PERCENTAGE
# ------------------------------------------------------------------
section_header("📊 Growth Percentage (Month-over-Month)")

monthly_sorted = monthly.sort_values("month").reset_index(drop=True)
growth_values = [0.0]
for i in range(1, len(monthly_sorted)):
    growth_values.append(
        calculate_growth_percentage(
            monthly_sorted.loc[i, "sales_closed"],
            monthly_sorted.loc[i - 1, "sales_closed"]
        )
    )
monthly_sorted["growth_pct"] = growth_values

fig_growth = px.bar(
    monthly_sorted, x="month", y="growth_pct",
    title="Month-over-Month Sales Growth (%)",
    labels={"month": "Month", "growth_pct": "Growth (%)"},
    color="growth_pct",
    color_continuous_scale=["#EF4444", "#F59E0B", "#22C55E"]
)
fig_growth.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_growth, use_container_width=True)

# ------------------------------------------------------------------
# 7. SALES FORECAST
# ------------------------------------------------------------------
section_header("🔮 Sales Forecast (Next 3 Months)")

if len(monthly_sorted) < 2:
    notification("Need at least 2 months of data to generate a forecast.", "info")
else:
    forecast_values = simple_forecast(monthly_sorted["sales_closed"], periods_ahead=3)

    # Build forecast month labels by adding periods to the last month
    last_period = pd.Period(monthly_sorted["month"].iloc[-1], freq="M")
    forecast_months = [str(last_period + i) for i in range(1, 4)]

    history_df = monthly_sorted[["month", "sales_closed"]].copy()
    history_df["type"] = "Actual"
    history_df = history_df.rename(columns={"sales_closed": "value"})

    forecast_df = pd.DataFrame({
        "month": forecast_months,
        "value": forecast_values,
        "type": "Forecast"
    })

    combined = pd.concat([history_df, forecast_df], ignore_index=True)

    fig_forecast = go.Figure()
    actual = combined[combined["type"] == "Actual"]
    forecast = combined[combined["type"] == "Forecast"]

    fig_forecast.add_trace(go.Scatter(
        x=actual["month"], y=actual["value"], mode="lines+markers",
        name="Actual", line=dict(color="#4F46E5")
    ))
    fig_forecast.add_trace(go.Scatter(
        x=pd.concat([actual["month"].tail(1), forecast["month"]]),
        y=pd.concat([actual["value"].tail(1), forecast["value"]]),
        mode="lines+markers", name="Forecast",
        line=dict(color="#22C55E", dash="dash")
    ))

    fig_forecast.update_layout(
        title="Sales Forecast (Linear Trend)",
        template="plotly_white", height=400,
        xaxis_title="Month", yaxis_title="Sales Closed"
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

    notification(
        f"Forecasted sales for the next 3 months: "
        f"{', '.join(f'{m}: {v:.0f}' for m, v in zip(forecast_months, forecast_values))}",
        "info"
    )