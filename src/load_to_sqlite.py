import sqlite3
import sys
from pathlib import Path
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "superstore.db"
CLEANED_CSV_PATH = DATA_DIR / "cleaned_superstore.csv"


def get_column_mapping() -> dict:
    """Map CSV column names to clean, SQL-friendly snake_case column names."""
    return {
        "Row ID": "row_id",
        "Order ID": "order_id",
        "Order Date": "order_date",
        "Ship Date": "ship_date",
        "Ship Mode": "ship_mode",
        "Customer ID": "customer_id",
        "Customer Name": "customer_name",
        "Segment": "segment",
        "Country": "country",
        "City": "city",
        "State": "state",
        "Postal Code": "postal_code",
        "Region": "region",
        "Product ID": "product_id",
        "Category": "category",
        "Sub-Category": "sub_category",
        "Product Name": "product_name",
        "Sales": "sales",
        "Quantity": "quantity",
        "Discount": "discount",
        "Profit": "profit",
        "Order Year": "order_year",
        "Order Month": "order_month",
        "Order Month Num": "order_month_num",
        "Order Month Name": "order_month_name",
        "Shipping Days": "shipping_days",
        "Profit Margin %": "profit_margin_pct",
        "Discount Band": "discount_band",
    }


def populate_sqlite_database() -> None:
    """Load cleaned Superstore data into SQLite using python's built-in sqlite3."""
    if not CLEANED_CSV_PATH.exists():
        sys.stderr.write(f"ERROR: Cleaned CSV not found at {CLEANED_CSV_PATH}. Run data_cleaning.py first.\n")
        sys.exit(1)

    print(f"Reading cleaned dataset from: {CLEANED_CSV_PATH}")
    df = pd.read_csv(CLEANED_CSV_PATH)

    # Rename columns to snake_case
    col_map = get_column_mapping()
    df_sql = df.rename(columns=col_map)

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Writing {len(df_sql)} records to SQLite database: {DB_PATH}")
    # Write to table 'orders'
    df_sql.to_sql("orders", conn, if_exists="replace", index=False)

    # Create indexes for optimal query performance
    print("Creating database indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);",
        "CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);",
        "CREATE INDEX IF NOT EXISTS idx_orders_category ON orders(category);",
        "CREATE INDEX IF NOT EXISTS idx_orders_sub_category ON orders(sub_category);",
        "CREATE INDEX IF NOT EXISTS idx_orders_region ON orders(region);",
        "CREATE INDEX IF NOT EXISTS idx_orders_state ON orders(state);",
        "CREATE INDEX IF NOT EXISTS idx_orders_discount ON orders(discount);",
    ]
    for idx_sql in indexes:
        cursor.execute(idx_sql)

    conn.commit()

    # Verification query
    cursor.execute("SELECT COUNT(*) FROM orders;")
    count = cursor.fetchone()[0]
    cursor.execute("SELECT ROUND(SUM(sales), 2), ROUND(SUM(profit), 2) FROM orders;")
    sales, profit = cursor.fetchone()

    conn.close()

    print("\n" + "=" * 50)
    print("      SQLITE DATABASE CREATED SUCCESSFULLY")
    print("=" * 50)
    print(f"Database File: {DB_PATH}")
    print(f"Total Rows In 'orders' Table: {count:,}")
    print(f"Verified Total Sales in SQLite: ${sales:,.2f}")
    print(f"Verified Total Profit in SQLite: ${profit:,.2f}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    populate_sqlite_database()
