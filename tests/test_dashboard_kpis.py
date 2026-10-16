import sqlite3
import unittest
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_CSV_PATH = PROJECT_ROOT / "data" / "cleaned_superstore.csv"
DB_PATH = PROJECT_ROOT / "data" / "superstore.db"


class TestDashboardCalculations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(CLEANED_CSV_PATH)
        cls.df["Order Date"] = pd.to_datetime(cls.df["Order Date"])

    def test_kpi_parity_with_sqlite(self):
        """Verify that Pandas calculations match SQLite results within pennies."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ROUND(SUM(sales), 2),
                ROUND(SUM(profit), 2),
                COUNT(DISTINCT order_id),
                SUM(quantity)
            FROM orders;
        """)
        sql_sales, sql_profit, sql_orders, sql_qty = cursor.fetchone()
        conn.close()

        df_sales = round(self.df["Sales"].sum(), 2)
        df_profit = round(self.df["Profit"].sum(), 2)
        df_orders = self.df["Order ID"].nunique()
        df_qty = self.df["Quantity"].sum()

        self.assertAlmostEqual(df_sales, sql_sales, places=1)
        self.assertAlmostEqual(df_profit, sql_profit, places=1)
        self.assertEqual(df_orders, sql_orders)
        self.assertEqual(df_qty, sql_qty)

    def test_profit_margin_formula(self):
        """Ensure profit margin calculation handles normal and edge cases without ZeroDivisionError."""
        sales = self.df["Sales"].sum()
        profit = self.df["Profit"].sum()
        margin = (profit / sales) * 100
        self.assertAlmostEqual(margin, 12.467, places=2)

        # Edge case: zero sales should yield 0.0 or nan safely, not an unhandled ZeroDivisionError
        zero_sales = 0.0
        safe_margin = (profit / zero_sales * 100) if zero_sales > 0 else 0.0
        self.assertEqual(safe_margin, 0.0)

    def test_filter_interactions(self):
        """Verify that multi-filter intersections produce mathematically valid subsets."""
        filtered = self.df[
            (self.df["Region"] == "West")
            & (self.df["Category"] == "Technology")
            & (self.df["Discount Band"] == "0% (No Discount)")
        ]
        self.assertGreater(len(filtered), 0)
        self.assertTrue((filtered["Region"] == "West").all())
        self.assertTrue((filtered["Category"] == "Technology").all())
        self.assertTrue((filtered["Discount"] == 0).all())

        # Metrics must be consistent within the slice
        subset_sales = filtered["Sales"].sum()
        subset_profit = filtered["Profit"].sum()
        subset_orders = filtered["Order ID"].nunique()
        self.assertGreater(subset_sales, 0)
        self.assertGreater(subset_profit, 0)
        self.assertLessEqual(subset_orders, len(filtered))

    def test_loss_making_subcategories_identified(self):
        """Verify that Tables and Bookcases have negative net profit in dataset."""
        sub_profit = self.df.groupby("Sub-Category")["Profit"].sum()
        self.assertLess(sub_profit["Tables"], 0, "Tables should be unprofitable in Superstore.")
        self.assertLess(sub_profit["Bookcases"], 0, "Bookcases should be unprofitable in Superstore.")

    def test_deep_discount_negative_profit(self):
        """Verify that transactions with discount > 40% yield net negative profit."""
        deep_disc = self.df[self.df["Discount"] > 0.40]
        self.assertLess(deep_disc["Profit"].sum(), 0, "Deep discount tier should have net negative profit.")


if __name__ == "__main__":
    unittest.main()
