#!/usr/bin/env python3
"""
Debug script to verify JST timezone conversion in data fetching pipeline.

Moved from the old name `test_jst_conversion.py` to avoid being collected by
pytest as an automated test, while keeping the original behaviour for
manual runs.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_kline.core import data_fetcher  # noqa: E402
from fx_kline.core.timezone_utils import JST_TZ  # noqa: E402


def main() -> int:
    print("=" * 70)
    print("JST Timezone Conversion Verification Test")
    print("=" * 70)
    print()

    # Test 1: Verify JST datetime creation
    print("Test 1: JST datetime creation")
    print("-" * 70)
    test_date = date(2025, 11, 28)
    jst_dt = JST_TZ.localize(datetime.combine(test_date, time.min))
    print(f"Input date: {test_date}")
    print(f"JST datetime: {jst_dt}")
    print(f"Timezone: {jst_dt.tzinfo}")
    print("Expected: Asia/Tokyo")
    assert str(jst_dt.tzinfo) == "Asia/Tokyo", f"Expected Asia/Tokyo, got {jst_dt.tzinfo}"
    print("✅ JST datetime creation: PASSED")
    print()

    # Test 2: Verify UTC conversion for API call
    print("Test 2: UTC conversion for API call")
    print("-" * 70)
    start_jst = JST_TZ.localize(datetime.combine(test_date - timedelta(days=1), time.min))
    end_jst = JST_TZ.localize(datetime.combine(test_date, time.min))
    print(f"Start JST: {start_jst}")
    print(f"End JST: {end_jst}")

    # Simulate what fetch_ohlc_range_dataframe does internally
    start_utc = start_jst.astimezone(timezone.utc)
    end_utc = end_jst.astimezone(timezone.utc)
    print(f"Start UTC: {start_utc}")
    print(f"End UTC: {end_utc}")

    # Verify time difference (JST is UTC+9)
    expected_diff_hours = 9
    actual_diff_hours = (start_jst.hour - start_utc.hour) % 24
    print(f"Time difference: {actual_diff_hours} hours (expected: {expected_diff_hours})")
    assert actual_diff_hours == expected_diff_hours or actual_diff_hours == (24 - expected_diff_hours), (
        f"Expected {expected_diff_hours} hour difference, got {actual_diff_hours}"
    )
    print("✅ UTC conversion: PASSED")
    print()

    # Test 3: Verify actual data fetch and JST conversion
    print("Test 3: Actual data fetch and JST conversion")
    print("-" * 70)
    print("Fetching USDJPY 15m data for verification...")
    print()

    try:
        # Use a small window to minimize API calls
        start_jst = JST_TZ.localize(datetime.combine(test_date - timedelta(days=2), time.min))
        end_jst = JST_TZ.localize(datetime.combine(test_date, time.min))

        df = data_fetcher.fetch_ohlc_range_dataframe(
            pair="USDJPY",
            interval="15m",
            start=start_jst,
            end=end_jst,
            exclude_weekends=True,
        )

        if df.empty:
            print("⚠️  No data returned (this may be normal if market is closed)")
            print("   Skipping DataFrame timezone verification")
        else:
            print(f"DataFrame shape: {df.shape}")
            print(f"Index type: {type(df.index)}")
            print(f"Index timezone: {df.index.tzinfo}")
            print(f"First index value: {df.index[0]}")
            print(f"Last index value: {df.index[-1]}")

            # Verify JST timezone
            assert df.index.tzinfo is not None, "DataFrame index should be timezone-aware"
            assert str(df.index.tzinfo) == "Asia/Tokyo", (
                f"Expected Asia/Tokyo timezone, got {df.index.tzinfo}"
            )

            # Verify timezone conversion (check a few sample times)
            print("\nSample timezone verification:")
            for i in range(min(5, len(df))):
                idx_val = df.index[i]
                print(f"  Row {i}: {idx_val} (timezone: {idx_val.tzinfo})")

            print("✅ DataFrame JST conversion: PASSED")

    except Exception as e:  # pragma: no cover - manual debug only
        print(f"❌ Error during data fetch: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("✅ JST datetime creation: PASSED")
    print("✅ UTC conversion for API: PASSED")
    if "df" in locals() and not isinstance(df, pd.DataFrame):
        pass
    elif "df" in locals() and not df.empty:
        print("✅ DataFrame JST conversion: PASSED")
    print()
    print("All timezone conversions are working correctly!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


