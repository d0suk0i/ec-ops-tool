import pandas as pd

from ebay_fees import (
    calculate_ebay_fee_jpy,
    calculate_ebay_break_even_price_jpy,
)
from ranking import rank_products
from data_cleaner import clean_and_validate_product_data
from duplicates import handle_duplicates
from profitability import calculate_profitability
from flags import apply_business_flags


TEST_PLATFORM_FEES = {
    "mercari": {
        "display_name": "Mercari",
        "fee_model": "flat_percentage",
        "fee_rate": 0.10,
        "enabled": True,
    }
}

TEST_RULES = {
    "low_margin_pct": 15,
    "high_roi_pct": 50,
}

TEST_RANKING_RULES = {
    "profit_weight": 0.40,
    "margin_weight": 0.30,
    "roi_weight": 0.30,
}

def make_product_dataframe():
    return pd.DataFrame([
        {
            "sku": "TEST001",
            "product_name": "Test Product",
            "platform": "Mercari",
            "sale_price": 5000,
            "item_cost": 2000,
            "shipping_cost": 500,
            "other_costs": 0,
            "quantity": 1,
        }
    ])


def test_profit_calculation():
    df = make_product_dataframe()

    result = calculate_profitability(
        df,
        TEST_PLATFORM_FEES
    )

    row = result.iloc[0]

    assert row["platform_fee"] == 500
    assert row["total_cost"] == 3000
    assert row["profit"] == 2000
    assert row["margin_pct"] == 40.0
    assert row["roi_pct"] == 80.0


def test_break_even_price():
    df = make_product_dataframe()

    result = calculate_profitability(
        df,
        TEST_PLATFORM_FEES
    )

    row = result.iloc[0]

    assert round(
        float(row["break_even_price"]),
        2
    ) == 2777.78


def test_missing_cost_is_detected():
    df = make_product_dataframe()

    df.loc[0, "item_cost"] = None

    _, issues = clean_and_validate_product_data(
        df
    )

    assert not issues.empty

    assert (
        "Missing or invalid item_cost"
        in issues["issue"].values
    )


def test_exact_duplicate_removed():
    original = make_product_dataframe()

    df = pd.concat(
        [original, original],
        ignore_index=True
    )

    cleaned, duplicate_issues = handle_duplicates(
        df
    )

    assert len(cleaned) == 1

    assert (
        "Exact duplicate row removed"
        in duplicate_issues["issue"].values
    )


def test_loss_is_flagged():
    df = make_product_dataframe()

    df.loc[0, "sale_price"] = 2000
    df.loc[0, "item_cost"] = 2500

    analysis = calculate_profitability(
        df,
        TEST_PLATFORM_FEES
    )

    flagged = apply_business_flags(
        analysis,
        TEST_PLATFORM_FEES,
        TEST_RULES,
    )

    flags = flagged.iloc[0]["flags"]

    assert "LOSS" in flags
    assert "REVIEW REQUIRED" in flags

def test_negative_quantity_is_invalid():
        df = make_product_dataframe()

        df.loc[0, "quantity"] = -1

        cleaned, validation_issues = (
            clean_and_validate_product_data(df)
        )

        analysis = calculate_profitability(
            cleaned,
            TEST_PLATFORM_FEES
        )

        flagged = apply_business_flags(
            analysis,
            TEST_PLATFORM_FEES,
            TEST_RULES,
            validation_issues,
        )

        flags = flagged.iloc[0]["flags"]

        assert "INVALID DATA" in flags
        assert "REVIEW REQUIRED" in flags
        assert pd.isna(flagged.iloc[0]["profit"])

def test_unknown_platform_is_flagged():
        df = make_product_dataframe()

        df.loc[0, "platform"] = "Unknown Marketplace"

        analysis = calculate_profitability(
            df,
            TEST_PLATFORM_FEES
        )

        flagged = apply_business_flags(
            analysis,
            TEST_PLATFORM_FEES,
            TEST_RULES,
        )

        flags = flagged.iloc[0]["flags"]

        assert "UNKNOWN PLATFORM" in flags
        assert "REVIEW REQUIRED" in flags
        assert pd.isna(flagged.iloc[0]["profit"])

def test_disabled_platform_is_flagged():
    disabled_fees = {
        "mercari": {
            "display_name": "Mercari",
            "fee_model": "flat_percentage",
            "fee_rate": 0.10,
            "enabled": False,
        }
    }

    df = make_product_dataframe()

    analysis = calculate_profitability(
            df,
            disabled_fees
        )

    flagged = apply_business_flags(
            analysis,
            disabled_fees,
            TEST_RULES,
        )

    flags = flagged.iloc[0]["flags"]

    assert "PLATFORM DISABLED" in flags
    assert "REVIEW REQUIRED" in flags
    assert pd.isna(flagged.iloc[0]["profit"])

