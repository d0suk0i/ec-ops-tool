import sys

import argparse

from pathlib import Path

from flags import (
    load_analysis_rules,
    apply_business_flags,
)
from ranking import (
    load_ranking_rules,
    rank_products,
)
from exporter import export_analysis_report
from data_loader import load_product_data
from data_cleaner import clean_and_validate_product_data
from duplicates import handle_duplicates
from profitability import (
    load_platform_fees,
    calculate_profitability,

)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Analyze EC product profitability, "
            "data quality, and product priority."
        )
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        default="input/products.csv",
        help=(
            "CSV or Excel product file to analyze. "
            "Default: input/products.csv"
        ),
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help=(
            "Directory where analysis reports are saved. "
            "Default: output"
        ),
    )

    parser.add_argument(
        "--lang",
        choices=[
            "en",
            "ja",
        ],
        default="en",
        help=(
            "Report language: "
            "en or ja. Default: en"
        ),
    )

    return parser.parse_args()

def main():
    args = parse_arguments()
    print("EC Operations Tool")
    print("------------------")

    input_file = Path(
        args.input_file
    )
    fee_config = Path("config/platform_fees.json")
    rules_config = Path("config/analysis_rules.json")
    ranking_config = Path(
        "config/ranking_rules.json"
    )
    try:
        products = load_product_data(input_file)

        print(f"Loaded {len(products)} product rows.")

        cleaned_products, validation_issues = (
            clean_and_validate_product_data(products)
        )

        final_products, duplicate_issues = (
            handle_duplicates(cleaned_products)
        )

        platform_fees = load_platform_fees(
            fee_config
        )

        analysis = calculate_profitability(
            final_products,
            platform_fees
        )
        analysis_rules = load_analysis_rules(
            rules_config
        )

        analysis = apply_business_flags(
            analysis,
            platform_fees,
            analysis_rules,
            validation_issues,
            duplicate_issues,
        )

        ranking_rules = load_ranking_rules(
            ranking_config
        )

        analysis = rank_products(
            analysis,
            ranking_rules
        )

        print()
        print("Validation complete.")

        if validation_issues.empty:
            print("No validation problems found.")
        else:
            print(
                validation_issues.to_string(
                    index=False
                )
            )

        print()
        print("Duplicate check complete.")

        if duplicate_issues.empty:
            print("No duplicate problems found.")
        else:
            print(
                duplicate_issues.to_string(
                    index=False
                )
            )

        print()
        print("Profitability analysis:")

        print()

        display_columns = [
            "sku",
            "product_name",
            "sale_price",
            "platform_fee",
            "total_cost",
            "profit",
            "margin_pct",
            "roi_pct",
            "break_even_price",
            "priority_score",
            "priority_rank",
            "flags",

        ]

        print(
            analysis[
                display_columns
            ].to_string(index=False)
        )

        output_file = export_analysis_report(
            analysis,
            validation_issues,
            duplicate_issues,
            Path(args.output_dir),
            language=args.lang,
        )

        print()
        print("Excel report created:")
        print(output_file)

    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()