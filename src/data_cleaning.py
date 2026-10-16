import sys
from pathlib import Path
import pandas as pd

# Allow importing from src
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from inspect_data import resolve_dataset_path, load_dataset_safely


def clean_and_transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and enriches the Superstore dataset:
    - Parses date columns
    - Derives calendar and operational metrics (Year, Month, Shipping Days)
    - Computes Profit Margin
    - Categorizes Discount levels into actionable analytical bands
    """
    # Create copy to prevent mutating the original DataFrame
    df_clean = df.copy()

    # 1. Parse date columns
    df_clean["Order Date"] = pd.to_datetime(df_clean["Order Date"], format="mixed")
    df_clean["Ship Date"] = pd.to_datetime(df_clean["Ship Date"], format="mixed")

    # 2. Derive temporal fields
    df_clean["Order Year"] = df_clean["Order Date"].dt.year
    df_clean["Order Month"] = df_clean["Order Date"].dt.to_period("M").astype(str)
    df_clean["Order Month Num"] = df_clean["Order Date"].dt.month
    df_clean["Order Month Name"] = df_clean["Order Date"].dt.strftime("%b")
    df_clean["Shipping Days"] = (df_clean["Ship Date"] - df_clean["Order Date"]).dt.days

    # Validation: Shipping Days should not be negative
    if (df_clean["Shipping Days"] < 0).any():
        raise ValueError("Detected negative shipping days in dataset.")

    # 3. Calculate unit / transaction profit margin %
    # Avoid division by zero by replacing zero sales with NaN for margin calculation
    df_clean["Profit Margin %"] = (df_clean["Profit"] / df_clean["Sales"]) * 100

    # 4. Create standard discount bands for sensitivity analysis
    bins = [-0.001, 0.0, 0.20, 0.40, 1.0]
    labels = ["0% (No Discount)", "1-20% (Low)", "21-40% (Moderate)", ">40% (Deep)"]
    df_clean["Discount Band"] = pd.cut(df_clean["Discount"], bins=bins, labels=labels)

    return df_clean


def compute_kpis(df: pd.DataFrame) -> dict:
    """Compute core executive KPIs."""
    total_sales = float(df["Sales"].sum())
    total_profit = float(df["Profit"].sum())
    order_count = int(df["Order ID"].nunique())
    total_quantity = int(df["Quantity"].sum())
    profit_margin = (total_profit / total_sales) * 100 if total_sales else 0.0

    return {
        "Total Sales ($)": total_sales,
        "Total Profit ($)": total_profit,
        "Total Unique Orders": order_count,
        "Total Quantity Sold": total_quantity,
        "Overall Profit Margin (%)": profit_margin,
    }


def print_exploratory_summary(df: pd.DataFrame) -> None:
    """Print structured analytical summaries across key dimensions."""
    kpis = compute_kpis(df)

    print("\n" + "=" * 65)
    print("           SUPERSTORE EXECUTIVE KPI SUMMARY")
    print("=" * 65)
    for kpi, val in kpis.items():
        if "($)" in kpi:
            print(f"  {kpi:<28}: ${val:,.2f}")
        elif "(%)" in kpi:
            print(f"  {kpi:<28}: {val:.2f}%")
        else:
            print(f"  {kpi:<28}: {val:,}")

    print("\n" + "-" * 65)
    print("1. CATEGORY PROFITABILITY BREAKDOWN")
    print("-" * 65)
    cat_summary = df.groupby("Category").agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Quantity=("Quantity", "sum")
    )
    cat_summary["Margin %"] = (cat_summary["Profit"] / cat_summary["Sales"]) * 100
    # Format summary cleanly for terminal display
    fmt_summary = cat_summary.copy()
    fmt_summary["Sales"] = fmt_summary["Sales"].map("${:,.2f}".format)
    fmt_summary["Profit"] = fmt_summary["Profit"].map("${:,.2f}".format)
    fmt_summary["Quantity"] = fmt_summary["Quantity"].map("{:,}".format)
    fmt_summary["Margin %"] = fmt_summary["Margin %"].map("{:.2f}%".format)
    print(fmt_summary)

    print("\n" + "-" * 65)
    print("2. SUB-CATEGORY TOP & BOTTOM PERFORMERS")
    print("-" * 65)
    sub_summary = df.groupby("Sub-Category").agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum")
    )
    sub_summary["Margin %"] = (sub_summary["Profit"] / sub_summary["Sales"]) * 100
    sub_summary = sub_summary.sort_values("Profit", ascending=False)
    print("Top 3 Profitable Sub-Categories:")
    print(sub_summary.head(3))
    print("\nBottom 3 Loss-Making Sub-Categories:")
    print(sub_summary.tail(3))

    print("\n" + "-" * 65)
    print("3. REGIONAL PROFITABILITY & PROBLEM STATES")
    print("-" * 65)
    reg_summary = df.groupby("Region").agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Avg_Discount=("Discount", "mean")
    )
    reg_summary["Margin %"] = (reg_summary["Profit"] / reg_summary["Sales"]) * 100
    print(reg_summary)

    print("\nBottom 5 States with Largest Losses:")
    state_summary = df.groupby("State").agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Avg_Discount=("Discount", "mean")
    )
    state_summary["Margin %"] = (state_summary["Profit"] / state_summary["Sales"]) * 100
    print(state_summary.sort_values("Profit").head(5))

    print("\n" + "-" * 65)
    print("4. DISCOUNT BAND PROFITABILITY (No causation assumed)")
    print("-" * 65)
    disc_summary = df.groupby("Discount Band", observed=False).agg(
        Orders=("Order ID", "nunique"),
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum"),
        Avg_Profit_Per_Order=("Profit", "mean")
    )
    disc_summary["Margin %"] = (disc_summary["Total_Profit"] / disc_summary["Total_Sales"]) * 100
    print(disc_summary)
    print("=" * 65 + "\n")


def main():
    raw_path = resolve_dataset_path()
    raw_df = load_dataset_safely(raw_path)
    clean_df = clean_and_transform_data(raw_df)

    output_path = PROJECT_ROOT / "data" / "cleaned_superstore.csv"
    clean_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[OK] Cleaned dataset saved to: {output_path}")

    print_exploratory_summary(clean_df)


if __name__ == "__main__":
    main()
