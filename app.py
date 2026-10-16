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
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        min-width: 0 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #8b949e !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #f0f6fc !important;
        white-space: nowrap !important;
        overflow: visible !important;
        line-height: 1.25 !important;
        letter-spacing: -0.2px;
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
        min-height: 220px;
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
# 3. SIDEBAR FILTERS & STATE MANAGEMENT
# ==============================================================================
st.sidebar.header("🔍 Dashboard Filters")

min_date = df_raw["Order Date"].min().date()
max_date = df_raw["Order Date"].max().date()
all_regions = sorted(df_raw["Region"].unique().tolist())
all_categories = sorted(df_raw["Category"].unique().tolist())
all_segments = sorted(df_raw["Segment"].unique().tolist())
all_discount_bands = [
    "0% (No Discount)",
    "1-20% (Low)",
    "21-40% (Moderate)",
    ">40% (Deep)",
]

# Check if a reset was requested from any button
if st.session_state.get("needs_reset", False):
    st.session_state["sel_date_range"] = (min_date, max_date)
    st.session_state["sel_regions"] = all_regions
    st.session_state["sel_categories"] = all_categories
    st.session_state["sel_segments"] = all_segments
    st.session_state["sel_discount_bands"] = all_discount_bands
    st.session_state["needs_reset"] = False

# Initialize session state for all filters on first run
if "sel_date_range" not in st.session_state:
    st.session_state["sel_date_range"] = (min_date, max_date)
if "sel_regions" not in st.session_state:
    st.session_state["sel_regions"] = all_regions
if "sel_categories" not in st.session_state:
    st.session_state["sel_categories"] = all_categories
if "sel_segments" not in st.session_state:
    st.session_state["sel_segments"] = all_segments
if "sel_discount_bands" not in st.session_state:
    st.session_state["sel_discount_bands"] = all_discount_bands


def request_filter_reset():
    """Flag that a full filter reset should be performed on the next run."""
    st.session_state["needs_reset"] = True


st.sidebar.button(
    "🔄 Reset All Filters",
    on_click=request_filter_reset,
    use_container_width=True,
)

# Date range filter
date_range = st.sidebar.date_input(
    "Order Date Range",
    min_value=min_date,
    max_value=max_date,
    key="sel_date_range",
)

