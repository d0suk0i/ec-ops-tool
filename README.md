# EC Operations Tool

[日本語版はこちら](README_ja.md)
# EC Operations Tool

A Python tool for checking e-commerce product data, calculating profitability, and exporting the results to Excel.

I built this around the kind of product and marketplace data that comes up in EC operations work in Japan. The goal was to take a CSV or Excel file, catch obvious data problems, calculate marketplace costs and profit, and produce something that can actually be reviewed in a spreadsheet.

## What it does

The tool imports product data and checks for missing values, invalid numbers, duplicate rows, and conflicting SKUs.

For valid products it calculates marketplace fees, total cost, profit, margin, ROI, and break-even price. Products can then be ranked using configurable weights for profit, margin, and ROI.

The final report is exported as an Excel workbook with separate sheets for the main analysis, scoring details, validation problems, and duplicate records.

Current marketplace support:

- Mercari
- Yahoo! Auctions
- Yahoo! Flea Market
- Rakuma
- Amazon Japan
- eBay
- Yahoo! Shopping
- Rakuten Ichiba

The fee logic is configurable because these marketplaces do not all use the same fee structure. The project currently handles flat fees, tiered fees, category-based fees, fixed order charges, international fees, and store-level monthly costs.

## Example

A sample input file is included here:

`examples/sample_products.csv`

A generated example report is included here:

`examples/sample_analysis.xlsx`

The sample contains normal products as well as a few intentionally bad records so the validation and review features can be seen in the output.

## Running the tool

Install the required packages:

```bash
pip install -r requirements.txt