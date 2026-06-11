# Report Workflow

## Start Conditions

Before any pull or report work, confirm:

1. Token or approved credential source
2. Account IDs
3. Date range
4. Buyer or person-name mapping

If the user does not provide updated buyer mapping, use `buyer_mapping_template.json`.

## Data Pull Rules

- API breakdown: `user_segment_key`
- Pull level: `ad`
- Keep these output columns:
  - `date_start`, `date_stop`
  - `account_name`, `account_id`
  - `campaign_name`, `adset_name`, `ad_name`
  - `user_segment_key`
  - `spend`, `reach`, `impressions`
  - `clicks_link`
  - `purchase_count`, `purchase_value`, `add_to_cart_value`
- `clicks_link` must come from `inline_link_clicks`
- Purchase metrics must come from `catalog_segment_actions` and `catalog_segment_value`

## Classification Rules

### Module classification

- `ad_name` contains `_SC` or `_JJ` -> `收割广告`
- `ad_name` contains `帖子` -> `合创广告`
- `ad_name` contains `混合目录` -> `混合目录`

### Audience classification

- `adset_name` contains `cold` or `COLD` -> `cold`
- `adset_name` contains `warm` or `WARM` -> `warm`

### G2G subtype classification

- `adset_name` contains `目录`, `CONV`, or `PUR` -> `转化帖子`
- `adset_name` contains `无目录`, `RCH`, or `IMP` -> `曝光帖子`

### Buyer classification

- `WK` -> `WK`
- `ZXS` -> `WL`
- `WL` -> `WL`
- `LLY` -> `JH`
- `LZY` -> `ZY`
- `JM` -> `JM`
- `CJH` -> `JH`
- `LKQ` -> `KQ`
- `ZQ` -> `ZQ`
- else -> `未知`

### Buyer groups

- `WL`, `ZY`, `JH` -> `收割投手`
- `WK`, `KQ`, `JM` -> `合创投手`
- others -> `其他投手`

### Product name

- Use the first `_` segment of `ad_name`

## Execution Notes

- Use single-account validation when the user is checking field correctness.
- Use all requested accounts only after validation is accepted.
- Save CSV with BOM for spreadsheet compatibility on Windows.
- Save markdown as UTF-8.
- If the user does not provide a report output path, auto-name the markdown file:
  - `user_segment_analysis_YYYY-MM.md` for a full month
  - `user_segment_analysis_YYYY-MM-DD_to_YYYY-MM-DD.md` for a custom range
