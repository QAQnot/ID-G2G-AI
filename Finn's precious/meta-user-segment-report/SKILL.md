---
name: meta-user-segment-report
description: Pull Meta Ads audience-segment data with the `user_segment_key` breakdown and generate the team's standard markdown audience report. Use this skill when the user wants to verify Meta audience segments via API, export one or more ad accounts by campaign/adset/ad with audience segments, compare spend, GMV, reach, impressions, and clicks_link by audience segment, or generate the standard monthly or custom-period audience report.
---

# Meta User Segment Report

Use this skill for the end-to-end workflow that pulls Meta audience-segment data and turns it into the standard team markdown report.

## Required Inputs

Before running any pull or report task, request these inputs if they are not already confirmed:

1. Access token or approved credential source.
2. Ad account ID list.
3. Date range.
4. Buyer or person-name mapping confirmation.

Do not start API requests until token and account IDs are confirmed.

## Workflow

1. Confirm whether the user wants a single-account validation pull or a multi-account pull.
2. Pull raw data with `scripts/fetch_meta_user_segment_insights.py`.
3. Confirm or override buyer mapping using `references/buyer_mapping_template.json`.
4. Generate the markdown report with `scripts/generate_meta_user_segment_report.py`.
5. Summarize findings after the markdown is produced.

For the standard operating flow, read [references/report_workflow.md](references/report_workflow.md).

## Output Contract

Always generate the markdown report in the current team format represented by the June audience report.

Before generating or updating a report, read:

- [references/standard_report_format.md](references/standard_report_format.md)

Do not invent a new report layout unless the user explicitly asks for one.

## Pull Rules

- Use `level=ad` when campaign, ad set, and ad name must stay in each row.
- Export:
  - `date_start`, `date_stop`
  - `account_name`, `account_id`
  - `campaign_name`, `adset_name`, `ad_name`
  - `user_segment_key`
  - `spend`, `reach`, `impressions`
  - `clicks_link`
  - `purchase_count`, `purchase_value`, `add_to_cart_value`
- Keep `clicks_link = inline_link_clicks`.
- Keep purchase metrics from `catalog_segment_actions` and `catalog_segment_value`.
- Do not request top-level `clicks`.
- Write CSV as `utf-8-sig`.

## Report Rules

- Use `user_segment_key` as the audience-segment source.
- Use the first `_` segment of `ad_name` as product name.
- Apply the audience, module, G2G subtype, buyer, and buyer-group rules described in [references/report_workflow.md](references/report_workflow.md).

## Entrypoints

```bash
python scripts/fetch_meta_user_segment_insights.py --access-token "<TOKEN>" --accounts act_123,act_456 --since 2026-05-01 --until 2026-05-31 --output output/all_accounts_user_segment_insights_2026-05.csv

python scripts/generate_meta_user_segment_report.py --input output/all_accounts_user_segment_insights_2026-05.csv --title "Audience Segment Performance Report" --period "2026-05-01 ~ 2026-05-31" --source-name "all_accounts_user_segment_insights_2026-05.csv" --analysis-date "2026-06-05"
```

If `--output` is omitted, the report script must auto-name the file as:

- `user_segment_analysis_YYYY-MM.md` for full natural-month ranges
- `user_segment_analysis_YYYY-MM-DD_to_YYYY-MM-DD.md` for custom ranges

## Resources

### scripts/

- `fetch_meta_user_segment_insights.py`
- `generate_meta_user_segment_report.py`

### references/

- `buyer_mapping_template.json`
- `report_workflow.md`
- `standard_report_format.md`
