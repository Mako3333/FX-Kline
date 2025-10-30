"""
Test script for FX business days filtering with DST support
"""

import pandas as pd
import pytz
from datetime import datetime
from src.fx_kline.core.business_days import (
    is_combined_dst_active,
    get_fx_market_close_hour_jst,
    filter_business_days_fx
)

JST_TZ = pytz.timezone('Asia/Tokyo')

def test_dst_detection():
    """Test DST detection for different dates"""
    print("=" * 60)
    print("DST Detection Tests")
    print("=" * 60)

    test_dates = [
        # Winter (January)
        datetime(2025, 1, 15, 12, 0, 0, tzinfo=JST_TZ),
        # Spring transition (March - before DST)
        datetime(2025, 3, 15, 12, 0, 0, tzinfo=JST_TZ),
        # Summer (July)
        datetime(2025, 7, 15, 12, 0, 0, tzinfo=JST_TZ),
        # Fall transition (November - after DST)
        datetime(2025, 11, 15, 12, 0, 0, tzinfo=JST_TZ),
        # Current date
        datetime.now(JST_TZ),
    ]

    for dt in test_dates:
        is_dst = is_combined_dst_active(dt)
        close_hour = get_fx_market_close_hour_jst(dt)
        print(f"{dt.strftime('%Y-%m-%d %H:%M %Z')}: DST={is_dst}, Close Hour={close_hour}:00 JST")

    print()


def test_fx_trading_time_filter():
    """Test FX trading time filtering for intraday data"""
    print("=" * 60)
    print("FX Trading Time Filter Tests (1h interval)")
    print("=" * 60)

    # Create test data spanning a weekend
    # Friday 20:00 to Monday 10:00
    dates = pd.date_range(
        start='2025-10-24 20:00:00',  # Friday evening
        end='2025-10-27 10:00:00',    # Monday morning
        freq='1h',
        tz='Asia/Tokyo'
    )

    df = pd.DataFrame({
        'Open': range(len(dates)),
        'High': range(len(dates)),
        'Low': range(len(dates)),
        'Close': range(len(dates)),
    }, index=dates)

    print(f"Original data points: {len(df)}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print("\nSample data around weekend:")
    print(df.to_string())

    # Apply FX trading time filter
    df_filtered = filter_business_days_fx(df, '1h')

    print(f"\n\nFiltered data points: {len(df_filtered)}")
    print(f"Removed: {len(df) - len(df_filtered)} rows")
    print("\nFiltered data:")
    print(df_filtered.to_string())

    # Check for Saturday morning data
    saturday_data = df_filtered[df_filtered.index.dayofweek == 5]
    print(f"\n\nSaturday data retained: {len(saturday_data)} rows")
    if len(saturday_data) > 0:
        print("Saturday hours retained:")
        for idx in saturday_data.index:
            print(f"  {idx.strftime('%Y-%m-%d %H:%M %A')}")

    print()


def test_daily_vs_intraday_filtering():
    """Compare filtering behavior for daily vs intraday intervals"""
    print("=" * 60)
    print("Daily vs Intraday Filtering Comparison")
    print("=" * 60)

    # Create test data with Saturday morning hours
    dates = pd.date_range(
        start='2025-10-25 00:00:00',  # Saturday midnight
        end='2025-10-25 10:00:00',    # Saturday 10:00
        freq='1h',
        tz='Asia/Tokyo'
    )

    df = pd.DataFrame({
        'Open': range(len(dates)),
        'High': range(len(dates)),
        'Low': range(len(dates)),
        'Close': range(len(dates)),
    }, index=dates)

    print(f"Test data: Saturday {dates[0]} to {dates[-1]}")
    print(f"Total data points: {len(df)}")

    # Test with different intervals
    intervals_to_test = ['1h', '15m', '1d']

    for interval in intervals_to_test:
        df_filtered = filter_business_days_fx(df, interval)
        close_hour = get_fx_market_close_hour_jst()

        print(f"\nInterval: {interval}")
        print(f"  Market close hour: {close_hour}:00 JST")
        print(f"  Filtered rows: {len(df_filtered)}")

        if len(df_filtered) > 0:
            print(f"  Hours retained: {[idx.hour for idx in df_filtered.index]}")
        else:
            print(f"  All Saturday data filtered out (expected for daily interval)")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FX Business Days Filtering - Comprehensive Test Suite")
    print("=" * 60)
    print()

    try:
        # Run all tests
        test_dst_detection()
        test_fx_trading_time_filter()
        test_daily_vs_intraday_filtering()

        print("=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
