import json

from ebay_fees import (
    calculate_ebay_fee_jpy,
    calculate_ebay_break_even_price_jpy,
)
from pathlib import Path

import pandas as pd


def safe_round(value, digits=2):
    if pd.isna(value):
        return pd.NA

    return round(float(value), digits)


def load_platform_fees(config_path):
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Platform configuration not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        raw_config = json.load(file)

    if not isinstance(raw_config, dict) or not raw_config:
        raise ValueError(
            "Platform configuration must contain at least one platform."
        )

    validated_config = {}

    for platform_name, settings in raw_config.items():

        normalized_name = str(
            platform_name
        ).strip().lower()

        if not normalized_name:
            raise ValueError(
                "Platform names cannot be blank."
            )

        if not isinstance(settings, dict):
            raise ValueError(
                f"Invalid configuration for platform: {platform_name}"
            )

        display_name = settings.get("display_name")
        enabled = settings.get("enabled")
        fee_model = settings.get(
            "fee_model",
            "flat_percentage"
        )

        if (
            not isinstance(display_name, str)
            or not display_name.strip()
        ):
            raise ValueError(
                f"{platform_name}: display_name must be text."
            )

        if not isinstance(enabled, bool):
            raise ValueError(
                f"{platform_name}: enabled must be true or false."
            )

        validated_settings = {
            "display_name": display_name.strip(),
            "enabled": enabled,
            "fee_model": fee_model,
        }

        # -------------------------
        # Flat percentage
        # -------------------------

        if fee_model == "flat_percentage":

            fee_rate = settings.get("fee_rate")

            _validate_rate(
                fee_rate,
                platform_name,
                "fee_rate"
            )

            validated_settings["fee_rate"] = float(
                fee_rate
            )

        # -------------------------
        # Tiered percentage
        # -------------------------

        elif fee_model == "tiered_percentage":

            current_fee_rate = settings.get(
                "current_fee_rate"
            )

            allowed_fee_rates = settings.get(
                "allowed_fee_rates"
            )

            if not isinstance(
                allowed_fee_rates,
                list
            ):
                raise ValueError(
                    f"{platform_name}: "
                    "allowed_fee_rates must be a list."
                )

            for rate in allowed_fee_rates:
                _validate_rate(
                    rate,
                    platform_name,
                    "tiered fee rate"
                )

            if current_fee_rate not in allowed_fee_rates:
                raise ValueError(
                    f"{platform_name}: "
                    "current_fee_rate must be one of "
                    "the allowed fee rates."
                )

            validated_settings[
                "current_fee_rate"
            ] = float(current_fee_rate)

            validated_settings[
                "allowed_fee_rates"
            ] = [
                float(rate)
                for rate in allowed_fee_rates
            ]

        # -------------------------
        # Category-based percentage
        # -------------------------

        elif fee_model == "category_percentage":

            categories = settings.get(
                "categories"
            )

            default_category = settings.get(
                "default_category"
            )

            extra_rate = settings.get(
                "extra_rate",
                0
            )

            _validate_rate(
                extra_rate,
                platform_name,
                "extra_rate"
            )

            if not isinstance(
                categories,
                dict
            ) or not categories:
                raise ValueError(
                    f"{platform_name}: "
                    "categories must contain category rules."
                )

            if (
                not isinstance(default_category, str)
                or default_category not in categories
            ):
                raise ValueError(
                    f"{platform_name}: "
                    "default_category must match a configured category."
                )

            validated_categories = {}

            for category_name, category_rule in categories.items():

                if not isinstance(
                    category_rule,
                    dict
                ):
                    raise ValueError(
                        f"{platform_name}/{category_name}: "
                        "category rule must be an object."
                    )

                minimum_fee = category_rule.get(
                    "minimum_fee",
                    0
                )

                if (
                    isinstance(minimum_fee, bool)
                    or not isinstance(
                        minimum_fee,
                        (int, float)
                    )
                    or minimum_fee < 0
                ):
                    raise ValueError(
                        f"{platform_name}/{category_name}: "
                        "minimum_fee must be zero or greater."
                    )

                validated_rule = {
                    "minimum_fee": float(
                        minimum_fee
                    )
                }

                if "fee_rate" in category_rule:

                    fee_rate = category_rule[
                        "fee_rate"
                    ]

                    _validate_rate(
                        fee_rate,
                        platform_name,
                        f"{category_name} fee_rate"
                    )

                    validated_rule[
                        "fee_rate"
                    ] = float(fee_rate)

                elif "tiers" in category_rule:

                    tiers = category_rule["tiers"]

                    if not isinstance(
                        tiers,
                        list
                    ) or not tiers:
                        raise ValueError(
                            f"{platform_name}/{category_name}: "
                            "tiers must be a non-empty list."
                        )

                    validated_tiers = []

                    for tier in tiers:

                        if not isinstance(
                            tier,
                            dict
                        ):
                            raise ValueError(
                                f"{platform_name}/{category_name}: "
                                "invalid tier."
                            )

                        fee_rate = tier.get(
                            "fee_rate"
                        )

                        max_price = tier.get(
                            "max_price"
                        )

                        _validate_rate(
                            fee_rate,
                            platform_name,
                            f"{category_name} tier fee"
                        )

                        if (
                            max_price is not None
                            and (
                                isinstance(
                                    max_price,
                                    bool
                                )
                                or not isinstance(
                                    max_price,
                                    (int, float)
                                )
                                or max_price < 0
                            )
                        ):
                            raise ValueError(
                                f"{platform_name}/{category_name}: "
                                "max_price must be positive or null."
                            )

                        validated_tiers.append({
                            "max_price": max_price,
                            "fee_rate": float(
                                fee_rate
                            ),
                        })

                    validated_rule[
                        "tiers"
                    ] = validated_tiers

                else:
                    raise ValueError(
                        f"{platform_name}/{category_name}: "
                        "must define fee_rate or tiers."
                    )

                validated_categories[
                    category_name.strip().lower()
                ] = validated_rule

            validated_settings[
                "categories"
            ] = validated_categories

            validated_settings[
                "default_category"
            ] = default_category.strip().lower()

            validated_settings[
                "extra_rate"
            ] = float(extra_rate)
        elif fee_model == "ebay_us_japan_seller":

            usd_to_jpy = settings.get(
                "usd_to_jpy"
            )

            international_fee_rate = settings.get(
                "international_fee_rate"
            )

            order_fee_usd = settings.get(
                "order_fee_usd"
            )

            categories = settings.get(
                "categories"
            )

            if (
                    isinstance(usd_to_jpy, bool)
                    or not isinstance(
                usd_to_jpy,
                (int, float)
            )
                    or usd_to_jpy <= 0
            ):
                raise ValueError(
                    f"{platform_name}: "
                    "usd_to_jpy must be greater than zero."
                )

            _validate_rate(
                international_fee_rate,
                platform_name,
                "international_fee_rate"
            )

            if not isinstance(
                    order_fee_usd,
                    dict
            ):
                raise ValueError(
                    f"{platform_name}: "
                    "order_fee_usd must be configured."
                )

            for fee_name in [
                "up_to_10",
                "over_10",
            ]:
                value = order_fee_usd.get(
                    fee_name
                )

                if (
                        isinstance(value, bool)
                        or not isinstance(
                    value,
                    (int, float)
                )
                        or value < 0
                ):
                    raise ValueError(
                        f"{platform_name}: "
                        f"invalid order fee '{fee_name}'."
                    )

            if (
                    not isinstance(categories, dict)
                    or not categories
            ):
                raise ValueError(
                    f"{platform_name}: "
                    "eBay categories must be configured."
                )

            validated_settings.update({
                "usd_to_jpy": float(
                    usd_to_jpy
                ),
                "international_fee_rate": float(
                    international_fee_rate
                ),
                "order_fee_usd": order_fee_usd,
                "categories": categories,
            })

        else:
            raise ValueError(
                f"{platform_name}: "
                f"unsupported fee model '{fee_model}'."
            )

        validated_config[
            normalized_name
        ] = validated_settings

    return validated_config


