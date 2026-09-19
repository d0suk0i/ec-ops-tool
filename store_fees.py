def calculate_store_fee_jpy(
    gross_revenue_jpy,
    platform_config,
):
    monthly_fixed_fee = platform_config[
        "monthly_fixed_fee"
    ]

    estimated_monthly_orders = platform_config[
        "estimated_monthly_orders"
    ]

    variable_components = platform_config[
        "variable_fee_components"
    ]

    if estimated_monthly_orders <= 0:
        raise ValueError(
            "estimated_monthly_orders must be greater than zero."
        )

    variable_fee_rate = sum(
        variable_components.values()
    )

    if not 0 <= variable_fee_rate < 1:
        raise ValueError(
            "Combined variable fee rate must be between 0 and 1."
        )

    allocated_fixed_fee = (
        monthly_fixed_fee
        / estimated_monthly_orders
    )

    variable_fee = (
        gross_revenue_jpy
        * variable_fee_rate
    )

    total_fee = (
        allocated_fixed_fee
        + variable_fee
    )

    return {
        "total_fee_jpy": total_fee,
        "variable_fee_jpy": variable_fee,
        "allocated_fixed_fee_jpy": allocated_fixed_fee,
        "variable_fee_rate": variable_fee_rate,
    }


def calculate_store_break_even_price_jpy(
    base_cost_jpy,
    quantity,
    platform_config,
):
    if quantity <= 0:
        return None

    monthly_fixed_fee = platform_config[
        "monthly_fixed_fee"
    ]

    estimated_monthly_orders = platform_config[
        "estimated_monthly_orders"
    ]

    variable_components = platform_config[
        "variable_fee_components"
    ]

    if estimated_monthly_orders <= 0:
        raise ValueError(
            "estimated_monthly_orders must be greater than zero."
        )

    variable_fee_rate = sum(
        variable_components.values()
    )

    allocated_fixed_fee = (
        monthly_fixed_fee
        / estimated_monthly_orders
    )

    break_even_total = (
        base_cost_jpy
        + allocated_fixed_fee
    ) / (
        1 - variable_fee_rate
    )

    return round(
        break_even_total / quantity,
        2
    )