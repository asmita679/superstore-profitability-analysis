import sqlite3
import unittest
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"


class TestAnalyticsPipeline(unittest.TestCase):
    def test_cleaned_dataset_integrity(self):
        csv_path = DATA_DIR / "cleaned_superstore.csv"
        self.assertTrue(csv_path.exists(), "Cleaned dataset does not exist.")
        df = pd.read_csv(csv_path)

        self.assertEqual(len(df), 9994, f"Expected 9,994 rows, found {len(df)}")
        self.assertIn("Shipping Days", df.columns)
        self.assertIn("Profit Margin %", df.columns)
        self.assertIn("Discount Band", df.columns)

        # Verify key baseline financial aggregates
        total_sales = round(df["Sales"].sum(), 2)
        total_profit = round(df["Profit"].sum(), 2)
        self.assertAlmostEqual(total_sales, 2297200.86, places=1)
        self.assertAlmostEqual(total_profit, 286397.02, places=1)

    def test_sqlite_database_tables_and_indexes(self):
        db_path = DATA_DIR / "superstore.db"
        self.assertTrue(db_path.exists(), "SQLite database does not exist.")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check row count
        cursor.execute("SELECT COUNT(*) FROM orders;")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 9994)

        # Check total metrics in SQLite
        cursor.execute("SELECT ROUND(SUM(sales), 2), ROUND(SUM(profit), 2) FROM orders;")
        sales, profit = cursor.fetchone()
        self.assertAlmostEqual(sales, 2297200.86, places=1)
        self.assertAlmostEqual(profit, 286397.02, places=1)

        conn.close()

    def test_sql_analysis_queries(self):
        db_path = DATA_DIR / "superstore.db"
        sql_path = PROJECT_ROOT / "sql" / "analysis_queries.sql"
        self.assertTrue(sql_path.exists(), "SQL queries file missing.")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with open(sql_path, "r", encoding="utf-8") as f:
            content = f.read()

        statements = [s.strip() for s in content.split(";") if s.strip()]
        self.assertEqual(len(statements), 10, f"Expected 10 SQL statements, found {len(statements)}")

        for i, stmt in enumerate(statements, 1):
            cursor.execute(stmt)
            rows = cursor.fetchall()
            self.assertGreater(len(rows), 0, f"Statement {i} returned no rows.")

        conn.close()


if __name__ == "__main__":
    unittest.main()
