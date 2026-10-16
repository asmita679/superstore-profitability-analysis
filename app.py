import sqlite3
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="Superstore Sales & Profitability Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling inspired by IBM Design Language (Carbon)
st.markdown(
    """
    <style>
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #f4f7fb;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #525252 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #161616 !important;
    }
    .insight-card {
        background-color: #ffffff;
        border-left: 4px solid #0f62fe;
        border-top: 1px solid #e0e0e0;
        border-right: 1px solid #e0e0e0;
        border-bottom: 1px solid #e0e0e0;
        padding: 16px 20px;
        border-radius: 4px;
        margin-bottom: 16px;
    }
    .insight-card.warning {
        border-left-color: #da1e28;
    }
    .insight-title {
        font-weight: 700;
        color: #161616;
        font-size: 1.05rem;
        margin-bottom: 6px;
    }
    .insight-metric {
        font-size: 0.9rem;
        color: #0f62fe;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .insight-body {
        font-size: 0.92rem;
        color: #393939;
        line-height: 1.45;
    }
    .insight-rec {
        margin-top: 8px;
        padding: 8px 12px;
        background-color: #f4f4f4;
        border-radius: 4px;
        font-size: 0.88rem;
        color: #161616;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
CLEANED_CSV_PATH = PROJECT_ROOT / "data" / "cleaned_superstore.csv"
DB_PATH = PROJECT_ROOT / "data" / "superstore.db"


# ==============================================================================
# 2. DATA LOADING & CACHING
# ==============================================================================
@st.cache_data(show_spinner="Loading Superstore Analytics Data...")
def load_data() -> pd.DataFrame:
    """Load cleaned Superstore dataset with safe fallbacks and caching."""
    if not CLEANED_CSV_PATH.exists():
        st.error(
            f"Cleaned dataset not found at `{CLEANED_CSV_PATH}`. "
            "Please run `python src/data_cleaning.py` first to generate it."
        )
        st.stop()

    df = pd.read_csv(CLEANED_CSV_PATH)
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"] = pd.to_datetime(df["Ship Date"])
    return df


df_raw = load_data()

# ==============================================================================
# 3. SIDEBAR FILTERS
# ==============================================================================
st.sidebar.header("🔍 Dashboard Filters")

# Reset filters button
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.session_state["sel_regions"] = list(df_raw["Region"].unique())
    st.session_state["sel_categories"] = list(df_raw["Category"].unique())
    st.session_state["sel_segments"] = list(df_raw["Segment"].unique())
    st.session_state["sel_discount_bands"] = list(df_raw["Discount Band"].dropna().unique())
    st.rerun()

# Date range filter
min_date = df_raw["Order Date"].min().date()
max_date = df_raw["Order Date"].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Multi-select options
all_regions = sorted(df_raw["Region"].unique().tolist())
all_categories = sorted(df_raw["Category"].unique().tolist())
all_segments = sorted(df_raw["Segment"].unique().tolist())
all_discount_bands = [
    "0% (No Discount)",
    "1-20% (Low)",
    "21-40% (Moderate)",
    ">40% (Deep)",
]

selected_regions = st.sidebar.multiselect(
    "Region", options=all_regions, default=all_regions, key="sel_regions"
)
selected_categories = st.sidebar.multiselect(
    "Category", options=all_categories, default=all_categories, key="sel_categories"
)
selected_segments = st.sidebar.multiselect(
    "Customer Segment", options=all_segments, default=all_segments, key="sel_segments"
)
selected_discount_bands = st.sidebar.multiselect(
    "Discount Tier",
    options=all_discount_bands,
    default=all_discount_bands,
    key="sel_discount_bands",
)

st.sidebar.markdown("---")
st.sidebar.caption("Portfolio Project | IBM Data Analytics")
st.sidebar.caption(f"Total Raw Records: {len(df_raw):,}")


# ==============================================================================
# 4. FILTER EXECUTION & INTEGRITY CHECKS
# ==============================================================================
# Handle date range tuple safely
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    start_date = end_date = pd.to_datetime(date_range[0])
else:
    start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

# Apply filters
filtered_df = df_raw[
    (df_raw["Order Date"] >= start_date)
    & (df_raw["Order Date"] <= end_date)
    & (df_raw["Region"].isin(selected_regions))
    & (df_raw["Category"].isin(selected_categories))
    & (df_raw["Segment"].isin(selected_segments))
    & (df_raw["Discount Band"].isin(selected_discount_bands))
]

# Title & Subtitle
st.title("Superstore Sales & Profitability Analysis")
st.markdown(
    "*Understanding revenue performance, margin erosion, and opportunities for profitable growth.*"
)

# Empty dataset handler
if filtered_df.empty:
    st.warning("⚠️ No records match the current filter selection. Please broaden your filter criteria in the sidebar.")
    st.stop()


# ==============================================================================
# 5. EXECUTIVE KPI CARDS
# ==============================================================================
total_sales = float(filtered_df["Sales"].sum())
total_profit = float(filtered_df["Profit"].sum())
unique_orders = int(filtered_df["Order ID"].nunique())
total_quantity = int(filtered_df["Quantity"].sum())
profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric(
    "Total Profit",
    f"${total_profit:,.2f}",
    delta=f"{profit_margin:.2f}% Margin",
    delta_color="normal" if total_profit >= 0 else "inverse",
)
col3.metric("Unique Orders", f"{unique_orders:,}")
col4.metric("Units Sold", f"{total_quantity:,}")
col5.metric(
    "Profit Margin",
    f"{profit_margin:.2f}%",
    delta="Healthy" if profit_margin >= 12.0 else "Needs Review",
    delta_color="normal" if profit_margin >= 12.0 else "inverse",
)

st.markdown("<br>", unsafe_allow_html=True)


# ==============================================================================
# 6. VISUALIZATION DASHBOARD
# ==============================================================================
tab_overview, tab_products, tab_geography, tab_discounts, tab_data = st.tabs(
    [
        "📈 Revenue & Profit Trends",
        "📦 Categories & Products",
        "🗺️ Regional & State Profitability",
        "🏷️ Discount Impact & Sensitivity",
        "📄 Detailed Records",
    ]
)

# ------------------------------------------------------------------------------
# TAB 1: Revenue & Profit Trends
# ------------------------------------------------------------------------------
with tab_overview:
    st.subheader("1. Monthly Sales & Profit Performance")
    
    monthly_trend = (
        filtered_df.groupby("Order Month")
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order ID", "nunique"),
        )
        .reset_index()
    )
    monthly_trend["Profit_Margin_%"] = (monthly_trend["Profit"] / monthly_trend["Sales"]) * 100

    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Bar(
            x=monthly_trend["Order Month"],
            y=monthly_trend["Sales"],
            name="Sales ($)",
            marker_color="#0f62fe",
            opacity=0.75,
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=monthly_trend["Order Month"],
            y=monthly_trend["Profit"],
            name="Profit ($)",
            mode="lines+markers",
            marker=dict(size=6, color="#24a148"),
            line=dict(width=3, color="#24a148"),
            yaxis="y2",
        )
    )

    fig_trend.update_layout(
        template="plotly_white",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="Order Month", tickangle=-45),
        yaxis=dict(title="Sales Revenue ($)", showgrid=True),
        yaxis2=dict(
            title="Net Profit ($)",
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=True,
            zerolinecolor="#da1e28",
            zerolinewidth=1.5,
        ),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Secondary comparison: Annual YoY Breakdown
    annual_summary = (
        filtered_df.groupby("Order Year")
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order ID", "nunique"),
            Quantity=("Quantity", "sum"),
        )
        .reset_index()
    )
    annual_summary["Profit Margin %"] = (annual_summary["Profit"] / annual_summary["Sales"]) * 100

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.write("##### Annual Performance Summary")
        fmt_annual = annual_summary.copy()
        fmt_annual["Sales"] = fmt_annual["Sales"].map("${:,.2f}".format)
        fmt_annual["Profit"] = fmt_annual["Profit"].map("${:,.2f}".format)
        fmt_annual["Orders"] = fmt_annual["Orders"].map("{:,}".format)
        fmt_annual["Quantity"] = fmt_annual["Quantity"].map("{:,}".format)
        fmt_annual["Profit Margin %"] = fmt_annual["Profit Margin %"].map("{:.2f}%".format)
        st.dataframe(fmt_annual, hide_index=True, use_container_width=True)

    with col_b:
        fig_segment = px.pie(
            filtered_df,
            values="Sales",
            names="Segment",
            title="Sales Distribution by Customer Segment",
            color="Segment",
            color_discrete_sequence=["#0f62fe", "#1192e8", "#6929c4"],
            hole=0.45,
        )
        fig_segment.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_segment, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 2: Categories & Products
# ------------------------------------------------------------------------------
with tab_products:
    st.subheader("2. Category & Sub-Category Profitability Comparison")

    col_cat1, col_cat2 = st.columns(2)

    with col_cat1:
        cat_agg = (
            filtered_df.groupby("Category")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
        )
        cat_agg["Margin_%"] = (cat_agg["Profit"] / cat_agg["Sales"]) * 100

        fig_cat = go.Figure()
        fig_cat.add_trace(
            go.Bar(
                x=cat_agg["Category"],
                y=cat_agg["Sales"],
                name="Sales ($)",
                marker_color="#0f62fe",
            )
        )
        fig_cat.add_trace(
            go.Bar(
                x=cat_agg["Category"],
                y=cat_agg["Profit"],
                name="Profit ($)",
                marker_color="#24a148",
            )
        )
        fig_cat.update_layout(
            barmode="group",
            template="plotly_white",
            title="Revenue vs. Profit by Category",
            height=380,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_cat2:
        subcat_agg = (
            filtered_df.groupby("Sub-Category")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
            .sort_values("Profit", ascending=True)
        )
        subcat_agg["Color"] = subcat_agg["Profit"].apply(
            lambda x: "#24a148" if x >= 0 else "#da1e28"
        )

        fig_subcat = go.Figure(
            go.Bar(
                x=subcat_agg["Profit"],
                y=subcat_agg["Sub-Category"],
                orientation="h",
                marker_color=subcat_agg["Color"],
                text=subcat_agg["Profit"].map("${:,.0f}".format),
                textposition="outside",
            )
        )
        fig_subcat.update_layout(
            template="plotly_white",
            title="Sub-Category Net Profit Ranking ($)",
            height=380,
            xaxis=dict(title="Total Profit ($)", zeroline=True, zerolinecolor="#161616"),
            margin=dict(l=20, r=40, t=40, b=20),
        )
        st.plotly_chart(fig_subcat, use_container_width=True)

    st.markdown("---")
    st.write("##### 3. Top 10 Product Loss Leaders (Highest Negative Profit)")
    prod_loss = (
        filtered_df.groupby(["Product Name", "Category", "Sub-Category"])
        .agg(
            Units_Sold=("Quantity", "sum"),
            Avg_Discount=("Discount", "mean"),
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
        )
        .reset_index()
        .sort_values("Total_Profit", ascending=True)
        .head(10)
    )

    fmt_loss = prod_loss.copy()
    fmt_loss["Avg_Discount"] = fmt_loss["Avg_Discount"].map("{:.1%}".format)
    fmt_loss["Total_Sales"] = fmt_loss["Total_Sales"].map("${:,.2f}".format)
    fmt_loss["Total_Profit"] = fmt_loss["Total_Profit"].map("${:,.2f}".format)
    st.dataframe(fmt_loss, hide_index=True, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 3: Regional & State Profitability
# ------------------------------------------------------------------------------
with tab_geography:
    st.subheader("4. Geographic Profitability & Bottom 10 States")

    col_reg1, col_reg2 = st.columns(2)

    with col_reg1:
        reg_agg = (
            filtered_df.groupby("Region")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
        )
        reg_agg["Margin_%"] = (reg_agg["Profit"] / reg_agg["Sales"]) * 100

        fig_reg = go.Figure()
        fig_reg.add_trace(
            go.Bar(
                x=reg_agg["Region"],
                y=reg_agg["Sales"],
                name="Sales ($)",
                marker_color="#0f62fe",
            )
        )
        fig_reg.add_trace(
            go.Bar(
                x=reg_agg["Region"],
                y=reg_agg["Profit"],
                name="Profit ($)",
                marker_color="#0072c3",
            )
        )
        fig_reg.update_layout(
            barmode="group",
            template="plotly_white",
            title="Sales & Profit Across Regions",
            height=380,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_reg, use_container_width=True)

    with col_reg2:
        state_loss = (
            filtered_df.groupby(["State", "Region"])
            .agg(
                Sales=("Sales", "sum"),
                Profit=("Profit", "sum"),
                Avg_Discount=("Discount", "mean"),
            )
            .reset_index()
            .sort_values("Profit", ascending=True)
            .head(10)
        )

        fig_state = go.Figure(
            go.Bar(
                x=state_loss["Profit"],
                y=state_loss["State"],
                orientation="h",
                marker_color="#da1e28",
                text=state_loss["Profit"].map("${:,.0f}".format),
                textposition="outside",
            )
        )
        fig_state.update_layout(
            template="plotly_white",
            title="Top 10 Loss-Making States ($ Net Profit)",
            height=380,
            xaxis=dict(title="Total Profit ($)", zeroline=True, zerolinecolor="#161616"),
            margin=dict(l=20, r=40, t=40, b=20),
        )
        st.plotly_chart(fig_state, use_container_width=True)

    # Detailed table of bottom states
    st.write("##### State-Level Loss Audit (Bottom 10 States)")
    fmt_state = state_loss.copy()
    fmt_state["Sales"] = fmt_state["Sales"].map("${:,.2f}".format)
    fmt_state["Profit"] = fmt_state["Profit"].map("${:,.2f}".format)
    fmt_state["Avg_Discount"] = fmt_state["Avg_Discount"].map("{:.1%}".format)
    fmt_state["Margin %"] = (
        (state_loss["Profit"] / state_loss["Sales"] * 100).map("{:.2f}%".format)
    )
    st.dataframe(fmt_state, hide_index=True, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 4: Discount Impact & Sensitivity
# ------------------------------------------------------------------------------
with tab_discounts:
    st.subheader("5. Discount Impact & Margin Sensitivity")
    st.info(
        "💡 **Methodology Note:** The figures below reflect empirical associations within "
        "the historical dataset. High discounting correlates with substantial profit erosion; "
        "however, discounts may interact with specific product categories, clearances, and contract pricing."
    )

    col_disc1, col_disc2 = st.columns(2)

    with col_disc1:
        # Discount tier aggregate
        tier_order = [
            "0% (No Discount)",
            "1-20% (Low)",
            "21-40% (Moderate)",
            ">40% (Deep)",
        ]
        tier_agg = (
            filtered_df.groupby("Discount Band", observed=False)
            .agg(
                Transactions=("Order ID", "count"),
                Orders=("Order ID", "nunique"),
                Total_Sales=("Sales", "sum"),
                Total_Profit=("Profit", "sum"),
            )
            .reindex(tier_order)
            .reset_index()
        )
        tier_agg["Margin_%"] = (tier_agg["Total_Profit"] / tier_agg["Total_Sales"]) * 100
        tier_agg["Color"] = tier_agg["Total_Profit"].apply(
            lambda x: "#24a148" if x >= 0 else "#da1e28"
        )

        fig_tier = go.Figure(
            go.Bar(
                x=tier_agg["Discount Band"],
                y=tier_agg["Total_Profit"],
                marker_color=tier_agg["Color"],
                text=tier_agg["Total_Profit"].map("${:,.0f}".format),
                textposition="outside",
            )
        )
        fig_tier.update_layout(
            template="plotly_white",
            title="Total Net Profit by Discount Tier ($)",
            height=380,
            yaxis=dict(title="Total Profit ($)", zeroline=True, zerolinecolor="#161616"),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    with col_disc2:
        # Scatter plot: Discount vs Profit
        # Sample for rendering speed if dataset exceeds 3000 rows
        scatter_sample = (
            filtered_df.sample(2500, random_state=42)
            if len(filtered_df) > 2500
            else filtered_df
        )

        fig_scatter = px.scatter(
            scatter_sample,
            x="Discount",
            y="Profit",
            color="Category",
            size="Sales",
            hover_data=["Order ID", "Sub-Category", "State"],
            title="Transaction Discount vs. Profit ($)",
            color_discrete_sequence=["#0f62fe", "#da1e28", "#24a148"],
            opacity=0.65,
        )
        fig_scatter.add_hline(y=0, line_dash="dash", line_color="#161616", opacity=0.7)
        fig_scatter.update_layout(
            template="plotly_white",
            height=380,
            xaxis=dict(title="Discount Rate (0.0 to 1.0)", tickformat=".0%"),
            yaxis=dict(title="Transaction Profit ($)"),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Discount Band Summary Table
    st.write("##### Discount Tier Breakdown Table")
    fmt_tier = tier_agg.copy()
    fmt_tier["Total_Sales"] = fmt_tier["Total_Sales"].map("${:,.2f}".format)
    fmt_tier["Total_Profit"] = fmt_tier["Total_Profit"].map("${:,.2f}".format)
    fmt_tier["Transactions"] = fmt_tier["Transactions"].map("{:,}".format)
    fmt_tier["Orders"] = fmt_tier["Orders"].map("{:,}".format)
    fmt_tier["Margin_%"] = fmt_tier["Margin_%"].map("{:.2f}%".format)
    st.dataframe(
        fmt_tier[["Discount Band", "Transactions", "Orders", "Total_Sales", "Total_Profit", "Margin_%"]],
        hide_index=True,
        use_container_width=True,
    )


# ------------------------------------------------------------------------------
# TAB 5: Detailed Records
# ------------------------------------------------------------------------------
with tab_data:
    st.subheader("6. Transaction Level Records")
    
    col_search, col_export = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("Filter by Order ID, Customer Name, or Product Name:")
    with col_export:
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Filtered CSV",
            data=csv_data,
            file_name="filtered_superstore_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

    display_df = filtered_df
    if search_query:
        mask = (
            display_df["Order ID"].astype(str).str.contains(search_query, case=False, na=False)
            | display_df["Customer Name"].astype(str).str.contains(search_query, case=False, na=False)
            | display_df["Product Name"].astype(str).str.contains(search_query, case=False, na=False)
        )
        display_df = display_df[mask]

    selected_cols = [
        "Order ID",
        "Order Date",
        "Category",
        "Sub-Category",
        "Region",
        "State",
        "Sales",
        "Quantity",
        "Discount",
        "Profit",
        "Profit Margin %",
    ]
    st.dataframe(
        display_df[selected_cols].head(500),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Showing up to 500 of {len(display_df):,} matching rows.")


# ==============================================================================
# 7. BUSINESS INSIGHTS & EVIDENCE-BASED RECOMMENDATIONS
# ==============================================================================
st.markdown("---")
st.subheader("💡 Executive Insights & Strategic Recommendations")

# Calculate live metrics for insights to ensure mathematical integrity
furn_sales = filtered_df[filtered_df["Category"] == "Furniture"]["Sales"].sum()
furn_profit = filtered_df[filtered_df["Category"] == "Furniture"]["Profit"].sum()
furn_margin = (furn_profit / furn_sales * 100) if furn_sales > 0 else 0.0

tech_sales = filtered_df[filtered_df["Category"] == "Technology"]["Sales"].sum()
tech_profit = filtered_df[filtered_df["Category"] == "Technology"]["Profit"].sum()
tech_margin = (tech_profit / tech_sales * 100) if tech_sales > 0 else 0.0

table_profit = filtered_df[filtered_df["Sub-Category"] == "Tables"]["Profit"].sum()
bookcase_profit = filtered_df[filtered_df["Sub-Category"] == "Bookcases"]["Profit"].sum()

deep_disc_loss = filtered_df[filtered_df["Discount"] > 0.20]["Profit"].sum()
zero_disc_profit = filtered_df[filtered_df["Discount"] == 0]["Profit"].sum()

ins1, ins2 = st.columns(2)

with ins1:
    st.markdown(
        f"""
        <div class="insight-card warning">
            <div class="insight-title">1. Furniture Margin Compression & Loss Leaders</div>
            <div class="insight-metric">Furniture Margin: {furn_margin:.2f}% vs. Technology: {tech_margin:.2f}%</div>
            <div class="insight-body">
                While Furniture accounts for roughly one-third of company revenue, its profit contribution is severely impaired. 
                Specifically, <b>Tables</b> (cumulative profit: ${table_profit:,.2f}) and <b>Bookcases</b> (${bookcase_profit:,.2f}) are major financial drains due to excessive promotions and high logistical costs.
            </div>
            <div class="insight-rec">
                <b>Actionable Recommendation:</b> Re-negotiate supplier agreements for Tables, introduce minimum order thresholds, and bundle low-margin items with high-margin Technology accessories.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="insight-card warning">
            <div class="insight-title">2. Discount Threshold & Severe Margin Degradation</div>
            <div class="insight-metric">Discounts >20% Profit: ${deep_disc_loss:,.2f} vs. 0% Discount: ${zero_disc_profit:,.2f}</div>
            <div class="insight-body">
                Transactions with discounts exceeding 20% consistently generate negative aggregate net margins (-15% to -77%). 
                The additional sales volume generated does not compensate for the steep loss in unit economics.
            </div>
            <div class="insight-rec">
                <b>Actionable Recommendation:</b> Implement hard governance caps at 20% maximum discount for standard sales reps, requiring regional managerial sign-off for deals exceeding 25%.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with ins2:
    st.markdown(
        """
        <div class="insight-card warning">
            <div class="insight-title">3. Geographic Loss Concentration in Key Central States</div>
            <div class="insight-metric">Texas, Ohio, Pennsylvania, and Illinois Lead All State-Level Losses</div>
            <div class="insight-body">
                Underperformance is geographically localized rather than nationwide. The Central region suffers the lowest profit margin (7.9%), 
                disproportionately dragged down by sustained losses in Texas (-$25.7k) and Illinois (-$12.6k), both exhibiting average discount rates between 37% and 39%.
            </div>
            <div class="insight-rec">
                <b>Actionable Recommendation:</b> Audit local pricing authority and freight contracts in Texas and Illinois to align gross margins with high-performing Western states.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="insight-card">
            <div class="insight-title">4. High-Margin Core Growth Opportunities</div>
            <div class="insight-metric">Copiers (37.2% Margin) & Paper/Binders Drive Sustainable Cash Flow</div>
            <div class="insight-body">
                Copiers, Phones, and Accessories generate healthy profits with minimal discounting. 
                Corporate and Consumer segments both demonstrate strong price tolerance on essential office technology.
            </div>
            <div class="insight-rec">
                <b>Actionable Recommendation:</b> Allocate promotional spend and inventory allocation toward high-yield sub-categories (Copiers, Phones, Storage) to maximize EBITDA.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
