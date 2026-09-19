def calculate_progressive_fee_usd(
    amount_usd,
    tiers,
):
    fee = 0.0
    previous_limit = 0.0

    for tier in tiers:
        max_amount = tier["max_amount_usd"]
        fee_rate = tier["fee_rate"]

        if max_amount is None:
            tier_amount = max(
                amount_usd - previous_limit,
                0
            )

        else:
            tier_amount = max(
                min(amount_usd, max_amount)
                - previous_limit,
                0
            )

        fee += tier_amount * fee_rate

        if (
            max_amount is None
            or amount_usd <= max_amount
        ):
            break

        previous_limit = max_amount

    return fee


def calculate_ebay_fee_jpy(
    gross_revenue_jpy,
    platform_config,
    category,
):
    normalized_category = str(
        category or ""
    ).strip().lower()

    categories = platform_config[
        "categories"
    ]

    if normalized_category not in categories:
        return None

    exchange_rate = platform_config[
        "usd_to_jpy"
    ]

    if exchange_rate <= 0:
        raise ValueError(
            "eBay USD/JPY exchange rate must be greater than zero."
        )

    gross_revenue_usd = (
        gross_revenue_jpy
        / exchange_rate
    )

    category_rule = categories[
        normalized_category
    ]

    variable_fee_usd = (
        calculate_progressive_fee_usd(
            gross_revenue_usd,
            category_rule["tiers"],
        )
    )

    if gross_revenue_usd <= 10:
        fixed_fee_usd = platform_config[
            "order_fee_usd"
        ]["up_to_10"]

    else:
        fixed_fee_usd = platform_config[
            "order_fee_usd"
        ]["over_10"]

    international_fee_rate = (
        platform_config[
            "international_fee_rate"
        ]
    )

    variable_fee_jpy = (
        variable_fee_usd
        * exchange_rate
    )

    fixed_fee_jpy = (
        fixed_fee_usd
        * exchange_rate
    )

    international_fee_jpy = (
        gross_revenue_jpy
        * international_fee_rate
    )

    total_fee_jpy = (
        variable_fee_jpy
        + fixed_fee_jpy
        + international_fee_jpy
    )

    return {
        "total_fee_jpy": total_fee_jpy,
        "variable_fee_jpy": variable_fee_jpy,
        "fixed_order_fee_jpy": fixed_fee_jpy,
        "international_fee_jpy": international_fee_jpy,
        "sale_amount_usd": gross_revenue_usd,
    }

def calculate_ebay_break_even_price_jpy(
    base_cost_jpy,
    quantity,
    platform_config,
    category,
):
    if quantity <= 0:
        return None

    if base_cost_jpy < 0:
        return None

    def profit_at_price(unit_price_jpy):
        gross_revenue_jpy = (
            unit_price_jpy * quantity
        )

        fee_result = calculate_ebay_fee_jpy(
            gross_revenue_jpy,
            platform_config,
            category,
        )

        if fee_result is None:
            return None

        return (
            gross_revenue_jpy
            - base_cost_jpy
            - fee_result["total_fee_jpy"]
        )

    low = 0.0

    high = max(
        base_cost_jpy / quantity,
        1.0,
    )

    high_profit = profit_at_price(
        high
    )

    if high_profit is None:
        return None

    # Expand the search range until
    # the candidate price becomes profitable.
    attempts = 0

    while (
        high_profit < 0
        and attempts < 100
    ):
        high *= 2

        high_profit = profit_at_price(
            high
        )

        attempts += 1

    if high_profit < 0:
        raise ValueError(
            "Unable to determine eBay break-even price."
        )

    # Binary search for the lowest
    # profitable unit sale price.
    for _ in range(100):
        midpoint = (
            low + high
        ) / 2

        midpoint_profit = profit_at_price(
            midpoint
        )

        if midpoint_profit is None:
            return None

        if midpoint_profit < 0:
            low = midpoint
        else:
            high = midpoint

    return round(
        high,
        2
    )