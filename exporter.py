from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


# ---------- COLOURS ----------

HEADER_FILL = PatternFill(
    "solid",
    fgColor="1F4E78"
)

PROFITABLE_FILL = PatternFill(
    "solid",
    fgColor="C6EFCE"
)

HIGH_ROI_FILL = PatternFill(
    "solid",
    fgColor="A9D18E"
)

WARNING_FILL = PatternFill(
    "solid",
    fgColor="FFF2CC"
)

REVIEW_FILL = PatternFill(
    "solid",
    fgColor="FCE4D6"
)

LOSS_FILL = PatternFill(
    "solid",
    fgColor="FFC7CE"
)


# ---------- HELPERS ----------

def auto_size_columns(worksheet):
    """
    Resize each column based on the longest displayed value,
    including currency and percentage formatting.
    """

    for column_cells in worksheet.columns:

        max_length = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:

            if cell.value is None:
                continue

            # Estimate how the value will actually appear
            if isinstance(cell.value, (int, float)):

                if "¥" in cell.number_format:
                    display_value = f"¥{cell.value:,.2f}"

                elif "%" in cell.number_format:
                    display_value = f"{cell.value:.2f}%"

                else:
                    display_value = str(cell.value)

            else:
                display_value = str(cell.value)

            max_length = max(
                max_length,
                len(display_value)
            )

        # Extra space for filter arrows / visual padding
        worksheet.column_dimensions[
            column_letter
        ].width = max_length + 3


