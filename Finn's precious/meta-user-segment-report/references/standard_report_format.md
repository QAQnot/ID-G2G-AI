# Standard Report Format

Use this exact section order by default:

1. `一、整体概况`
2. `二、广告类型 × 用户分层`
3. `三、投手 × 用户分层`
4. `四、广告类型 × 受众 × 用户分层`
5. `五、收割广告 TOP15 产品详情`
6. `六、合创广告（过滤后）— TOP15 产品 × 用户分层`
7. `七、混合目录 — 完整人群分层`
8. `八、花费结构总览`

## Formatting Rules

- Keep headings in Chinese.
- Put one compact summary line above each core table.
- Use markdown tables for all core quantitative sections.
- Keep the standard audience rows in this order:
  - `engaged`
  - `existing`
  - `prospecting`
  - `unknown`

## Section Details

### Section 1

- Show:
  - data days
  - average daily spend
  - total spend
  - total GMV
  - total ROAS
  - total CPA
  - total CVR
  - total reach
  - total impressions
  - reach rate
  - cost per 1k reach

### Section 2

Show these blocks:

- `收割广告`
- `合创广告`
- `合创广告（过滤后：有目录且非无目录）`
- `混合目录`

Each block uses:

- one summary line
- one detailed segment table with:
  - 分层
  - 花费
  - 占比
  - GMV
  - ROAS
  - CPA
  - AOV
  - CVR
  - CTR
  - CPM
  - 触达
  - 千次触达

### Section 3

Show:

- `收割投手`
- `合创投手`
- `其他投手` only when present
- `各投手`

Each buyer block uses the same detailed segment table style as section 2.

### Section 4

For each module:

- `收割广告 — Cold/Warm × 用户分层`
- `合创广告 — Cold/Warm × 用户分层`
- `混合目录 — Cold/Warm × 用户分层`

Inside each module:

- `Cold (新客)` block
- `Warm (再营销)` block

Each block uses:

- one media summary line
- one detailed segment table

### Section 5

Output one TOP15 product summary table for harvest ads with:

- 产品
- 花费
- ROAS
- CPA
- CVR
- AOV
- Engaged%
- Existing%
- Prosp%

### Section 6

First show:

- `过滤前花费: X -> 过滤后花费: Y (Z%)`

Then output one TOP15 filtered co-creation product summary table with:

- 产品
- 花费
- ROAS
- CPA
- CVR
- Engaged%
- Existing%
- Prosp%

### Section 7

Show:

1. one mixed-catalog total summary line
2. one compact segment table
3. `Cold (新客)` compact block
4. `Warm (再营销)` compact block

Compact tables use:

- 分层
- 花费
- 占比
- ROAS
- CPA
- CVR
- AOV
- 触达

The total mixed-catalog table keeps GMV as well.

### Section 8

Show:

- `按广告类型`
- `按投手类型`
- `各投手`

Use markdown tables, not bullets, for the standard output.

## Output Naming

Unless the user explicitly requests another filename:

- full month report:
  - `user_segment_analysis_YYYY-MM.md`
- custom range report:
  - `user_segment_analysis_YYYY-MM-DD_to_YYYY-MM-DD.md`
