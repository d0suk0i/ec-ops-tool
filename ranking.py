import json
from pathlib import Path

import pandas as pd


def load_ranking_rules(config_path):
    path = Path(config_path)

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def rank_products(df, rules):
    results = df.copy()

    profit_weight = rules["profit_weight"]
    margin_weight = rules["margin_weight"]
    roi_weight = rules["roi_weight"]

    # Create percentile scores from 0 to 100.
    # Higher values are better.
    results["profit_score"] = (
        results["profit"]
        .astype("Float64")
        .rank(pct=True)
        * 100
    )

    results["margin_score"] = (
        results["margin_pct"]
        .astype("Float64")
        .rank(pct=True)
        * 100
    )

    results["roi_score"] = (
        results["roi_pct"]
        .astype("Float64")
        .rank(pct=True)
        * 100
    )

    results["priority_score"] = (
        results["profit_score"] * profit_weight
        + results["margin_score"] * margin_weight
        + results["roi_score"] * roi_weight
    )

    # Products requiring review should not receive a usable ranking.
    review_mask = results["flags"].str.contains(
        "REVIEW REQUIRED",
        na=False
    )

    results.loc[
        review_mask,
        "priority_score"
    ] = pd.NA

    results["priority_score"] = (
        results["priority_score"]
        .round(2)
    )

    # Rank valid products.
    results["priority_rank"] = (
        results["priority_score"]
        .rank(
            ascending=False,
            method="min"
        )
        .astype("Int64")
    )

    # Put usable products first and review items last.
    results = results.sort_values(
        by="priority_score",
        ascending=False,
        na_position="last"
    )

    return results