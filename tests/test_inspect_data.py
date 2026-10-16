import sys
import unittest
from pathlib import Path

# Add project root and src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from inspect_data import resolve_dataset_path, load_dataset_safely


class TestInspectData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_path = resolve_dataset_path()
        cls.df = load_dataset_safely(cls.file_path)

    def test_file_exists(self):
        self.assertTrue(self.file_path.exists(), "Dataset file does not exist.")
        self.assertTrue(self.file_path.is_file(), "Dataset path is not a file.")

    def test_dataset_dimensions(self):
        # Sample Superstore standard dataset: 9994 rows, 21 columns
        self.assertEqual(self.df.shape, (9994, 21), f"Unexpected shape: {self.df.shape}")

    def test_required_columns_present(self):
        expected_columns = [
            "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
            "Customer ID", "Customer Name", "Segment", "Country", "City",
            "State", "Postal Code", "Region", "Product ID", "Category",
            "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit"
        ]
        for col in expected_columns:
            self.assertIn(col, self.df.columns, f"Missing required column: {col}")

    def test_no_null_values(self):
        total_missing = self.df.isnull().sum().sum()
        self.assertEqual(total_missing, 0, f"Expected 0 missing values, found {total_missing}")

    def test_duplicate_rows(self):
        duplicate_count = self.df.duplicated().sum()
        self.assertEqual(duplicate_count, 0, f"Expected 0 duplicate rows, found {duplicate_count}")

    def test_metrics_range(self):
        self.assertTrue((self.df["Sales"] >= 0).all(), "Negative sales values found.")
        self.assertTrue((self.df["Quantity"] > 0).all(), "Non-positive quantity values found.")
        self.assertTrue(((self.df["Discount"] >= 0) & (self.df["Discount"] <= 1.0)).all(),
                        "Discount values out of bounds [0, 1].")


if __name__ == "__main__":
    unittest.main()
