from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


SEGMENT_ORDER = ["engaged", "existing", "prospecting", "unknown"]
DEFAULT_BUYER_RULES = [
    {"contains": "WK", "buyer": "WK"},
    {"contains": "ZXS", "buyer": "WL"},
    {"contains": "WL", "buyer": "WL"},
    {"contains": "LLY", "buyer": "JH"},
    {"contains": "LZY", "buyer": "ZY"},
    {"contains": "JM", "buyer": "JM"},
    {"contains": "CJH", "buyer": "JH"},
    {"contains": "LKQ", "buyer": "KQ"},
    {"contains": "ZQ", "buyer": "ZQ"},
]
DEFAULT_BUYER_GROUPS = {
    "收割投手": ["WL", "ZY", "JH"],
    "合创投手": ["WK", "KQ", "JM"],
}
BUYER_ORDER = ["WL", "ZY", "JH", "WK", "KQ", "JM", "ZQ", "未知"]
BUYER_GROUP_ORDER = ["收割投手", "合创投手", "其他投手"]
MODULE_ORDER = ["收割广告", "合创广告", "混合目录"]


@dataclass
class Metrics:
    spend: float
    gmv: float
    purchases: float
    clicks: float
    impressions: float
    reach: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate user segment markdown report.")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=False, default=None, help="Output markdown path")
    parser.add_argument("--title", required=True, help="Report title")
    parser.add_argument("--period", required=True, help="Date period label")
    parser.add_argument("--source-name", required=True, help="Source file name shown in report")
    parser.add_argument("--analysis-date", required=True, help="Analysis date label")
    parser.add_argument("--buyer-mapping", default=None, help="Optional JSON file overriding buyer rules and groups")
    return parser.parse_args()


