#!/usr/bin/env python3
"""
Test other currency pairs (USDJPY, EURUSD) to verify they still work
after the XAUUSD fix
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fx_kline.core import OHLCRequest, fetch_batch_ohlc_sync

def test_other_pairs():
    """Test that other currency pairs still work after XAUUSD fix"""
    print("=" * 70)
    print("Other Currency Pairs Verification Test")
    print("=" * 70)
    print()

    # Test with longer periods to avoid weekend filtering issues
    requests = [
        OHLCRequest(pair="USDJPY", interval="1h", period="5d"),
        OHLCRequest(pair="EURUSD", interval="1h", period="5d"),
        OHLCRequest(pair="GBPUSD", interval="15m", period="2d"),
    ]

    print("Testing other currency pairs:")
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
                print(f"    First row Close: {ohlc.rows[0]['Close']}")
                print(f"    Last row Close: {ohlc.rows[-1]['Close']}")

    # Display failed data
    if response.failed:
        print("\n❌ Failed fetches:")
        for err in response.failed:
            print(f"\n  {err.pair} ({err.interval} / {err.period})")
            print(f"    Error Type: {err.error_type}")
            print(f"    Message: {err.error_message}")

    print("\n" + "=" * 70)
    if response.total_failed == 0:
        print("✅ All other currency pair tests passed!")
        print("   The XAUUSD fix did not break other pairs.")
    else:
        print(f"⚠️  {response.total_failed} test(s) failed")
        print("   This may be a pre-existing issue or needs investigation.")
    print("=" * 70)
    print()

    return response.total_failed == 0


if __name__ == "__main__":
    success = test_other_pairs()
    sys.exit(0 if success else 1)

