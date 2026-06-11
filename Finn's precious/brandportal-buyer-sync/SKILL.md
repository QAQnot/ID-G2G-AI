---
name: brandportal-buyer-sync
description: Export Brand Portal Buyer data and sync it into Google Sheets. Use for either the download-based Gender/Age workflow or the direct API-based Buyers-by-category workflow. Supports date-based deduplication, skip-existing-date behavior, and range-limited writes that preserve later formula columns.
---

# Brand Portal Buyer Sync

Use the bundled scripts for two workflows:

- Download-based Buyer export, then sync `Gender` / `Age`
- Direct Buyer-by-category API fetch, then write to the `Buyers` tab

## Workflow

1. Ensure `brandportal_state.json` exists and the Brand Portal session is valid.
2. Ask which shop name or shop ID to use before running.
3. Choose one workflow:
   - `Gender/Age`: download Buyer reports, then parse local `.xlsx`
   - `Buyers`: direct API fetch by category, no download-center export needed
4. Sync results into the target Google Sheet tab.
5. Re-run an online Sheet verification after sync.

## Scripts

- `scripts/brandportal_download_buyer_report.py` downloads one Buyer report for a chosen date.
- `scripts/brandportal_buyer_download_batch.py` downloads a month or date range.
- `scripts/brandportal_gender_age_to_sheets.py` syncs local Buyer files into Google Sheets.
- `scripts/brandportal_buyer_category_summary.py` fetches one day of Buyer-by-category data directly from Brand Portal and can write to the `Buyers` tab.
- `scripts/brandportal_buyer_category_batch_to_sheet.py` batch-fetches Buyer-by-category data for a date range and writes it to the `Buyers` tab.
- `scripts/brandportal_verify_sheet_sync.py` checks that the new dates exist in Google Sheets after sync.
- `scripts/brandportal_sync_pipeline.py` runs download and sync as one pipeline.

## Preconditions

- `configs/finn-project-492212-1ed280f69011.json` exists and has access to the target Google Sheet.
- `configs/isrgrootx1.pem` exists for the Brand Portal session.
- `temp_scripts/brandportal_state.json` exists and is valid.
- `gspread` and `openpyxl` are installed in the active environment.
- If state is missing or expired, run `brandportal_login.py` first and save a fresh `brandportal_state.json`.
- Ask the user for the target shop name or shop ID before each download run.

## Target Sheet Rules

- Spreadsheet: `1N3OzU6lFx-zM1WUuxwN1GMEHbtAOGaGUkEjJxg3IHE8`
- Tabs: `Gender`, `Age`
- Match on first column `Date`
- Append only if that date is not already present
- Never write headers into appended rows
- Never clear or overwrite columns `J` and beyond

## Buyers Tab Rules

- Spreadsheet: `1N3OzU6lFx-zM1WUuxwN1GMEHbtAOGaGUkEjJxg3IHE8`
- Tab: `Buyers`
- Direct workflow output columns are `A:H` only:
  - `Date`, `Region`, `Brand Name`, `Shop Name`, `Category`, `Buyers`, `New Buyers`, `Existing Buyers`
- Never write outside `A:H`
- Preserve any formulas or manual content in later columns
- Batch workflow should skip any date already present for the same `Shop Name`
- Single-day workflow may upsert rows by `Date + Region + Brand Name + Shop Name + Category`

## Verification

- After syncing, verify the new dates exist in both `Gender` and `Age`.
- Use a retry if Google Sheets temporarily fails to connect.
- For the `Buyers` tab, verify the expected dates exist and inspect the tail rows when counts look wrong.