def safe_div(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator


def fmt_money(value: float, digits: int = 0) -> str:
    return f"${value:,.{digits}f}"


def fmt_num(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}"


def fmt_pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def fmt_ratio(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def load_buyer_mapping(path: str | None) -> tuple[list[dict], dict]:
    if not path:
        return DEFAULT_BUYER_RULES, DEFAULT_BUYER_GROUPS
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload.get("buyer_code_rules", DEFAULT_BUYER_RULES), payload.get("buyer_group_rules", DEFAULT_BUYER_GROUPS)


def normalize_segment(value: str) -> str:
    value = str(value or "").strip().lower()
    if value in {"engaged", "existing", "prospecting"}:
        return value
    return "unknown"


def classify_module(ad_name: str) -> str:
    name = str(ad_name or "")
    parts = name.split("_")
    first_part = parts[0] if parts else ""
    if "混合目录" in first_part or name.startswith("混合目录"):
        return "混合目录"
    if any(part.startswith("SC") or part.startswith("JJ") for part in parts[1:]):
        return "收割广告"
    if "帖子" in name or any("帖子" in part for part in parts[1:]):
        return "合创广告"
    return "其他"


def classify_harvest_format(ad_name: str) -> str:
    name = str(ad_name or "")
    parts = name.split("_")
    for part in parts[1:]:
        if part.startswith("SC"):
            return "图文"
        if part.startswith("JJ"):
            return "视频"
    return "未知"


def classify_audience(adset_name: str) -> str:
    value = str(adset_name or "").lower()
    if "cold" in value:
        return "cold"
    if "warm" in value:
        return "warm"
    return "unknown"


def classify_g2g_subtype(adset_name: str) -> str:
    value = str(adset_name or "")
    upper = value.upper()
    if "无目录" in value or "RCH" in upper or "IMP" in upper:
        return "曝光帖子"
    if "目录" in value or "CONV" in upper or "PUR" in upper:
        return "转化帖子"
    return "其他帖子"


def classify_buyer(campaign_name: str, buyer_rules: list[dict]) -> str:
    value = str(campaign_name or "")
    for rule in buyer_rules:
        if rule["contains"] in value:
            return rule["buyer"]
    return "未知"


def classify_buyer_group(buyer: str, buyer_groups: dict) -> str:
    for group_name, buyers in buyer_groups.items():
        if buyer in buyers:
            return group_name
    return "其他投手"


def extract_product(ad_name: str) -> str:
    value = str(ad_name or "").strip()
    if not value:
        return "未知产品"
    return value.split("_", 1)[0].strip() or "未知产品"


def load_data(csv_path: Path, buyer_rules: list[dict], buyer_groups: dict) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    numeric_columns = [
        "spend",
        "reach",
        "impressions",
        "clicks_link",
        "purchase_count",
        "purchase_value",
        "add_to_cart_value",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    df["user_segment_key"] = df["user_segment_key"].map(normalize_segment)
    df["module_type"] = df["ad_name"].map(classify_module)
    df["harvest_format"] = df["ad_name"].map(classify_harvest_format)
    df["audience_type"] = df["adset_name"].map(classify_audience)
    df["g2g_subtype"] = df["adset_name"].map(classify_g2g_subtype)
    df["buyer"] = df["campaign_name"].map(lambda value: classify_buyer(value, buyer_rules))
    df["buyer_group"] = df["buyer"].map(lambda value: classify_buyer_group(value, buyer_groups))
    df["product_name"] = df["ad_name"].map(extract_product)
    return df


def metrics_from_df(df: pd.DataFrame) -> Metrics:
    return Metrics(
        spend=float(df["spend"].sum()),
        gmv=float(df["purchase_value"].sum()),
        purchases=float(df["purchase_count"].sum()),
        clicks=float(df["clicks_link"].sum()),
        impressions=float(df["impressions"].sum()),
        reach=float(df["reach"].sum()),
    )


def build_summary_line(df: pd.DataFrame, include_reach: bool = True) -> str:
    m = metrics_from_df(df)
    roas = safe_div(m.gmv, m.spend)
    cpa = safe_div(m.spend, m.purchases)
    cvr = safe_div(m.purchases, m.clicks)
    reach_cost = safe_div(m.spend * 1000, m.reach)
    parts = [
        f"总花费: {fmt_money(m.spend)}",
        f"GMV: {fmt_money(m.gmv)}",
        f"ROAS: {fmt_ratio(roas)}",
        f"CPA: {fmt_money(cpa, 2)}",
        f"CVR: {fmt_pct(cvr)}",
    ]
    if include_reach:
        parts.extend(
            [
                f"触达: {fmt_num(m.reach)}",
                f"千次触达花费: {fmt_money(reach_cost, 2)}",
            ]
        )
    return " | ".join(parts)


def build_summary_line_with_media(df: pd.DataFrame) -> str:
    m = metrics_from_df(df)
    roas = safe_div(m.gmv, m.spend)
    cpa = safe_div(m.spend, m.purchases)
    cvr = safe_div(m.purchases, m.clicks)
    cpm = safe_div(m.spend * 1000, m.impressions)
    reach_cost = safe_div(m.spend * 1000, m.reach)
    parts = [
        f"总花费: {fmt_money(m.spend)}",
        f"GMV: {fmt_money(m.gmv)}",
        f"ROAS: {fmt_ratio(roas)}",
        f"CPA: {fmt_money(cpa, 2)}",
        f"CVR: {fmt_pct(cvr)}",
        f"CPM: {fmt_money(cpm, 3)}",
        f"触达: {fmt_num(m.reach)}",
        f"千次触达花费: {fmt_money(reach_cost, 2)}",
    ]
    return " | ".join(parts)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "| 无数据 |\n|---|\n| 无 |"
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    return "\n".join(lines)


def segment_table(df: pd.DataFrame, spend_share_base: float | None = None) -> str:
    spend_share_base = spend_share_base if spend_share_base is not None else float(df["spend"].sum())
    rows = []
    for segment in SEGMENT_ORDER:
        sdf = df[df["user_segment_key"] == segment]
        m = metrics_from_df(sdf)
        rows.append(
            {
                "分层": segment,
                "花费": fmt_money(m.spend),
                "占比": fmt_pct(safe_div(m.spend, spend_share_base)),
                "GMV": fmt_money(m.gmv),
                "ROAS": fmt_ratio(safe_div(m.gmv, m.spend)),
                "CPA": fmt_money(safe_div(m.spend, m.purchases), 2),
                "CVR": fmt_pct(safe_div(m.purchases, m.clicks)),
                "触达": fmt_num(m.reach),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def detailed_segment_table(df: pd.DataFrame, spend_share_base: float | None = None) -> str:
    spend_share_base = spend_share_base if spend_share_base is not None else float(df["spend"].sum())
    rows = []
    for segment in SEGMENT_ORDER:
        sdf = df[df["user_segment_key"] == segment]
        m = metrics_from_df(sdf)
        rows.append(
            {
                "分层": segment,
                "花费": fmt_money(m.spend),
                "占比": fmt_pct(safe_div(m.spend, spend_share_base), 0),
                "GMV": fmt_money(m.gmv),
                "ROAS": fmt_ratio(safe_div(m.gmv, m.spend)),
                "CPA": fmt_money(safe_div(m.spend, m.purchases), 2),
                "AOV": fmt_money(safe_div(m.gmv, m.purchases), 2),
                "CVR": fmt_pct(safe_div(m.purchases, m.clicks)),
                "CTR": fmt_pct(safe_div(m.clicks, m.impressions), 2),
                "CPM": fmt_money(safe_div(m.spend * 1000, m.impressions), 3),
                "触达": fmt_num(m.reach),
                "千次触达": fmt_money(safe_div(m.spend * 1000, m.reach), 2),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def top_products_mix_table(df: pd.DataFrame, top_n: int = 15) -> str:
    grouped = (
        df.groupby("product_name", as_index=False)
        .agg(
            spend=("spend", "sum"),
            gmv=("purchase_value", "sum"),
            purchases=("purchase_count", "sum"),
            clicks=("clicks_link", "sum"),
        )
        .sort_values("spend", ascending=False)
        .head(top_n)
    )
    rows = []
    for _, row in grouped.iterrows():
        pdf = df[df["product_name"] == row["product_name"]]
        total_spend = float(pdf["spend"].sum())
        segment_spend = pdf.groupby("user_segment_key")["spend"].sum().to_dict()
        rows.append(
            {
                "产品": row["product_name"],
                "花费": fmt_money(row["spend"]),
                "ROAS": fmt_ratio(safe_div(row["gmv"], row["spend"])),
                "CPA": fmt_money(safe_div(row["spend"], row["purchases"]), 2),
                "CVR": fmt_pct(safe_div(row["purchases"], row["clicks"])),
                "AOV": fmt_money(safe_div(row["gmv"], row["purchases"]), 2),
                "Engaged%": fmt_pct(safe_div(segment_spend.get("engaged", 0.0), total_spend), 0),
                "Existing%": fmt_pct(safe_div(segment_spend.get("existing", 0.0), total_spend), 0),
                "Prosp%": fmt_pct(safe_div(segment_spend.get("prospecting", 0.0), total_spend), 0),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def filtered_products_mix_table(df: pd.DataFrame, top_n: int = 15) -> str:
    grouped = (
        df.groupby("product_name", as_index=False)
        .agg(
            spend=("spend", "sum"),
            gmv=("purchase_value", "sum"),
            purchases=("purchase_count", "sum"),
            clicks=("clicks_link", "sum"),
        )
        .sort_values("spend", ascending=False)
        .head(top_n)
    )
    rows = []
    for _, row in grouped.iterrows():
        pdf = df[df["product_name"] == row["product_name"]]
        total_spend = float(pdf["spend"].sum())
        segment_spend = pdf.groupby("user_segment_key")["spend"].sum().to_dict()
        rows.append(
            {
                "产品": row["product_name"],
                "花费": fmt_money(row["spend"]),
                "ROAS": fmt_ratio(safe_div(row["gmv"], row["spend"])),
                "CPA": fmt_money(safe_div(row["spend"], row["purchases"]), 2),
                "CVR": fmt_pct(safe_div(row["purchases"], row["clicks"])),
                "Engaged%": fmt_pct(safe_div(segment_spend.get("engaged", 0.0), total_spend), 0),
                "Existing%": fmt_pct(safe_div(segment_spend.get("existing", 0.0), total_spend), 0),
                "Prosp%": fmt_pct(safe_div(segment_spend.get("prospecting", 0.0), total_spend), 0),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def module_mix_table(df: pd.DataFrame) -> str:
    total_spend = float(df["spend"].sum())
    grouped = (
        df.groupby("module_type", as_index=False)
        .agg(spend=("spend", "sum"), gmv=("purchase_value", "sum"), reach=("reach", "sum"), impressions=("impressions", "sum"))
    )
    grouped["module_type"] = pd.Categorical(grouped["module_type"], categories=MODULE_ORDER + ["其他"], ordered=True)
    grouped = grouped.sort_values("module_type")
    rows = []
    for _, row in grouped.iterrows():
        rows.append(
            {
                "广告类型": row["module_type"],
                "花费": fmt_money(row["spend"]),
                "花费占比": fmt_pct(safe_div(row["spend"], total_spend)),
                "GMV": fmt_money(row["gmv"]),
                "ROAS": fmt_ratio(safe_div(row["gmv"], row["spend"])),
                "触达": fmt_num(row["reach"]),
                "曝光": fmt_num(row["impressions"]),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def buyer_group_mix_table(df: pd.DataFrame) -> str:
    total_spend = float(df["spend"].sum())
    grouped = (
        df.groupby("buyer_group", as_index=False)
        .agg(spend=("spend", "sum"), gmv=("purchase_value", "sum"), reach=("reach", "sum"))
    )
    grouped["buyer_group"] = pd.Categorical(grouped["buyer_group"], categories=BUYER_GROUP_ORDER, ordered=True)
    grouped = grouped.sort_values("buyer_group")
    rows = []
    for _, row in grouped.iterrows():
        rows.append(
            {
                "投手类型": row["buyer_group"],
                "花费": fmt_money(row["spend"]),
                "花费占比": fmt_pct(safe_div(row["spend"], total_spend)),
                "GMV": fmt_money(row["gmv"]),
                "ROAS": fmt_ratio(safe_div(row["gmv"], row["spend"])),
                "触达": fmt_num(row["reach"]),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def buyer_mix_table(df: pd.DataFrame) -> str:
    total_spend = float(df["spend"].sum())
    grouped = (
        df.groupby("buyer", as_index=False)
        .agg(spend=("spend", "sum"), gmv=("purchase_value", "sum"), reach=("reach", "sum"))
    )
    grouped["buyer"] = pd.Categorical(grouped["buyer"], categories=BUYER_ORDER, ordered=True)
    grouped = grouped.sort_values("buyer")
    rows = []
    for _, row in grouped.iterrows():
        rows.append(
            {
                "投手": row["buyer"],
                "花费": fmt_money(row["spend"]),
                "花费占比": fmt_pct(safe_div(row["spend"], total_spend)),
                "GMV": fmt_money(row["gmv"]),
                "ROAS": fmt_ratio(safe_div(row["gmv"], row["spend"])),
                "触达": fmt_num(row["reach"]),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def audience_subsection_table(df: pd.DataFrame, audience: str) -> str:
    adf = df[df["audience_type"] == audience]
    rows = []
    total_spend = float(adf["spend"].sum())
    for segment in SEGMENT_ORDER:
        sdf = adf[adf["user_segment_key"] == segment]
        m = metrics_from_df(sdf)
        rows.append(
            {
                "分层": segment,
                "花费": fmt_money(m.spend),
                "占比": fmt_pct(safe_div(m.spend, total_spend), 0),
                "GMV": fmt_money(m.gmv),
                "ROAS": fmt_ratio(safe_div(m.gmv, m.spend)),
                "CPA": fmt_money(safe_div(m.spend, m.purchases), 2),
                "AOV": fmt_money(safe_div(m.gmv, m.purchases), 2),
                "CVR": fmt_pct(safe_div(m.purchases, m.clicks)),
                "CTR": fmt_pct(safe_div(m.clicks, m.impressions), 2),
                "CPM": fmt_money(safe_div(m.spend * 1000, m.impressions), 3),
                "触达": fmt_num(m.reach),
                "千次触达": fmt_money(safe_div(m.spend * 1000, m.reach), 2),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def compact_segment_table(df: pd.DataFrame) -> str:
    total_spend = float(df["spend"].sum())
    rows = []
    for segment in SEGMENT_ORDER:
        sdf = df[df["user_segment_key"] == segment]
        m = metrics_from_df(sdf)
        rows.append(
            {
                "分层": segment,
                "花费": fmt_money(m.spend),
                "占比": fmt_pct(safe_div(m.spend, total_spend)),
                "GMV": fmt_money(m.gmv),
                "ROAS": fmt_ratio(safe_div(m.gmv, m.spend)),
                "CPA": fmt_money(safe_div(m.spend, m.purchases), 2),
                "CVR": fmt_pct(safe_div(m.purchases, m.clicks)),
                "AOV": fmt_money(safe_div(m.gmv, m.purchases), 2),
                "触达": fmt_num(m.reach),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def compact_audience_table(df: pd.DataFrame, audience: str) -> str:
    adf = df[df["audience_type"] == audience]
    total_spend = float(adf["spend"].sum())
    rows = []
    for segment in SEGMENT_ORDER:
        sdf = adf[adf["user_segment_key"] == segment]
        m = metrics_from_df(sdf)
        rows.append(
            {
                "分层": segment,
                "花费": fmt_money(m.spend),
                "占比": fmt_pct(safe_div(m.spend, total_spend), 0),
                "ROAS": fmt_ratio(safe_div(m.gmv, m.spend)),
                "CPA": fmt_money(safe_div(m.spend, m.purchases), 2),
                "CVR": fmt_pct(safe_div(m.purchases, m.clicks)),
                "AOV": fmt_money(safe_div(m.gmv, m.purchases), 2),
                "触达": fmt_num(m.reach),
            }
        )
    return markdown_table(pd.DataFrame(rows))


def build_report(df: pd.DataFrame, title: str, period: str, source_name: str, analysis_date: str) -> str:
    total = metrics_from_df(df)
    min_date = pd.to_datetime(df["date_start"]).min()
    max_date = pd.to_datetime(df["date_stop"]).max()
    total_days = int((max_date - min_date).days) + 1
    overall_lines = [
        f"# {title}",
        "",
        f"**数据周期**: {period}",
        f"**数据来源**: `{source_name}`",
        f"**分析日期**: {analysis_date}",
        "",
        "---",
        "",
        "## 一、整体概况",
        "",
        f"数据天数: {total_days}天 | 日均花费: {fmt_money(safe_div(total.spend, total_days))}",
        f"总花费: {fmt_money(total.spend)} | 总GMV: {fmt_money(total.gmv)} | 总ROAS: {fmt_ratio(safe_div(total.gmv, total.spend))} | 总CPA: {fmt_money(safe_div(total.spend, total.purchases), 2)} | 总CVR: {fmt_pct(safe_div(total.purchases, total.clicks))}",
        f"总触达: {fmt_num(total.reach)} | 总展示: {fmt_num(total.impressions)} | 触达率: {fmt_pct(safe_div(total.reach, total.impressions))} | 千次触达花费: {fmt_money(safe_div(total.spend * 1000, total.reach), 2)}",
        "",
        segment_table(df),
        "",
        "---",
        "",
        "## 二、广告类型 × 用户分层",
        "",
    ]

    sections = []
    module_map = {
        "收割广告": df[df["module_type"] == "收割广告"],
        "合创广告": df[df["module_type"] == "合创广告"],
        "合创广告（过滤后：有目录且非无目录）": df[(df["module_type"] == "合创广告") & (df["g2g_subtype"] == "转化帖子")],
        "混合目录": df[df["module_type"] == "混合目录"],
    }
    for name, sdf in module_map.items():
        sections.extend(
            [
                f"### {name}",
                build_summary_line(sdf),
                "",
                detailed_segment_table(sdf),
                "",
            ]
        )

    sections.extend(
        [
            "---",
            "",
            "## 三、投手 × 用户分层",
            "",
        ]
    )

    for buyer_group in BUYER_GROUP_ORDER:
        gdf = df[df["buyer_group"] == buyer_group]
        if gdf.empty:
            continue
        sections.extend(
            [
                f"### {buyer_group}",
                build_summary_line(gdf),
                "",
                detailed_segment_table(gdf),
                "",
            ]
        )

    sections.extend(["### 各投手", ""])
    for buyer in BUYER_ORDER:
        bdf = df[df["buyer"] == buyer]
        if bdf.empty:
            continue
        sections.extend(
            [
                f"#### {buyer}",
                build_summary_line(bdf),
                "",
                detailed_segment_table(bdf),
                "",
            ]
        )

    sections.extend(["---", "", "## 四、广告类型 × 受众 × 用户分层", ""])

    for name in ["收割广告", "合创广告", "混合目录"]:
        sdf = df[df["module_type"] == name]
        sections.extend([f"### {name} — Cold/Warm × 用户分层", ""])
        for audience, label in [("cold", "Cold (新客)"), ("warm", "Warm (再营销)")]:
            adf = sdf[sdf["audience_type"] == audience]
            if adf["spend"].sum() <= 0:
                continue
            sections.extend(
                [
                    f"**{label}**",
                    build_summary_line_with_media(adf),
                    "",
                    audience_subsection_table(sdf, audience),
                    "",
                ]
            )

    harvest_df = df[df["module_type"] == "收割广告"]
    cocreate_df = df[df["module_type"] == "合创广告"]
    cocreate_filtered_df = df[(df["module_type"] == "合创广告") & (df["g2g_subtype"] == "转化帖子")]
    mixed_df = df[df["module_type"] == "混合目录"]

    sections.extend(
        [
            "---",
            "",
            "## 五、收割广告 TOP15 产品详情",
            "",
            top_products_mix_table(harvest_df),
            "",
            "---",
            "",
            "## 六、合创广告（过滤后）— TOP15 产品 × 用户分层",
            "",
            f"过滤前花费: {fmt_money(cocreate_df['spend'].sum())} → 过滤后花费: {fmt_money(cocreate_filtered_df['spend'].sum())} ({fmt_pct(safe_div(cocreate_filtered_df['spend'].sum(), cocreate_df['spend'].sum()), 0)})",
            "",
            filtered_products_mix_table(cocreate_filtered_df),
            "",
            "---",
            "",
            "## 七、混合目录 — 完整人群分层",
            "",
            build_summary_line_with_media(mixed_df).replace(" | CPM:", f" | AOV: {fmt_money(safe_div(metrics_from_df(mixed_df).gmv, metrics_from_df(mixed_df).purchases), 2)} | CTR: {fmt_pct(safe_div(metrics_from_df(mixed_df).clicks, metrics_from_df(mixed_df).impressions), 2)} | CPM:"),
            "",
            compact_segment_table(mixed_df),
            "",
        ]
    )

    for audience, label in [("cold", "Cold (新客)"), ("warm", "Warm (再营销)")]:
        adf = mixed_df[mixed_df["audience_type"] == audience]
        if adf["spend"].sum() <= 0:
            continue
        sections.extend(
            [
                f"**{label}** | 花费: {fmt_money(adf['spend'].sum())} ({fmt_pct(safe_div(adf['spend'].sum(), mixed_df['spend'].sum()), 0)}) | ROAS: {fmt_ratio(safe_div(adf['purchase_value'].sum(), adf['spend'].sum()))} | CPA: {fmt_money(safe_div(adf['spend'].sum(), adf['purchase_count'].sum()), 2)} | CVR: {fmt_pct(safe_div(adf['purchase_count'].sum(), adf['clicks_link'].sum()))} | CPM: {fmt_money(safe_div(adf['spend'].sum() * 1000, adf['impressions'].sum()), 3)} | 触达: {fmt_num(adf['reach'].sum())}",
                "",
                compact_audience_table(mixed_df, audience),
                "",
            ]
        )

    sections.extend(
        [
            "---",
            "",
            "## 八、花费结构总览",
            "",
            "### 按广告类型",
            "",
            module_mix_table(df),
            "",
            "### 按投手类型",
            "",
            buyer_group_mix_table(df),
            "",
            "### 各投手",
            "",
            buyer_mix_table(df),
            "",
        ]
    )

    return "\n".join(overall_lines + sections)


def infer_output_path(args: argparse.Namespace, df: pd.DataFrame) -> Path:
    if args.output:
        return Path(args.output)

    min_date = pd.to_datetime(df["date_start"]).min().date()
    max_date = pd.to_datetime(df["date_stop"]).max().date()

    is_full_month = (
        min_date.day == 1
        and min_date.year == max_date.year
        and min_date.month == max_date.month
        and (max_date + pd.Timedelta(days=1)).day == 1
    )

    if is_full_month:
        filename = f"user_segment_analysis_{min_date.strftime('%Y-%m')}.md"
    else:
        filename = f"user_segment_analysis_{min_date.strftime('%Y-%m-%d')}_to_{max_date.strftime('%Y-%m-%d')}.md"

    return Path(args.input).resolve().parent / filename


def main() -> None:
    args = parse_args()
    buyer_rules, buyer_groups = load_buyer_mapping(args.buyer_mapping)
    input_path = Path(args.input)
    df = load_data(input_path, buyer_rules, buyer_groups)
    output_path = infer_output_path(args, df)
    report = build_report(df, args.title, args.period, args.source_name, args.analysis_date)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote report to {output_path}")


if __name__ == "__main__":
    main()