def test_conflicting_duplicate_requires_review():
        first = make_product_dataframe()

        second = make_product_dataframe()
        second.loc[0, "sale_price"] = 6500

        df = pd.concat(
            [first, second],
            ignore_index=True
        )

        cleaned, duplicate_issues = handle_duplicates(
            df
        )

        analysis = calculate_profitability(
            cleaned,
            TEST_PLATFORM_FEES
        )

        flagged = apply_business_flags(
            analysis,
            TEST_PLATFORM_FEES,
            TEST_RULES,
            duplicate_issues=duplicate_issues,
        )

        assert all(
            "CONFLICTING DUPLICATE" in flags
            for flags in flagged["flags"]
        )

        assert all(
            "REVIEW REQUIRED" in flags
            for flags in flagged["flags"]
        )

def test_review_required_product_is_not_ranked():
        df = make_product_dataframe()

        df.loc[0, "platform"] = "Unknown Marketplace"

        analysis = calculate_profitability(
            df,
            TEST_PLATFORM_FEES
        )

        flagged = apply_business_flags(
            analysis,
            TEST_PLATFORM_FEES,
            TEST_RULES,
        )

        ranked = rank_products(
            flagged,
            TEST_RANKING_RULES
        )

        row = ranked.iloc[0]

        assert pd.isna(row["priority_score"])
        assert pd.isna(row["priority_rank"])

def test_yahoo_flea_market_fee():
    fees = {
        "yahoo! flea market": {
            "display_name": "Yahoo! Flea Market",
            "fee_model": "flat_percentage",
            "fee_rate": 0.05,
            "enabled": True,
        }
    }

    df = make_product_dataframe()
    df.loc[0, "platform"] = "Yahoo! Flea Market"
    df.loc[0, "sale_price"] = 5000

    result = calculate_profitability(
        df,
        fees
    )

    assert result.iloc[0]["platform_fee"] == 250


def test_rakuma_tiered_fee():
    fees = {
        "rakuma": {
            "display_name": "Rakuma",
            "fee_model": "tiered_percentage",
            "current_fee_rate": 0.10,
            "allowed_fee_rates": [
                0.10,
                0.09,
                0.08,
                0.07,
                0.06,
                0.045,
            ],
            "enabled": True,
        }
    }

    df = make_product_dataframe()
    df.loc[0, "platform"] = "Rakuma"
    df.loc[0, "sale_price"] = 5000

    result = calculate_profitability(
        df,
        fees
    )

    assert result.iloc[0]["platform_fee"] == 500

def test_amazon_electronics_fee():
    fees = {
        "amazon japan": {
            "display_name": "Amazon Japan",
            "fee_model": "category_percentage",
            "default_category": "consumer electronics",
            "extra_rate": 0.0,
            "enabled": True,
            "categories": {
                "consumer electronics": {
                    "minimum_fee": 30,
                    "tiers": [
                        {
                            "max_price": 750,
                            "fee_rate": 0.05,
                        },
                        {
                            "max_price": None,
                            "fee_rate": 0.084,
                        },
                    ],
                }
            },
        }
    }

    df = make_product_dataframe()

    df.loc[0, "platform"] = "Amazon Japan"
    df.loc[0, "category"] = "Consumer Electronics"
    df.loc[0, "sale_price"] = 5000

    result = calculate_profitability(
        df,
        fees
    )

    assert result.iloc[0]["platform_fee"] == 420