def _validate_rate(
    rate,
    platform_name,
    field_name
):
    if (
        isinstance(rate, bool)
        or not isinstance(
            rate,
            (int, float)
        )
    ):
        raise ValueError(
            f"{platform_name}: "
            f"{field_name} must be a number."
        )

    if not 0 <= rate < 1:
        raise ValueError(
            f"{platform_name}: "
            f"{field_name} must be between 0 and 1."
        )


def resolve_fee_components(
    platform_config,
    category,
    sale_price
):
    fee_model = platform_config[
        "fee_model"
    ]

    if fee_model == "flat_percentage":

        return {
            "fee_rate": platform_config[
                "fee_rate"
            ],
            "minimum_fee": 0,
            "extra_rate": 0,
        }

    if fee_model == "tiered_percentage":

        return {
            "fee_rate": platform_config[
                "current_fee_rate"
            ],
            "minimum_fee": 0,
            "extra_rate": 0,
        }

    if fee_model == "category_percentage":

        categories = platform_config[
            "categories"
        ]

        normalized_category = str(
            category or ""
        ).strip().lower()

        if (
                not normalized_category
                or normalized_category not in categories
        ):
            return None

        category_rule = categories[
            normalized_category
        ]

        if "fee_rate" in category_rule:

            fee_rate = category_rule[
                "fee_rate"
            ]

        else:

            fee_rate = None

            for tier in category_rule[
                "tiers"
            ]:

                max_price = tier[
                    "max_price"
                ]

                if (
                    max_price is None
                    or sale_price <= max_price
                ):
                    fee_rate = tier[
                        "fee_rate"
                    ]
                    break

            if fee_rate is None:
                raise ValueError(
                    "No matching fee tier found."
                )

        return {
            "fee_rate": fee_rate,
            "minimum_fee": category_rule[
                "minimum_fee"
            ],
            "extra_rate": platform_config[
                "extra_rate"
            ],
        }

    raise ValueError(
        f"Unsupported fee model: {fee_model}"
    )


