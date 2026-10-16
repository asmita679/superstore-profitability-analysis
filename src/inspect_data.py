import sys
from pathlib import Path
import pandas as pd


def resolve_dataset_path() -> Path:
    """
    Resolve the project root independently of the terminal's current directory
    and verify the dataset path exists.
    """
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    expected_dir = project_root / "data"

    # Candidate file locations in order of preference
    candidates = [
        expected_dir / "Sample - Superstore.csv",
        expected_dir / "SampleSuperstore.csv",
        Path("data") / "Sample - Superstore.csv",
        Path("data") / "SampleSuperstore.csv",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    expected_path = expected_dir / "Sample - Superstore.csv"
    sys.stderr.write(
        "\n" + "=" * 60 + "\n"
        "ERROR: Superstore CSV dataset was not found!\n"
        f"Expected file location: {expected_path}\n\n"
        "Instructions to fix:\n"
        f"1. Place 'Sample - Superstore.csv' inside directory:\n   {expected_dir}\n"
        "2. Ensure the filename matches 'Sample - Superstore.csv' or 'SampleSuperstore.csv'.\n"
        "=" * 60 + "\n"
    )
    sys.exit(1)


def load_dataset_safely(file_path: Path) -> pd.DataFrame:
    """
    Load CSV trying common encodings safely without silent data corruption.
    """
    encodings_to_try = ["utf-8", "windows-1252", "latin1", "iso-8859-1"]
    last_error = None

    for enc in encodings_to_try:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            print(f"[OK] Successfully loaded '{file_path.name}' using encoding: {enc}")
            return df
        except UnicodeDecodeError as err:
            last_error = err
            continue
        except Exception as err:
            sys.stderr.write(f"ERROR: Failed reading '{file_path}' ({type(err).__name__}): {err}\n")
            sys.exit(1)

    sys.stderr.write(
        f"ERROR: Could not decode '{file_path}' using supported encodings ({encodings_to_try}).\n"
        f"Last error: {last_error}\n"
    )
    sys.exit(1)


def validate_and_inspect(df: pd.DataFrame, file_path: Path) -> None:
    """
    Validate data integrity and display inspection metrics:
    - First 5 rows
    - Dimensions and column names
    - Data types
    - Missing-value counts
    - Duplicate-row counts
    """
    if df.empty:
        sys.stderr.write(f"ERROR: Dataset at '{file_path}' is empty.\n")
        sys.exit(1)

    expected_columns = ["Order ID", "Sales", "Profit", "Category", "Sub-Category"]
    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        sys.stderr.write(f"ERROR: Dataset is missing required columns: {missing_cols}\n")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("           SUPERSTORE DATA INSPECTION REPORT")
    print("=" * 60)
    print(f"Verified File Path: {file_path}")

    print("\n--- First 5 rows ---")
    print(df.head())

    print("\n--- Dataset dimensions ---")
    print(f"Rows: {df.shape[0]:,}, Columns: {df.shape[1]}")

    print("\n--- Column names ---")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")

    print("\n--- Data types ---")
    print(df.dtypes)

    print("\n--- Missing values count ---")
    null_counts = df.isnull().sum()
    print(null_counts)
    print(f"\nTotal missing values across dataset: {null_counts.sum()}")

    print("\n--- Duplicate rows count ---")
    duplicate_count = df.duplicated().sum()
    print(f"Total duplicate rows: {duplicate_count}")
    print("=" * 60 + "\n")


def main():
    dataset_path = resolve_dataset_path()
    df = load_dataset_safely(dataset_path)
    validate_and_inspect(df, dataset_path)


if __name__ == "__main__":
    main()