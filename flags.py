import json
from pathlib import Path

import pandas as pd


def load_analysis_rules(config_path):
    path = Path(config_path)

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def apply_business_flags(
    df,
    platform_fees,
    rules,
    validation_issues=None,
    duplicate_issues=None,
):
    results = df.copy()

    low_margin_threshold = rules["low_margin_pct"]
    high_roi_threshold = rules["high_roi_pct"]

    # SKUs with validation problems
    invalid_skus = set()

    if (
        validation_issues is not None
        and not validation_issues.empty
    ):
        invalid_skus = set(
            validation_issues["sku"]
            .dropna()
            .astype(str)
        )

    # SKUs with conflicting duplicate records
    conflicting_duplicate_skus = set()

    if (
        duplicate_issues is not None
        and not duplicate_issues.empty
    ):
        conflict_rows = duplicate_issues[
            duplicate_issues["issue"]
            == "Duplicate SKU with conflicting data"
        ]

        conflicting_duplicate_skus = set(
            conflict_rows["sku"]
            .dropna()
            .astype(str)
        )

    flags_column = []

    for _, row in results.iterrows():
        flags = []

        sku = str(row["sku"])

        platform = str(
            row["platform"]
        ).strip().lower()

        required_values = [
            row["sale_price"],
            row["item_cost"],
            row["shipping_cost"],
            row["other_costs"],
            row["quantity"],
        ]

        # Missing values
        if any(
            pd.isna(value)
            for value in required_values
        ):
            flags.append(
                "MISSING DATA"
            )

        # Any validation failure
        if sku in invalid_skus:
            flags.append(
                "INVALID DATA"
            )

        # Conflicting duplicate SKU
        if sku in conflicting_duplicate_skus:
            flags.append(
                "CONFLICTING DUPLICATE"
            )

        # Marketplace problems
        if platform not in platform_fees:
            flags.append(
                "UNKNOWN PLATFORM"
            )

        elif not platform_fees[
            platform
        ]["enabled"]:
            flags.append(
                "PLATFORM DISABLED"
            )

        platform_config = platform_fees.get(
            platform
        )

        if (
                platform_config is not None
                and platform_config["enabled"]
                and platform_config["fee_model"]
                == "category_percentage"
        ):
            category = str(
                row.get("category", "")
            ).strip().lower()

            if (
                    not category
                    or category
                    not in platform_config["categories"]
            ):
                flags.append(
                    "UNKNOWN CATEGORY"
                )

        platform_config = platform_fees.get(
            platform
        )

        if (
                platform_config is not None
                and platform_config["enabled"]
                and platform_config["fee_model"]
                == "category_percentage"
        ):
            category = str(
                row.get("category", "")
            ).strip().lower()

            if (
                    not category
                    or category
                    not in platform_config["categories"]
            ):
                flags.append(
                    "UNKNOWN CATEGORY"
                )

        profit = row["profit"]
        margin = row["margin_pct"]
        roi = row["roi_pct"]

        if pd.notna(profit):

            if profit < 0:
                flags.append(
                    "LOSS"
                )

            elif profit == 0:
                flags.append(
                    "BREAK EVEN"
                )

            else:
                flags.append(
                    "PROFITABLE"
                )

            if (
                profit > 0
                and pd.notna(margin)
                and margin
                < low_margin_threshold
            ):
                flags.append(
                    "LOW MARGIN"
                )

            if (
                profit > 0
                and pd.notna(roi)
                and roi
                >= high_roi_threshold
            ):
                flags.append(
                    "HIGH ROI"
                )

        # Only serious integrity/analysis issues
        # require manual review.
        review_flags = {
            "MISSING DATA",
            "INVALID DATA",
            "CONFLICTING DUPLICATE",
            "UNKNOWN PLATFORM",
            "PLATFORM DISABLED",
            "LOSS",
            "UNKNOWN CATEGORY",
        }

        if any(
            flag in review_flags
            for flag in flags
        ):
            flags.append(
                "REVIEW REQUIRED"
            )

        flags_column.append(
            " | ".join(flags)
        )

    results["flags"] = flags_column

    return results