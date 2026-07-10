"""
Global Superstore — Interactive Business Intelligence Dashboard
Task 5: Data Analytics Internship (Codiora Software House)

Run with:
    streamlit run streamlit_dashboard.py

Expects either 'superstore_cleaned.csv' (produced by Superstore_BI_Analysis.ipynb)
or the raw 'superstore.csv' in the same folder — it will clean the raw file
automatically if the cleaned version isn't found.
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# --------------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="Global Superstore BI Dashboard",
    page_icon="📊",
    layout="wide",
)

# --------------------------------------------------------------------------------
# Data loading & cleaning (cached)
# --------------------------------------------------------------------------------
@st.cache_data
def load_data():
    cleaned_path = "superstore_cleaned.csv"
    raw_path = "superstore.csv"

    if os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
    elif os.path.exists(raw_path):
        df = pd.read_csv(raw_path)
        df = df.drop_duplicates()
        df.columns = [c.strip().replace(".", "_").lower() for c in df.columns]
        drop_cols = [c for c in ["记录数", "market2", "weeknum"] if c in df.columns]
        df = df.drop(columns=drop_cols, errors="ignore")
        df = df[(df["sales"] > 0) & (df["quantity"] > 0)].reset_index(drop=True)
    else:
        st.error("Could not find 'superstore_cleaned.csv' or 'superstore.csv' in the app folder.")
        st.stop()

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    if "order_month" not in df.columns:
        df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    if "order_year" not in df.columns:
        df["order_year"] = df["order_date"].dt.year

    return df


df = load_data()

# --------------------------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------------------------
st.sidebar.header("🔎 Filters")

regions = sorted(df["region"].dropna().unique().tolist())
categories = sorted(df["category"].dropna().unique().tolist())

selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

subcats_available = sorted(
    df.loc[df["category"].isin(selected_categories), "sub_category"].dropna().unique().tolist()
)
selected_subcats = st.sidebar.multiselect("Sub-Category", subcats_available, default=subcats_available)

years = sorted(df["order_year"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect("Order Year", years, default=years)

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit · Plotly · Pandas")

# --------------------------------------------------------------------------------
# Apply filters
# --------------------------------------------------------------------------------
mask = (
    df["region"].isin(selected_regions)
    & df["category"].isin(selected_categories)
    & df["sub_category"].isin(selected_subcats)
    & df["order_year"].isin(selected_years)
)
fdf = df.loc[mask].copy()

# --------------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------------
st.title("📊 Global Superstore — Business Intelligence Dashboard")
st.caption("Sales, Profit, and Segment-wise Performance Analysis")

if fdf.empty:
    st.warning("No data matches the current filter selection. Please broaden your filters.")
    st.stop()

# --------------------------------------------------------------------------------
# KPI row
# --------------------------------------------------------------------------------
total_sales = fdf["sales"].sum()
total_profit = fdf["profit"].sum()
total_orders = fdf["order_id"].nunique()
profit_margin = (total_profit / total_sales * 100) if total_sales else 0
avg_discount = fdf["discount"].mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Total Sales", f"${total_sales:,.0f}")
k2.metric("📈 Total Profit", f"${total_profit:,.0f}")
k3.metric("🧾 Total Orders", f"{total_orders:,}")
k4.metric("📊 Profit Margin", f"{profit_margin:.1f}%")
k5.metric("🏷️ Avg. Discount", f"{avg_discount:.1f}%")

st.markdown("---")

# --------------------------------------------------------------------------------
# Row 1: Sales & Profit trend + Category performance
# --------------------------------------------------------------------------------
c1, c2 = st.columns((2, 1))

with c1:
    st.subheader("📅 Monthly Sales & Profit Trend")
    monthly = fdf.groupby("order_month")[["sales", "profit"]].sum().reset_index().sort_values("order_month")
    fig_trend = px.line(
        monthly, x="order_month", y=["sales", "profit"],
        labels={"order_month": "Month", "value": "Amount", "variable": "Metric"},
        markers=True,
    )
    fig_trend.update_layout(legend_title_text="", height=420)
    st.plotly_chart(fig_trend, use_container_width=True)

with c2:
    st.subheader("🗂️ Sales by Category")
    cat_sales = fdf.groupby("category")["sales"].sum().reset_index()
    fig_cat = px.pie(cat_sales, names="category", values="sales", hole=0.45)
    fig_cat.update_layout(height=420)
    st.plotly_chart(fig_cat, use_container_width=True)

# --------------------------------------------------------------------------------
# Row 2: Region performance + Sub-Category profit
# --------------------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("🌍 Sales vs Profit by Region")
    region_perf = fdf.groupby("region")[["sales", "profit"]].sum().reset_index().sort_values("sales", ascending=False)
    fig_region = px.bar(
        region_perf, x="region", y=["sales", "profit"], barmode="group",
        labels={"value": "Amount", "region": "Region", "variable": "Metric"},
    )
    fig_region.update_layout(legend_title_text="", height=420)
    st.plotly_chart(fig_region, use_container_width=True)

with c4:
    st.subheader("📦 Profit by Sub-Category")
    subcat_perf = fdf.groupby("sub_category")["profit"].sum().reset_index().sort_values("profit")
    fig_subcat = px.bar(
        subcat_perf, x="profit", y="sub_category", orientation="h",
        color=subcat_perf["profit"] > 0,
        color_discrete_map={True: "#2ca02c", False: "#d62728"},
        labels={"profit": "Profit", "sub_category": "Sub-Category"},
    )
    fig_subcat.update_layout(showlegend=False, height=420)
    st.plotly_chart(fig_subcat, use_container_width=True)

# --------------------------------------------------------------------------------
# Row 3: Segment performance + Top 5 customers
# --------------------------------------------------------------------------------
c5, c6 = st.columns(2)

with c5:
    st.subheader("👥 Segment-wise Performance")
    seg_perf = fdf.groupby("segment")[["sales", "profit"]].sum().reset_index()
    fig_seg = px.bar(
        seg_perf, x="segment", y=["sales", "profit"], barmode="group",
        labels={"value": "Amount", "segment": "Segment", "variable": "Metric"},
    )
    fig_seg.update_layout(legend_title_text="", height=420)
    st.plotly_chart(fig_seg, use_container_width=True)

with c6:
    st.subheader("🏆 Top 5 Customers by Sales")
    top5 = (
        fdf.groupby("customer_name")["sales"].sum()
        .sort_values(ascending=False).head(5).reset_index()
    )
    fig_top5 = px.bar(
        top5.sort_values("sales"), x="sales", y="customer_name", orientation="h",
        labels={"sales": "Total Sales", "customer_name": "Customer"},
        color="sales", color_continuous_scale="Blues",
    )
    fig_top5.update_layout(coloraxis_showscale=False, height=420)
    st.plotly_chart(fig_top5, use_container_width=True)

    st.dataframe(
        top5.rename(columns={"customer_name": "Customer", "sales": "Total Sales ($)"})
            .style.format({"Total Sales ($)": "{:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# --------------------------------------------------------------------------------
# Row 4: Discount vs Profit + Data table
# --------------------------------------------------------------------------------
c7, c8 = st.columns((1, 1))

with c7:
    st.subheader("🏷️ Discount vs Profit")
    sample = fdf.sample(min(3000, len(fdf)), random_state=42)
    fig_disc = px.scatter(
        sample, x="discount", y="profit", opacity=0.4,
        labels={"discount": "Discount", "profit": "Profit"},
    )
    fig_disc.update_layout(height=380)
    st.plotly_chart(fig_disc, use_container_width=True)

with c8:
    st.subheader("📋 Filtered Data (first 200 rows)")
    st.dataframe(
        fdf[["order_date", "customer_name", "category", "sub_category",
             "region", "segment", "sales", "profit", "discount"]].head(200),
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    f"Showing {len(fdf):,} of {len(df):,} total records based on the selected filters."
)
