from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "sku",
    "product_name",
    "platform",
    "sale_price",
    "item_cost",
    "shipping_cost",
    "other_costs",
    "quantity",
}

if "category" not in df.columns:
    df["category"] = ""

def load_product_data(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)

    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)

    else:
        raise ValueError(
            "Unsupported file type. Please use CSV or Excel."
        )

    # Standardize column names
    df.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        for column in df.columns
    ]

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    return df