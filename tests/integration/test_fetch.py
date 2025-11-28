#!/usr/bin/env python3
"""
Simple test script to verify data fetching works
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fx_kline.core import OHLCRequest, fetch_batch_ohlc_sync, get_preset_pairs  # type: ignore
from datetime import datetime

def test_simple_fetch():
    """Test a simple fetch"""
    print("=" * 60)
    print("FX-Kline Data Fetch Test")
    print("=" * 60)

    # Create a simple request
    requests = [
        OHLCRequest(pair="USDJPY", interval="1h", period="1d"),
        OHLCRequest(pair="EURUSD", interval="1h", period="1d"),
    ]

    print("\nRequesting data for:")
    for req in requests:
        print(f"  - {req.pair} ({req.interval} / {req.period})")

    print("\nFetching data... (this may take a moment)")

    # Fetch data
    response = fetch_batch_ohlc_sync(requests)

    # Display results
    print(f"\nResults:")
    print(f"  Total Requested: {response.total_requested}")
    print(f"  Total Succeeded: {response.total_succeeded}")
    print(f"  Total Failed: {response.total_failed}")

    # Display successful data
    if response.successful:
        print(f"\nSuccessful fetches:")
        for ohlc in response.successful:
            print(f"\n  {ohlc.pair} ({ohlc.interval} / {ohlc.period})")
            print(f"    Data points: {ohlc.data_count}")
            if ohlc.rows:
                print(f"    Date range: {ohlc.rows[0]['Datetime']} to {ohlc.rows[-1]['Datetime']}")
                print(f"    First row:")
                first = ohlc.rows[0]
                print(f"      Datetime: {first['Datetime']}")
                print(f"      Open: {first['Open']}")
                print(f"      High: {first['High']}")
                print(f"      Low: {first['Low']}")
                print(f"      Close: {first['Close']}")

    # Display failed data
    if response.failed:
        print(f"\nFailed fetches:")
        for err in response.failed:
            print(f"\n  {err.pair} ({err.interval} / {err.period})")
            print(f"    Error: {err.error_type}")
            print(f"    Message: {err.error_message}")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_simple_fetch()
