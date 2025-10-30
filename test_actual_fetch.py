"""
Test actual data fetching with the new FX business days filtering
"""

import json
from src.fx_kline.core.data_fetcher import fetch_single_ohlc
from src.fx_kline.core.models import OHLCRequest
from src.fx_kline.core.data_fetcher import fetch_batch_ohlc_sync

def test_single_fetch():
    """Test single data fetch scenarios"""
    print("=" * 60)
    print("Test 1: 1-hour interval, 5 days (original issue)")
    print("=" * 60)

    # Test the original issue: 1h interval, 5d period
    ohlc_data, error = fetch_single_ohlc(
        pair="USDJPY",
        interval="1h",
        period="5d",
        exclude_weekends=True
    )

    if error:
        print(f"[ERROR] {error.error_message}")
    else:
        print(f"[SUCCESS]")
        print(f"  Pair: {ohlc_data.pair}")
        print(f"  Interval: {ohlc_data.interval}")
        print(f"  Period: {ohlc_data.period}")
        print(f"  Data count: {ohlc_data.data_count}")

        # Count data by day of week
        from datetime import datetime
        day_counts = {}
        for row in ohlc_data.rows:
            dt_str = row['Datetime']
            # Parse datetime (format: "2025-10-30 09:00:00 JST")
            dt = datetime.strptime(dt_str[:19], '%Y-%m-%d %H:%M:%S')
            day_name = dt.strftime('%A')
            day_counts[day_name] = day_counts.get(day_name, 0) + 1

        print(f"\n  Data distribution by day:")
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day in day_counts:
                print(f"    {day}: {day_counts[day]} rows")

        # Show first and last 3 rows
        print(f"\n  First 3 rows:")
        for row in ohlc_data.rows[:3]:
            print(f"    {row['Datetime']}: O={row['Open']:.2f}")

        print(f"\n  Last 3 rows:")
        for row in ohlc_data.rows[-3:]:
            print(f"    {row['Datetime']}: O={row['Open']:.2f}")

        # Check for Saturday data
        saturday_rows = [r for r in ohlc_data.rows if 'Saturday' in datetime.strptime(r['Datetime'][:19], '%Y-%m-%d %H:%M:%S').strftime('%A')]
        if saturday_rows:
            print(f"\n  Saturday data found: {len(saturday_rows)} rows")
            print(f"  Saturday times:")
            for row in saturday_rows[:10]:  # Show first 10
                dt = datetime.strptime(row['Datetime'][:19], '%Y-%m-%d %H:%M:%S')
                print(f"    {dt.strftime('%Y-%m-%d %H:%M (%A)')}")

    print("\n")

    # Test 15-minute interval, 1 day
    print("=" * 60)
    print("Test 2: 15-minute interval, 1 day (original issue)")
    print("=" * 60)

    ohlc_data, error = fetch_single_ohlc(
        pair="USDJPY",
        interval="15m",
        period="1d",
        exclude_weekends=True
    )

    if error:
        print(f"[ERROR] {error.error_message}")
    else:
        print(f"[SUCCESS]")
        print(f"  Data count: {ohlc_data.data_count}")
        print(f"  First row: {ohlc_data.rows[0]['Datetime']}")
        print(f"  Last row: {ohlc_data.rows[-1]['Datetime']}")

    print("\n")

    # Test 1-day interval, 20 days
    print("=" * 60)
    print("Test 3: 1-day interval, 20 days (should work as before)")
    print("=" * 60)

    ohlc_data, error = fetch_single_ohlc(
        pair="USDJPY",
        interval="1d",
        period="20d",
        exclude_weekends=True
    )

    if error:
        print(f"[ERROR] {error.error_message}")
    else:
        print(f"[SUCCESS]")
        print(f"  Data count: {ohlc_data.data_count}")
        print(f"  First row: {ohlc_data.rows[0]['Datetime']}")
        print(f"  Last row: {ohlc_data.rows[-1]['Datetime']}")

        # Check no Saturday/Sunday data for daily interval
        weekend_rows = []
        for row in ohlc_data.rows:
            dt = datetime.strptime(row['Datetime'][:19], '%Y-%m-%d %H:%M:%S')
            day_name = dt.strftime('%A')
            if day_name in ['Saturday', 'Sunday']:
                weekend_rows.append(row)

        if weekend_rows:
            print(f"  [WARNING] Weekend data found (should be empty): {len(weekend_rows)} rows")
        else:
            print(f"  [OK] No weekend data (as expected for daily interval)")

    print("\n")


def test_batch_fetch():
    """Test batch fetching"""
    print("=" * 60)
    print("Test 4: Batch fetch (multiple pairs and intervals)")
    print("=" * 60)

    requests = [
        OHLCRequest(pair="USDJPY", interval="1h", period="5d"),
        OHLCRequest(pair="EURUSD", interval="1h", period="5d"),
        OHLCRequest(pair="USDJPY", interval="15m", period="1d"),
    ]

    response = fetch_batch_ohlc_sync(requests, exclude_weekends=True)

    print(f"Total requested: {response.total_requested}")
    print(f"Total succeeded: {response.total_succeeded}")
    print(f"Total failed: {response.total_failed}")

    print(f"\nSuccessful fetches:")
    for ohlc in response.successful:
        print(f"  {ohlc.pair} {ohlc.interval} {ohlc.period}: {ohlc.data_count} rows")

    if response.failed:
        print(f"\nFailed fetches:")
        for err in response.failed:
            print(f"  {err.pair} {err.interval} {err.period}: {err.error_message}")

    print("\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Actual Data Fetch Tests")
    print("=" * 60)
    print()

    try:
        test_single_fetch()
        test_batch_fetch()

        print("=" * 60)
        print("All data fetch tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAILED] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