def test_amazon_minimum_fee():
    fees = {
        "amazon japan": {
            "display_name": "Amazon Japan",
            "fee_model": "category_percentage",
            "default_category": "consumer electronics",
            "extra_rate": 0.0,
            "enabled": True,
            "categories": {
                "consumer electronics": {
                    "minimum_fee": 30,
                    "tiers": [
                        {
                            "max_price": 750,
                            "fee_rate": 0.05,
                        },
                        {
                            "max_price": None,
                            "fee_rate": 0.084,
                        },
                    ],
                }
            },
        }
    }

    df = make_product_dataframe()

    df.loc[0, "platform"] = "Amazon Japan"
    df.loc[0, "category"] = "Consumer Electronics"
    df.loc[0, "sale_price"] = 400

    result = calculate_profitability(
        df,
        fees
    )

    assert result.iloc[0]["platform_fee"] == 30

    def test_amazon_electronics_fee():
        fees = {
            "amazon japan": {
                "display_name": "Amazon Japan",
                "fee_model": "category_percentage",
                "default_category": "consumer electronics",
                "extra_rate": 0.0,
                "enabled": True,
                "categories": {
                    "consumer electronics": {
                        "minimum_fee": 30,
                        "tiers": [
                            {
                                "max_price": 750,
                                "fee_rate": 0.05,
                            },
                            {
                                "max_price": None,
                                "fee_rate": 0.084,
                            },
                        ],
                    }
                },
            }
        }

        df = make_product_dataframe()

        df.loc[0, "platform"] = "Amazon Japan"
        df.loc[0, "category"] = "Consumer Electronics"
        df.loc[0, "sale_price"] = 5000

        result = calculate_profitability(
            df,
            fees
        )

        assert result.iloc[0]["platform_fee"] == 420

    def test_amazon_minimum_fee():
        fees = {
            "amazon japan": {
                "display_name": "Amazon Japan",
                "fee_model": "category_percentage",
                "default_category": "consumer electronics",
                "extra_rate": 0.0,
                "enabled": True,
                "categories": {
                    "consumer electronics": {
                        "minimum_fee": 30,
                        "tiers": [
                            {
                                "max_price": 750,
                                "fee_rate": 0.05,
                            },
                            {
                                "max_price": None,
                                "fee_rate": 0.084,
                            },
                        ],
                    }
                },
            }
        }

        df = make_product_dataframe()

        df.loc[0, "platform"] = "Amazon Japan"
        df.loc[0, "category"] = "Consumer Electronics"
        df.loc[0, "sale_price"] = 400

        result = calculate_profitability(
            df,
            fees
        )

        assert result.iloc[0]["platform_fee"] == 30

EBAY_TEST_CONFIG = {
    "usd_to_jpy": 150.0,
    "international_fee_rate": 0.0135,

    "order_fee_usd": {
        "up_to_10": 0.30,
        "over_10": 0.40,
    },

    "categories": {
        "most categories": {
            "tiers": [
                {
                    "max_amount_usd": 7500,
                    "fee_rate": 0.136,
                },
                {
                    "max_amount_usd": None,
                    "fee_rate": 0.0235,
                },
            ]
        }
    },
}


def test_ebay_order_under_10_usd():
    result = calculate_ebay_fee_jpy(
        1200,
        EBAY_TEST_CONFIG,
        "Most Categories",
    )

    assert round(
        result["total_fee_jpy"],
        2
    ) == 224.40


def test_ebay_order_over_10_usd():
    result = calculate_ebay_fee_jpy(
        15000,
        EBAY_TEST_CONFIG,
        "Most Categories",
    )

    assert round(
        result["total_fee_jpy"],
        2
    ) == 2302.50


def test_ebay_progressive_high_value_fee():
    result = calculate_ebay_fee_jpy(
        1200000,
        EBAY_TEST_CONFIG,
        "Most Categories",
    )

    assert round(
        result["total_fee_jpy"],
        2
    ) == 171022.50

def test_ebay_integrates_with_profitability():
    fees = {
        "ebay": {
            "display_name": "eBay.com",
            "fee_model": "ebay_us_japan_seller",
            "enabled": True,
            "usd_to_jpy": 150.0,
            "international_fee_rate": 0.0135,
            "order_fee_usd": {
                "up_to_10": 0.30,
                "over_10": 0.40,
            },
            "categories": {
                "most categories": {
                    "tiers": [
                        {
                            "max_amount_usd": 7500,
                            "fee_rate": 0.136,
                        },
                        {
                            "max_amount_usd": None,
                            "fee_rate": 0.0235,
                        },
                    ]
                }
            },
        }
    }

    df = make_product_dataframe()

    df.loc[0, "platform"] = "eBay"
    df.loc[0, "category"] = "Most Categories"
    df.loc[0, "sale_price"] = 15000
    df.loc[0, "item_cost"] = 7000
    df.loc[0, "shipping_cost"] = 1500

    result = calculate_profitability(
        df,
        fees
    )

    row = result.iloc[0]

    assert row["platform_fee"] == 2302.50
    assert row["profit"] == 4197.50
    assert row["break_even_price"] == 10064.67

def test_ebay_break_even_price():
        base_cost = 8500

        result = calculate_ebay_break_even_price_jpy(
            base_cost,
            1,
            EBAY_TEST_CONFIG,
            "Most Categories",
        )

        assert result == 10064.67