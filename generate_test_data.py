import random
from pathlib import Path

import pandas as pd


random.seed(42)


PRODUCT_NAMES = [
    "Wireless Mouse",
    "Mechanical Keyboard",
    "USB-C Hub",
    "Webcam",
    "Bluetooth Speaker",
    "Gaming Headset",
    "Laptop Stand",
    "Portable SSD",
    "USB Microphone",
    "Phone Charger",
    "ワイヤレスマウス",
    "メカニカルキーボード",
    "USBハブ",
    "ウェブカメラ",
    "Bluetoothスピーカー",
    "ノートPCスタンド",
    "外付けSSD",
    "スマホ充電器",
]

SUPPORTED_PLATFORMS = [
    "Mercari",
    "Yahoo Auctions",
]


def create_normal_product(index):
    item_cost = random.randint(500, 8000)

    shipping_cost = random.choice([
        210,
        450,
        750,
        850,
        1050,
    ])

    other_costs = random.choice([
        0,
        0,
        0,
        100,
        200,
        300,
    ])

    # Generate a mixture of strong and weak margins
    markup = random.uniform(
        1.05,
        2.2
    )

    sale_price = round(
        item_cost * markup
        + shipping_cost
        + other_costs
    )

    return {
        "sku": f"SKU{index:04d}",
        "product_name": random.choice(
            PRODUCT_NAMES
        ),
        "platform": random.choice(
            SUPPORTED_PLATFORMS
        ),
        "sale_price": sale_price,
        "item_cost": item_cost,
        "shipping_cost": shipping_cost,
        "other_costs": other_costs,
        "quantity": random.choice([
            1,
            1,
            1,
            2,
            3,
            5,
        ]),
    }


def main():
    rows = []

    # -------------------------
    # 130 mostly normal products
    # -------------------------

    for index in range(
        1,
        131
    ):
        rows.append(
            create_normal_product(index)
        )

    # -------------------------
    # Exact duplicates
    # -------------------------

    rows.append(
        rows[10].copy()
    )

    rows.append(
        rows[25].copy()
    )

    rows.append(
        rows[60].copy()
    )

    # -------------------------
    # Conflicting duplicate SKU
    # -------------------------

    conflict = rows[20].copy()

    conflict["sale_price"] += 2000

    rows.append(conflict)

    # -------------------------
    # Missing item cost
    # -------------------------

    rows.append({
        "sku": "TEST-MISSING-COST",
        "product_name": "Missing Cost Product",
        "platform": "Mercari",
        "sale_price": 5000,
        "item_cost": None,
        "shipping_cost": 450,
        "other_costs": 0,
        "quantity": 1,
    })

    # -------------------------
    # Missing sale price
    # -------------------------

    rows.append({
        "sku": "TEST-MISSING-PRICE",
        "product_name": "Missing Price Product",
        "platform": "Yahoo Auctions",
        "sale_price": None,
        "item_cost": 2000,
        "shipping_cost": 750,
        "other_costs": 0,
        "quantity": 1,
    })

    # -------------------------
    # Invalid numeric value
    # -------------------------

    rows.append({
        "sku": "TEST-BAD-NUMBER",
        "product_name": "Bad Number Product",
        "platform": "Mercari",
        "sale_price": "not-a-number",
        "item_cost": 1800,
        "shipping_cost": 450,
        "other_costs": 0,
        "quantity": 1,
    })

    # -------------------------
    # Negative cost
    # -------------------------

    rows.append({
        "sku": "TEST-NEGATIVE",
        "product_name": "Negative Cost Product",
        "platform": "Mercari",
        "sale_price": 5000,
        "item_cost": -1000,
        "shipping_cost": 450,
        "other_costs": 0,
        "quantity": 1,
    })

    # -------------------------
    # Zero quantity
    # -------------------------

    rows.append({
        "sku": "TEST-ZERO-QTY",
        "product_name": "Zero Quantity Product",
        "platform": "Mercari",
        "sale_price": 5000,
        "item_cost": 2000,
        "shipping_cost": 450,
        "other_costs": 0,
        "quantity": 0,
    })

    # -------------------------
    # Negative quantity
    # -------------------------

    rows.append({
        "sku": "TEST-NEGATIVE-QTY",
        "product_name": "Negative Quantity Product",
        "platform": "Yahoo Auctions",
        "sale_price": 5000,
        "item_cost": 2000,
        "shipping_cost": 450,
        "other_costs": 0,
        "quantity": -2,
    })

    # -------------------------
    # Unknown marketplace
    # -------------------------

    rows.append({
        "sku": "TEST-UNKNOWN",
        "product_name": "Unknown Platform Product",
        "platform": "Amazon JP",
        "sale_price": 7000,
        "item_cost": 3000,
        "shipping_cost": 600,
        "other_costs": 200,
        "quantity": 1,
    })

    # -------------------------
    # Deliberate loss
    # -------------------------

    rows.append({
        "sku": "TEST-LOSS",
        "product_name": "Loss Product",
        "platform": "Mercari",
        "sale_price": 3000,
        "item_cost": 3500,
        "shipping_cost": 750,
        "other_costs": 200,
        "quantity": 1,
    })

    # -------------------------
    # Very low margin
    # -------------------------

    rows.append({
        "sku": "TEST-LOW-MARGIN",
        "product_name": "Low Margin Product",
        "platform": "Yahoo Auctions",
        "sale_price": 5000,
        "item_cost": 3900,
        "shipping_cost": 450,
        "other_costs": 100,
        "quantity": 1,
    })

    dataframe = pd.DataFrame(
        rows
    )

    output_path = Path(
        "input/products_stress_test.csv"
    )

    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"Created {len(dataframe)} test rows."
    )

    print(
        f"Saved to: {output_path}"
    )


if __name__ == "__main__":
    main()