def calculate_profitability(
    df,
    platform_fees
):
    results = df.copy()

    results["fee_rate"] = pd.NA
    results["gross_revenue"] = pd.NA
    results["platform_fee"] = pd.NA
    results["product_cost_total"] = pd.NA
    results["total_cost"] = pd.NA
    results["profit"] = pd.NA
    results["margin_pct"] = pd.NA
    results["roi_pct"] = pd.NA
    results["break_even_price"] = pd.NA

    for index, row in results.iterrows():

        platform = str(
            row["platform"]
        ).strip().lower()

        platform_config = platform_fees.get(
            platform
        )

        if platform_config is None:
            continue

        if not platform_config["enabled"]:
            continue

        fee_model = platform_config[
            "fee_model"
        ]

        required_values = [
            row["sale_price"],
            row["item_cost"],
            row["shipping_cost"],
            row["other_costs"],
            row["quantity"],
        ]

        if any(
            pd.isna(value)
            for value in required_values
        ):
            continue

        sale_price = float(
            row["sale_price"]
        )

        item_cost = float(
            row["item_cost"]
        )

        shipping_cost = float(
            row["shipping_cost"]
        )

        other_costs = float(
            row["other_costs"]
        )

        quantity = float(
            row["quantity"]
        )

        if sale_price <= 0:
            continue

        if item_cost < 0:
            continue

        if shipping_cost < 0:
            continue

        if other_costs < 0:
            continue

        if quantity <= 0:
            continue

        category = row.get(
            "category",
            ""
        )

        if fee_model == "ebay_us_japan_seller":

            gross_revenue = (
                    sale_price * quantity
            )

            ebay_fee_result = calculate_ebay_fee_jpy(
                gross_revenue,
                platform_config,
                category,
            )

            if ebay_fee_result is None:
                continue

            platform_fee = ebay_fee_result[
                "total_fee_jpy"
            ]

            fee_rate = pd.NA

        else:

            fee_components = resolve_fee_components(
                platform_config,
                category,
                sale_price,
            )

            if fee_components is None:
                continue

            fee_rate = fee_components[
                "fee_rate"
            ]

            minimum_fee = fee_components[
                "minimum_fee"
            ]

            extra_rate = fee_components[
                "extra_rate"
            ]

            gross_revenue = (
                    sale_price * quantity
            )

            base_platform_fee = max(
                gross_revenue * fee_rate,
                minimum_fee * quantity,
            )

            additional_platform_fee = (
                    gross_revenue * extra_rate
            )

            platform_fee = (
                    base_platform_fee
                    + additional_platform_fee
            )

            additional_platform_fee = (
                    gross_revenue
                    * extra_rate
            )

            platform_fee = (
                    base_platform_fee
                    + additional_platform_fee
            )

        product_cost_total = (
            item_cost * quantity
        )

        base_cost = (
            product_cost_total
            + shipping_cost
            + other_costs
        )

        total_cost = (
            base_cost
            + platform_fee
        )

        profit = (
            gross_revenue
            - total_cost
        )

        if gross_revenue > 0:
            margin_pct = (
                                 profit
                                 / gross_revenue
                         ) * 100
        else:
            margin_pct = pd.NA

        if base_cost > 0:
            roi_pct = (
                              profit
                              / base_cost
                      ) * 100
        else:
            roi_pct = pd.NA

        if fee_model == "ebay_us_japan_seller":
            break_even_price = (
                calculate_ebay_break_even_price_jpy(
                    base_cost,
                    quantity,
                    platform_config,
                    category,
                )
            )

        else:
            effective_fee_rate = (
                    fee_rate + extra_rate
            )

            if (
                    effective_fee_rate < 1
                    and quantity > 0
            ):
                break_even_price = (
                        base_cost
                        / (
                                (
                                        1
                                        - effective_fee_rate
                                )
                                * quantity
                        )
                )
            else:
                break_even_price = pd.NA
        results.at[
            index,
            "fee_rate"
        ] = fee_rate

        results.at[
            index,
            "gross_revenue"
        ] = safe_round(
            gross_revenue
        )

        results.at[
            index,
            "platform_fee"
        ] = safe_round(
            platform_fee
        )

        results.at[
            index,
            "product_cost_total"
        ] = safe_round(
            product_cost_total
        )

        results.at[
            index,
            "total_cost"
        ] = safe_round(
            total_cost
        )

        results.at[
            index,
            "profit"
        ] = safe_round(
            profit
        )

        results.at[
            index,
            "margin_pct"
        ] = safe_round(
            margin_pct
        )

        results.at[
            index,
            "roi_pct"
        ] = safe_round(
            roi_pct
        )

        results.at[
            index,
            "break_even_price"
        ] = safe_round(
            break_even_price
        )

    return results