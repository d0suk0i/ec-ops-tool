import pandas as pd


TEXT_COLUMNS = [
    "sku",
    "product_name",
    "platform",
]

NUMERIC_COLUMNS = [
    "sale_price",
    "item_cost",
    "shipping_cost",
    "other_costs",
    "quantity",
]


def clean_and_validate_product_data(df):
    cleaned = df.copy()

    issues = []

    # Clean text fields
    for column in TEXT_COLUMNS:
        cleaned[column] = (
            cleaned[column]
            .astype("string")
            .str.strip()
        )

    # Convert numeric fields
    for column in NUMERIC_COLUMNS:
        cleaned[column] = pd.to_numeric(
            cleaned[column],
            errors="coerce"
        )

    # Check each row
    for index, row in cleaned.iterrows():

        # +2 because CSV row 1 is the header
        csv_row = index + 2

        sku = row["sku"]

        # Missing text fields
        for column in TEXT_COLUMNS:
            if pd.isna(row[column]) or row[column] == "":
                issues.append({
                    "row": csv_row,
                    "sku": sku,
                    "issue": f"Missing {column}"
                })

        # Missing or invalid numeric fields
        for column in NUMERIC_COLUMNS:
            if pd.isna(row[column]):
                issues.append({
                    "row": csv_row,
                    "sku": sku,
                    "issue": f"Missing or invalid {column}"
                })

        # Negative financial values
        for column in [
            "sale_price",
            "item_cost",
            "shipping_cost",
            "other_costs",
        ]:
            if pd.notna(row[column]) and row[column] < 0:
                issues.append({
                    "row": csv_row,
                    "sku": sku,
                    "issue": f"{column} cannot be negative"
                })

        # Quantity must be greater than zero
        if pd.notna(row["quantity"]) and row["quantity"] <= 0:
            issues.append({
                "row": csv_row,
                "sku": sku,
                "issue": "quantity must be greater than zero"
            })
    issues_df = pd.DataFrame(issues)

    return cleaned, issues_df