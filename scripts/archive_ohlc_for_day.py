#!/usr/bin/env python3
"""
Archive previous-day 15m OHLC into data/YYYY/MM/DD/ohlc/.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_kline.analyst import data_manager  # noqa: E402
from fx_kline.core import data_fetcher  # noqa: E402
from fx_kline.core.business_days import is_business_day  # noqa: E402
from fx_kline.core.timezone_utils import JST_TZ  # noqa: E402
from fx_kline.core.validators import get_preset_pairs  # noqa: E402

DEFAULT_PAIRS = ["USDJPY", "EURUSD", "AUDJPY", "AUDUSD", "EURJPY", "XAUUSD"]
DEFAULT_TIMEFRAME = "15m"


def _parse_market_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _default_pairs() -> list[str]:
    env_pairs = os.environ.get("PAIRS")
    if env_pairs:
        return env_pairs.split()
    # Fall back to the preset list but keep parity with the current workflow defaults
    preset = get_preset_pairs()
    return [p for p in DEFAULT_PAIRS if p in preset] or preset


def _jst_datetime(day: date) -> datetime:
    """Create a JST datetime for the start of the given date."""
    return JST_TZ.localize(datetime.combine(day, time.min))


def archive_for_target_date(market_date: date, pairs: list[str], timeframe: str = DEFAULT_TIMEFRAME) -> None:
    target_date = market_date - timedelta(days=1)
    
    # Adjust target_date to previous business day if it falls on a weekend
    # This prevents attempting to archive weekend data when exclude_weekends=True
    target_datetime = _jst_datetime(target_date)
    if not is_business_day(target_datetime):
        # If Saturday (5), go back 1 day; if Sunday (6), go back 2 days
        days_back = 2 if target_date.weekday() == 6 else 1
        target_date = target_date - timedelta(days=days_back)
        print(f"[INFO] Adjusted target_date to previous business day: {target_date}")
    
    start_jst = _jst_datetime(target_date - timedelta(days=1))
    end_jst = _jst_datetime(market_date)

    for pair in pairs:
        try:
            df = data_fetcher.fetch_ohlc_range_dataframe(
                pair=pair,
                interval=timeframe,
                start=start_jst,
                end=end_jst,
                exclude_weekends=True,
            )
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[WARN] Failed to fetch {pair} {timeframe} data: {exc}")
            continue

        if df.empty:
            print(f"[WARN] No data returned for {pair} {timeframe} in window {start_jst} - {end_jst}")
            continue

        # Restrict to the target day in JST
        df_target = df[df.index.date == target_date]
        if df_target.empty:
            print(f"[WARN] No {timeframe} data for {pair} on target date {target_date}")
            continue

        df_target = df_target.rename(columns=str.lower)
        df_target.index.name = "datetime"

        out_path = data_manager.get_daily_ohlc_filepath(target_date, pair, timeframe)
        df_target.to_csv(out_path, index=True)
        print(f"[OK] Archived {pair} {timeframe} -> {out_path}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Archive previous-day 15m OHLC into data/YYYY/MM/DD/ohlc/"
    )
    parser.add_argument(
        "--market-date",
        required=True,
        help="Market date in YYYY-MM-DD (JST). Target day is market-date - 1 day.",
    )
    parser.add_argument(
        "--pairs",
        nargs="+",
        help="Optional override for currency pairs (default: workflow preset).",
    )
    parser.add_argument(
        "--timeframe",
        default=DEFAULT_TIMEFRAME,
        help="Timeframe to fetch (default: 15m).",
    )

    args = parser.parse_args(argv)

    market_date = _parse_market_date(args.market_date)
    pairs = args.pairs if args.pairs else _default_pairs()
    archive_for_target_date(market_date, pairs, timeframe=args.timeframe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
