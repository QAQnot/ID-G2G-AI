import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


GRAPH_API_BASE = "https://graph.facebook.com"


def get_segment_value(items: Iterable[Dict[str, Any]], action_type: str) -> Optional[str]:
    for item in items:
        if item.get("action_type") == action_type:
            return item.get("value")
    return None


def get_first_segment_value(items: Iterable[Dict[str, Any]], action_types: Iterable[str]) -> Optional[str]:
    for action_type in action_types:
        value = get_segment_value(items, action_type)
        if value not in (None, ""):
            return value
    return None


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def parse_accounts(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_params(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "level": args.level,
        "fields": ",".join(
            [
                "account_name",
                "account_id",
                "campaign_name",
                "adset_name",
                "ad_name",
                "spend",
                "reach",
                "impressions",
                "inline_link_clicks",
                "catalog_segment_actions",
                "catalog_segment_value",
            ]
        ),
        "breakdowns": "user_segment_key",
        "time_range": json.dumps({"since": args.since, "until": args.until}, separators=(",", ":")),
        "limit": args.page_limit,
        "access_token": args.access_token,
    }


def build_proxies(args: argparse.Namespace) -> Dict[str, str]:
    proxies: Dict[str, str] = {}
    if args.http_proxy:
        proxies["http"] = args.http_proxy
    if args.https_proxy:
        proxies["https"] = args.https_proxy
    return proxies


def fetch_account(session: requests.Session, ad_account_id: str, args: argparse.Namespace) -> List[Dict[str, Any]]:
    url = f"{GRAPH_API_BASE}/{args.api_version}/{ad_account_id}/insights"
    params = build_params(args)
    all_rows: List[Dict[str, Any]] = []
    wait_seconds = args.rate_limit_initial_wait_seconds

    while url:
        response = session.get(
            url,
            params=params,
            timeout=args.request_timeout,
            proxies=build_proxies(args),
        )
        params = None

        if response.status_code == 200:
            payload = response.json()
            all_rows.extend(payload.get("data", []))
            url = payload.get("paging", {}).get("next")
            wait_seconds = args.rate_limit_initial_wait_seconds
            if url:
                time.sleep(args.page_request_delay_seconds)
            continue

        try:
            error_payload = response.json()
        except ValueError:
            response.raise_for_status()

        error = error_payload.get("error", {})
        code = error.get("code")
        message = error.get("message", "Unknown error")
        if code in {4, 17, 32, 613, 80003, 80004}:
            time.sleep(wait_seconds)
            wait_seconds = min(wait_seconds * 2, args.rate_limit_max_wait_seconds)
            continue

        raise RuntimeError(f"{ad_account_id} request failed: code={code}, message={message}")

    return all_rows


def transform_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for item in rows:
        output.append(
            {
                "date_start": item.get("date_start"),
                "date_stop": item.get("date_stop"),
                "account_name": item.get("account_name"),
                "account_id": item.get("account_id"),
                "campaign_name": item.get("campaign_name"),
                "adset_name": item.get("adset_name"),
                "ad_name": item.get("ad_name"),
                "user_segment_key": item.get("user_segment_key"),
                "spend": as_float(item.get("spend")),
                "reach": as_int(item.get("reach")),
                "impressions": as_int(item.get("impressions")),
                "clicks_link": as_int(item.get("inline_link_clicks")),
                "purchase_count": as_int(
                    get_first_segment_value(
                        item.get("catalog_segment_actions", []),
                        ["purchase", "onsite_app_purchase", "app_custom_event.fb_mobile_purchase"],
                    )
                ),
                "purchase_value": as_float(
                    get_first_segment_value(
                        item.get("catalog_segment_value", []),
                        ["purchase", "onsite_app_purchase", "app_custom_event.fb_mobile_purchase"],
                    )
                ),
                "add_to_cart_value": as_float(
                    get_first_segment_value(
                        item.get("catalog_segment_value", []),
                        ["add_to_cart", "onsite_app_add_to_cart", "app_custom_event.fb_mobile_add_to_cart"],
                    )
                ),
            }
        )
    return output


def write_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date_start",
        "date_stop",
        "account_name",
        "account_id",
        "campaign_name",
        "adset_name",
        "ad_name",
        "user_segment_key",
        "spend",
        "reach",
        "impressions",
        "clicks_link",
        "purchase_count",
        "purchase_value",
        "add_to_cart_value",
    ]
    with output_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Meta user segment insights for one or more ad accounts.")
    parser.add_argument("--access-token", required=True, help="Meta Graph API access token.")
    parser.add_argument("--accounts", required=True, help="Comma-separated ad account IDs like act_123,act_456")
    parser.add_argument("--since", required=True, help="Start date in YYYY-MM-DD")
    parser.add_argument("--until", required=True, help="End date in YYYY-MM-DD")
    parser.add_argument("--output", type=Path, required=True, help="CSV output path")
    parser.add_argument("--api-version", default="v23.0", help="Graph API version")
    parser.add_argument("--level", default="ad", choices=["campaign", "adset", "ad"])
    parser.add_argument("--request-timeout", type=int, default=60)
    parser.add_argument("--page-limit", type=int, default=500)
    parser.add_argument("--min-request-interval-seconds", type=float, default=1.0)
    parser.add_argument("--page-request-delay-seconds", type=float, default=0.5)
    parser.add_argument("--rate-limit-initial-wait-seconds", type=float, default=60.0)
    parser.add_argument("--rate-limit-max-wait-seconds", type=float, default=600.0)
    parser.add_argument("--http-proxy", default=None)
    parser.add_argument("--https-proxy", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    accounts = parse_accounts(args.accounts)
    session = requests.Session()
    raw_rows: List[Dict[str, Any]] = []
    failures: List[Dict[str, str]] = []

    for index, ad_account_id in enumerate(accounts, start=1):
        print(f"[{index}/{len(accounts)}] Fetching {ad_account_id} ...")
        try:
            rows = fetch_account(session, ad_account_id, args)
            print(f"  Retrieved {len(rows)} rows from {ad_account_id}")
            raw_rows.extend(rows)
        except Exception as exc:
            print(f"  Failed {ad_account_id}: {exc}")
            failures.append({"ad_account_id": ad_account_id, "error": str(exc)})
        time.sleep(args.min_request_interval_seconds)

    transformed = transform_rows(raw_rows)
    write_csv(transformed, args.output)
    print(f"Wrote {len(transformed)} rows to {args.output}")

    if failures:
        error_path = args.output.with_name(f"{args.output.stem}_errors.json")
        error_path.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {len(failures)} account errors to {error_path}")


if __name__ == "__main__":
    main()
