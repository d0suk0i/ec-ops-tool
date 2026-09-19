import pandas as pd


def handle_duplicates(df):
    working = df.copy()

    duplicate_issues = []

    # Find completely identical rows
    exact_duplicates = working.duplicated(
        keep="first"
    )

    for index, row in working[exact_duplicates].iterrows():
        duplicate_issues.append({
            "row": index + 2,
            "sku": row["sku"],
            "issue": "Exact duplicate row removed"
        })

    # Remove only completely identical duplicate rows
    cleaned = working.drop_duplicates(
        keep="first"
    ).copy()

    # Look for SKUs that still occur more than once.
    # These are NOT automatically removed because
    # something about the rows must be different.
    duplicate_skus = cleaned[
        cleaned.duplicated(
            subset=["sku"],
            keep=False
        )
    ]

    for index, row in duplicate_skus.iterrows():
        duplicate_issues.append({
            "row": index + 2,
            "sku": row["sku"],
            "issue": "Duplicate SKU with conflicting data"
        })

    duplicate_report = pd.DataFrame(
        duplicate_issues
    )

    return cleaned, duplicate_report