# Multi-select filters
selected_regions = st.sidebar.multiselect(
    "Region",
    options=all_regions,
    key="sel_regions",
)
selected_categories = st.sidebar.multiselect(
    "Category",
    options=all_categories,
    key="sel_categories",
)
selected_segments = st.sidebar.multiselect(
    "Customer Segment",
    options=all_segments,
    key="sel_segments",
)
selected_discount_bands = st.sidebar.multiselect(
    "Discount Tier",
    options=all_discount_bands,
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

# Empty dataset handler with clear recovery action
if filtered_df.empty:
    st.warning(
        "⚠️ **No matching records found for the current filter criteria.**\n\n"
        "Please adjust your date range, regions, categories, segments, or discount tiers in the sidebar to view data."
    )
    st.button("🔄 Reset Filters Now", on_click=request_filter_reset)
    st.stop()


# ==============================================================================
# 5. EXECUTIVE KPI CARDS
# ==============================================================================
total_sales = float(filtered_df["Sales"].sum())
total_profit = float(filtered_df["Profit"].sum())
unique_orders = int(filtered_df["Order ID"].nunique())
total_quantity = int(filtered_df["Quantity"].sum())
profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0.0

# Five evenly spaced, visually balanced columns across the available content width
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Unique Orders", f"{unique_orders:,}")
col4.metric("Units Sold", f"{total_quantity:,}")
col5.metric("Profit Margin", f"{profit_margin:.2f}%")

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
    monthly_trend["Profit_Margin_%"] = (
        monthly_trend["Profit"] / monthly_trend["Sales"] * 100
    ).fillna(0)

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

    # Annual Performance Summary
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
    annual_summary["Profit Margin %"] = (
        annual_summary["Profit"] / annual_summary["Sales"] * 100
    ).fillna(0)

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
        cat_agg["Margin_%"] = (cat_agg["Profit"] / cat_agg["Sales"] * 100).fillna(0)

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
    st.write("##### 3. Top 10 Product Loss Leaders (Highest Negative Profit in Filtered View)")
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
        reg_agg["Margin_%"] = (reg_agg["Profit"] / reg_agg["Sales"] * 100).fillna(0)

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

        state_loss["Color"] = state_loss["Profit"].apply(
            lambda x: "#24a148" if x >= 0 else "#da1e28"
        )
        fig_state = go.Figure(
            go.Bar(
                x=state_loss["Profit"],
                y=state_loss["State"],
                orientation="h",
                marker_color=state_loss["Color"],
                text=state_loss["Profit"].map("${:,.0f}".format),
                textposition="outside",
            )
        )
        fig_state.update_layout(
            template="plotly_white",
            title="Bottom 10 States by Net Profit ($)",
            height=380,
            xaxis=dict(title="Total Profit ($)", zeroline=True, zerolinecolor="#161616"),
            margin=dict(l=20, r=40, t=40, b=20),
        )
        st.plotly_chart(fig_state, use_container_width=True)

    # Detailed table of bottom states
    st.write("##### State-Level Performance Audit (Bottom 10 States in Current Filter)")
    fmt_state = state_loss.copy()
    fmt_state["Sales"] = fmt_state["Sales"].map("${:,.2f}".format)
    fmt_state["Profit"] = fmt_state["Profit"].map("${:,.2f}".format)
    fmt_state["Avg_Discount"] = fmt_state["Avg_Discount"].map("{:.1%}".format)
    fmt_state["Margin %"] = (
        (state_loss["Profit"] / state_loss["Sales"] * 100).fillna(0).map("{:.2f}%".format)
    )
    st.dataframe(
        fmt_state[["State", "Region", "Sales", "Profit", "Avg_Discount", "Margin %"]],
        hide_index=True,
        use_container_width=True,
    )


# ------------------------------------------------------------------------------
# TAB 4: Discount Impact & Sensitivity
# ------------------------------------------------------------------------------
with tab_discounts:
    st.subheader("5. Discount Impact & Margin Sensitivity")
    st.info(
        "💡 **Methodology Note:** The figures below reflect empirical associations within "
        "the filtered dataset. High discounting correlates with substantial profit erosion; "
        "however, discounts may interact with specific product categories, clearances, and contract pricing."
    )

    col_disc1, col_disc2 = st.columns(2)

    with col_disc1:
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
            .fillna(0)
            .reset_index()
        )
        tier_agg["Margin_%"] = (
            tier_agg["Total_Profit"] / tier_agg["Total_Sales"] * 100
        ).fillna(0)
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
        scatter_sample = (
            filtered_df.sample(min(2500, len(filtered_df)), random_state=42)
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

    # Search query applied directly to filtered records
    search_query = st.text_input(
        "Filter table by Order ID, Customer Name, or Product Name:",
        key="table_search_input",
    )

    display_df = filtered_df
    if search_query:
        mask = (
            display_df["Order ID"].astype(str).str.contains(search_query, case=False, na=False)
            | display_df["Customer Name"].astype(str).str.contains(search_query, case=False, na=False)
            | display_df["Product Name"].astype(str).str.contains(search_query, case=False, na=False)
        )
        display_df = display_df[mask]

    col_search_info, col_export = st.columns([3, 1])
    with col_search_info:
        st.caption(f"Displaying {len(display_df):,} of {len(filtered_df):,} filtered transactions.")
    with col_export:
        # Export reflects the EXACT filtered and searched records
        csv_data = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"📥 Export Filtered CSV ({len(display_df):,} rows)",
            data=csv_data,
            file_name="filtered_superstore_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

    selected_cols = [
        "Order ID",
        "Order Date",
        "Customer Name",
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
    if len(display_df) > 500:
        st.caption(f"Showing first 500 rows. Use 'Export Filtered CSV' to download all {len(display_df):,} records.")


# ==============================================================================
# 7. BUSINESS INSIGHTS & EVIDENCE-BASED RECOMMENDATIONS
# ==============================================================================
st.markdown("---")
st.subheader("💡 Executive Insights & Strategic Recommendations")

# Compute live, dynamic analytics from filtered_df to prevent stale or hardcoded figures
cat_profit_summary = filtered_df.groupby("Category").agg(
    Sales=("Sales", "sum"), Profit=("Profit", "sum")
)
cat_profit_summary["Margin %"] = (
    cat_profit_summary["Profit"] / cat_profit_summary["Sales"] * 100
).fillna(0)

subcat_profit_summary = (
    filtered_df.groupby("Sub-Category")["Profit"].sum().sort_values(ascending=True)
)
loss_subcats = subcat_profit_summary[subcat_profit_summary < 0]

deep_disc_df = filtered_df[filtered_df["Discount"] > 0.20]
deep_disc_sales = deep_disc_df["Sales"].sum()
deep_disc_profit = deep_disc_df["Profit"].sum()
deep_disc_margin = (deep_disc_profit / deep_disc_sales * 100) if deep_disc_sales > 0 else 0.0

low_disc_df = filtered_df[filtered_df["Discount"] <= 0.20]
low_disc_sales = low_disc_df["Sales"].sum()
low_disc_profit = low_disc_df["Profit"].sum()
low_disc_margin = (low_disc_profit / low_disc_sales * 100) if low_disc_sales > 0 else 0.0

state_profit_summary = (
    filtered_df.groupby("State")
    .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Avg_Discount=("Discount", "mean"))
    .sort_values("Profit", ascending=True)
)
loss_states = state_profit_summary[state_profit_summary["Profit"] < 0]

top_profit_subcats = (
    filtered_df.groupby("Sub-Category")
    .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    .sort_values("Profit", ascending=False)
)
top_profit_subcats["Margin %"] = (
    top_profit_subcats["Profit"] / top_profit_subcats["Sales"] * 100
).fillna(0)

# Build Dynamic Insight 1: Category Margins & Loss Sub-Categories
if not cat_profit_summary.empty:
    lowest_cat = cat_profit_summary["Margin %"].idxmin()
    lowest_cat_margin = cat_profit_summary.loc[lowest_cat, "Margin %"]
    highest_cat = cat_profit_summary["Margin %"].idxmax()
    highest_cat_margin = cat_profit_summary.loc[highest_cat, "Margin %"]
    cat_metric_text = (
        f"Lowest: {lowest_cat} ({lowest_cat_margin:.2f}%) vs. Highest: {highest_cat} ({highest_cat_margin:.2f}%)"
    )
    if not loss_subcats.empty:
        worst_subcat_list = ", ".join(
            [f"<b>{name}</b> (${val:,.2f})" for name, val in loss_subcats.head(2).items()]
        )
        cat_body_text = (
            f"Within the filtered slice, <b>{lowest_cat}</b> demonstrates the lowest margin efficiency. "
            f"Key sub-category loss drivers include: {worst_subcat_list}."
        )
    else:
        best_sub = subcat_profit_summary.index[-1]
        best_val = subcat_profit_summary.iloc[-1]
        cat_body_text = (
            f"All sub-categories in the current selection are profitable. "
            f"Leading profit generator is <b>{best_sub}</b> (${best_val:,.2f})."
        )
else:
    cat_metric_text = "No category data"
    cat_body_text = "No records in current selection."

# Build Dynamic Insight 2: Discount Tier Impact
disc_metric_text = (
    f"Discounts >20%: ${deep_disc_profit:,.2f} ({deep_disc_margin:.2f}% Margin) vs. "
    f"<=20%: ${low_disc_profit:,.2f} ({low_disc_margin:.2f}% Margin)"
)
if len(deep_disc_df) > 0:
    disc_body_text = (
        f"Filtered transactions with discounts exceeding 20% total ${deep_disc_sales:,.2f} in sales "
        f"but yield {deep_disc_margin:.2f}% net margin. Higher discounting does not generate sufficient "
        "volume to compensate for severe unit margin erosion."
    )
else:
    disc_body_text = (
        "The current filter selection contains no deep-discount (>20%) transactions, "
        "resulting in healthy overall margin preservation."
    )

# Build Dynamic Insight 3: Geographic Distribution
if not loss_states.empty:
    worst_state_names = ", ".join(loss_states.head(3).index.tolist())
    total_state_loss = loss_states["Profit"].sum()
    geo_metric_text = f"{len(loss_states)} Loss-Making States Totaling ${total_state_loss:,.2f} in Deficits"
    top_loss_details = ", ".join(
        [
            f"<b>{st}</b> (${loss_states.loc[st, 'Profit']:,.2f}, avg discount {loss_states.loc[st, 'Avg_Discount']:.1%})"
            for st in loss_states.head(3).index
        ]
    )
    geo_body_text = (
        f"Profitability drag is localized in key states: {top_loss_details}. "
        "These states exhibit elevated discount rates that erode bottom-line returns."
    )
else:
    best_state = state_profit_summary.index[-1] if not state_profit_summary.empty else "N/A"
    best_state_profit = (
        state_profit_summary.loc[best_state, "Profit"] if not state_profit_summary.empty else 0.0
    )
    geo_metric_text = "All Filtered States Are Profitable"
    geo_body_text = (
        f"Every state in the active filter selection contributes positive net profit. "
        f"Top performing state is <b>{best_state}</b> (${best_state_profit:,.2f})."
    )

# Build Dynamic Insight 4: Core Growth Opportunities
if not top_profit_subcats.empty:
    lead_sub = top_profit_subcats.index[0]
    lead_profit = top_profit_subcats.loc[lead_sub, "Profit"]
    lead_margin = top_profit_subcats.loc[lead_sub, "Margin %"]
    growth_metric_text = f"{lead_sub} Leads with ${lead_profit:,.2f} Profit ({lead_margin:.1f}% Margin)"
    growth_body_text = (
        f"Top sub-categories like <b>{lead_sub}</b> drive high-margin cash flow. "
        "Customer demand in these categories exhibits high price elasticity tolerance."
    )
else:
    growth_metric_text = "No growth data"
    growth_body_text = "No records in current selection."


ins1, ins2 = st.columns(2)

with ins1:
    st.markdown(
        f"""
        <div class="insight-card warning">
            <div class="insight-title">1. Category Margin Dispersion & Loss Drivers</div>
            <div class="insight-metric">{cat_metric_text}</div>
            <div class="insight-body">
                {cat_body_text}
            </div>
            <div class="insight-rec">
                <b>Actionable Recommendation:</b> Re-negotiate vendor terms for persistent loss-makers, introduce minimum price floors, and bundle low-margin items with high-margin technology accessories.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="insight-card warning">
            <div class="insight-title">2. Discount Sensitivity & Margin Degradation</div>
            <div class="insight-metric">{disc_metric_text}</div>
            <div class="insight-body">
                {disc_body_text}
            </div>
            <div class="insight-rec">
                <b>Actionable Recommendation:</b> Enforce a 20% discount governance ceiling for sales reps, requiring regional managerial sign-off for larger promotional allowances.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with ins2:
    st.markdown(
        f"""
        <div class="insight-card {'warning' if not loss_states.empty else ''}">
            <div class="insight-title">3. Geographic Performance & State Deficits</div>
            <div class="insight-metric">{geo_metric_text}</div>
            <div class="insight-body">
                {geo_body_text}
            </div>
            <div class="insight-rec">
                <b>Actionable Recommendation:</b> Audit local pricing authority and freight carrier contracts in underperforming territories to match gross margins achieved in profitable regions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">4. High-Yield Growth & Cash Flow Drivers</div>
            <div class="insight-metric">{growth_metric_text}</div>
            <div class="insight-body">
                {growth_body_text}
            </div>
            <div class="insight-rec">
                <b>Actionable Recommendation:</b> Shift marketing spend and inventory buffer toward high-yield sub-categories with proven price tolerance to maximize EBITDA.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