def format_headers(worksheet):

    thin_border = Border(
        bottom=Side(
            style="thin",
            color="D9E1F2"
        )
    )

    for cell in worksheet[1]:

        cell.fill = HEADER_FILL

        cell.font = Font(
            color="FFFFFF",
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        cell.border = thin_border

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions


def format_status_cells(worksheet, status_column):

    for row_number in range(
        2,
        worksheet.max_row + 1
    ):

        cell = worksheet.cell(
            row=row_number,
            column=status_column
        )

        status = str(cell.value or "")

        # Severity takes priority
        if "LOSS" in status:
            cell.fill = LOSS_FILL

        elif "REVIEW REQUIRED" in status:
            cell.fill = REVIEW_FILL

        elif "LOW MARGIN" in status:
            cell.fill = WARNING_FILL

        elif "HIGH ROI" in status:
            cell.fill = HIGH_ROI_FILL

        elif "PROFITABLE" in status:
            cell.fill = PROFITABLE_FILL


# ---------- EXPORT ----------

def export_analysis_report(
    analysis,
    validation_issues,
    duplicate_issues,
    output_dir
):

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_path = (
        output_dir
        / f"ec_analysis_{timestamp}.xlsx"
    )

    # -------------------------
    # SUMMARY
    # -------------------------

    total_products = len(analysis)

    profitable_products = analysis[
        analysis["flags"].str.contains(
            "PROFITABLE",
            na=False
        )
    ].shape[0]

    review_products = analysis[
        analysis["flags"].str.contains(
            "REVIEW REQUIRED",
            na=False
        )
    ].shape[0]

    loss_products = analysis[
        analysis["flags"].str.contains(
            "LOSS",
            na=False
        )
    ].shape[0]

    summary = pd.DataFrame({
        "Metric": [
            "Products analyzed",
            "Profitable products",
            "Products requiring review",
            "Loss-making products",
            "Validation issues",
            "Duplicate issues",
        ],
        "Value": [
            total_products,
            profitable_products,
            review_products,
            loss_products,
            len(validation_issues),
            len(duplicate_issues),
        ],
    })

    # -------------------------
    # CLEAN MAIN REPORT
    # -------------------------

    report_columns = [
        "priority_rank",
        "sku",
        "product_name",
        "platform",
        "category",
        "quantity",
        "sale_price",
        "item_cost",
        "shipping_cost",
        "other_costs",
        "platform_fee",
        "total_cost",
        "profit",
        "margin_pct",
        "roi_pct",
        "break_even_price",
        "flags",
    ]

    product_report = analysis[
        report_columns
    ].copy()

    product_report = product_report.rename(
        columns={
            "priority_rank": "Rank",
            "sku": "SKU",
            "product_name": "Product",
            "platform": "Platform",
            "category": "Category",
            "quantity": "Quantity",
            "sale_price": "Sale Price",
            "item_cost": "Item Cost",
            "shipping_cost": "Shipping",
            "other_costs": "Other Costs",
            "platform_fee": "Platform Fee",
            "total_cost": "Total Cost",
            "profit": "Profit",
            "margin_pct": "Margin",
            "roi_pct": "ROI",
            "break_even_price": "Break-Even Price",
            "flags": "Status",
        }
    )

    # -------------------------
    # SCORING DETAIL
    # -------------------------

    scoring_columns = [
        "sku",
        "product_name",
        "profit_score",
        "margin_score",
        "roi_score",
        "priority_score",
        "priority_rank",
    ]

    scoring_report = analysis[
        scoring_columns
    ].copy()

    scoring_report = scoring_report.rename(
        columns={
            "sku": "SKU",
            "product_name": "Product",
            "profit_score": "Profit Score",
            "margin_score": "Margin Score",
            "roi_score": "ROI Score",
            "priority_score": "Priority Score",
            "priority_rank": "Rank",
        }
    )

    # -------------------------
    # WRITE WORKBOOK
    # -------------------------

    with pd.ExcelWriter(
        output_path,
        engine="openpyxl"
    ) as writer:

        summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        product_report.to_excel(
            writer,
            sheet_name="Product Analysis",
            index=False
        )

        scoring_report.to_excel(
            writer,
            sheet_name="Scoring Detail",
            index=False
        )

        validation_issues.to_excel(
            writer,
            sheet_name="Validation Issues",
            index=False
        )

        duplicate_issues.to_excel(
            writer,
            sheet_name="Duplicate Issues",
            index=False
        )

        workbook = writer.book

        # -------------------------
        # GENERAL FORMATTING
        # -------------------------

        for worksheet in workbook.worksheets:

            format_headers(
                worksheet
            )

            auto_size_columns(
                worksheet
            )

        # -------------------------
        # PRODUCT ANALYSIS FORMATS
        # -------------------------

        analysis_sheet = workbook[
            "Product Analysis"
        ]

        headers = {
            cell.value: cell.column
            for cell in analysis_sheet[1]
        }

        currency_columns = [
            "Sale Price",
            "Item Cost",
            "Shipping",
            "Other Costs",
            "Platform Fee",
            "Total Cost",
            "Profit",
            "Break-Even Price",
        ]

        for column_name in currency_columns:

            column_number = headers[
                column_name
            ]

            for row in range(
                2,
                analysis_sheet.max_row + 1
            ):

                analysis_sheet.cell(
                    row=row,
                    column=column_number
                ).number_format = '¥#,##0.00'

        # Margin and ROI are already stored as
        # numbers such as 33.47, so add the %
        # symbol without multiplying by 100.
        for column_name in [
            "Margin",
            "ROI",
        ]:

            column_number = headers[
                column_name
            ]

            for row in range(
                2,
                analysis_sheet.max_row + 1
            ):

                analysis_sheet.cell(
                    row=row,
                    column=column_number
                ).number_format = '0.00"%"'

        # Status cell background colours
        format_status_cells(
            analysis_sheet,
            headers["Status"]
        )

        # Highlight negative profit directly
        profit_column = headers["Profit"]

        for row in range(
            2,
            analysis_sheet.max_row + 1
        ):

            profit_cell = analysis_sheet.cell(
                row=row,
                column=profit_column
            )

            if (
                isinstance(
                    profit_cell.value,
                    (int, float)
                )
                and profit_cell.value < 0
            ):
                profit_cell.fill = LOSS_FILL

        # -------------------------
        # SCORING SHEET FORMATS
        # -------------------------

        scoring_sheet = workbook[
            "Scoring Detail"
        ]

        scoring_headers = {
            cell.value: cell.column
            for cell in scoring_sheet[1]
        }

        for column_name in [
            "Profit Score",
            "Margin Score",
            "ROI Score",
            "Priority Score",
        ]:

            column_number = scoring_headers[
                column_name
            ]

            for row in range(
                2,
                scoring_sheet.max_row + 1
            ):

                scoring_sheet.cell(
                    row=row,
                    column=column_number
                ).number_format = "0.00"

        # Re-run sizing after header names
        # and formatting are finalized.
        for worksheet in workbook.worksheets:

            auto_size_columns(
                worksheet
            )

    return output_path