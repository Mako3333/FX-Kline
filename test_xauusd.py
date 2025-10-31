#!/usr/bin/env python3
"""
Test XAUUSD data fetching after fix
Verifies that XAUUSD works with multiple intervals and periods
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fx_kline.core import OHLCRequest, fetch_batch_ohlc_sync

def test_xauusd_fetch():
    """Test XAUUSD data fetching with the error cases from the report"""
    print("=" * 70)
    print("XAUUSD Data Fetch Test (After Fix)")
    print("=" * 70)
    print()

    # Test cases matching the original error report
    test_cases = [
        ("1h", "5d"),
        ("15m", "2d"),
        ("1d", "20d"),
    ]

    requests = [
        OHLCRequest(pair="XAUUSD", interval=interval, period=period)
        for interval, period in test_cases
    ]

    print("Testing XAUUSD with the following configurations:")
    for req in requests:
        print(f"  - {req.pair} ({req.interval} / {req.period})")
    print()

    print("Fetching data... (this may take a moment)")
    print()

    # Fetch data
    response = fetch_batch_ohlc_sync(requests, exclude_weekends=True)

    # Display results
    print(f"Results:")
    print(f"  Total Requested: {response.total_requested}")
    print(f"  Total Succeeded: {response.total_succeeded}")
    print(f"  Total Failed: {response.total_failed}")
    print()

    # Display successful data
    if response.successful:
        print("✅ Successful fetches:")
        for ohlc in response.successful:
            print(f"\n  {ohlc.pair} ({ohlc.interval} / {ohlc.period})")
            print(f"    Data points: {ohlc.data_count}")
            if ohlc.rows:
                print(f"    Date range: {ohlc.rows[0]['Datetime']} to {ohlc.rows[-1]['Datetime']}")
                print(f"    First row:")
                first = ohlc.rows[0]
                print(f"      Datetime: {first['Datetime']}")
                print(f"      Open: ${first['Open']:.2f}")
                print(f"      High: ${first['High']:.2f}")
                print(f"      Low: ${first['Low']:.2f}")
                print(f"      Close: ${first['Close']:.2f}")
                print(f"    Last row:")
                last = ohlc.rows[-1]
                print(f"      Datetime: {last['Datetime']}")
                print(f"      Close: ${last['Close']:.2f}")

    # Display failed data
    if response.failed:
        print("\n❌ Failed fetches:")
        for err in response.failed:
            print(f"\n  {err.pair} ({err.interval} / {err.period})")
            print(f"    Error Type: {err.error_type}")
            print(f"    Message: {err.error_message}")

    print("\n" + "=" * 70)
    if response.total_failed == 0:
        print("✅ All XAUUSD tests passed!")
    else:
        print(f"❌ {response.total_failed} test(s) failed")
    print("=" * 70)
    print()

    return response.total_failed == 0


if __name__ == "__main__":
    success = test_xauusd_fetch()
    sys.exit(0 if success else 1)

