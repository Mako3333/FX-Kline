"""
Test to investigate the issue when fetching 3 intervals simultaneously
Specifically: 1h/5d + 15m/1d + 1d/20d causes hourly data to have only 5 rows
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fx_kline.core import fetch_batch_ohlc_sync, OHLCRequest
from datetime import datetime

def test_2_vs_3_fetch():
    """Compare fetching 2 intervals vs 3 intervals"""
    print("=" * 70)
    print("INVESTIGATING 3-FETCH ISSUE")
    print("=" * 70)

    # Test 1: Fetch 2 intervals (1h + 15m) - Should work correctly
    print("\n[Test 1] Fetching 2 intervals: 1h/5d + 15m/1d")
    print("-" * 70)

    requests_2 = [
        OHLCRequest(pair="USDJPY", interval="1h", period="5d"),
        OHLCRequest(pair="USDJPY", interval="15m", period="1d"),
    ]

    response_2 = fetch_batch_ohlc_sync(requests_2, exclude_weekends=True)

    print(f"Results:")
    for ohlc in response_2.successful:
        print(f"  {ohlc.pair} {ohlc.interval} {ohlc.period}: {ohlc.data_count} rows")

    if response_2.failed:
        print(f"Failed:")
        for err in response_2.failed:
            print(f"  {err.pair} {err.interval} {err.period}: {err.error_message}")

    # Test 2: Fetch 3 intervals (1h + 15m + 1d) - Reported to cause issues
    print("\n[Test 2] Fetching 3 intervals: 1h/5d + 15m/1d + 1d/20d")
    print("-" * 70)

    requests_3 = [
        OHLCRequest(pair="USDJPY", interval="1h", period="5d"),
        OHLCRequest(pair="USDJPY", interval="15m", period="1d"),
        OHLCRequest(pair="USDJPY", interval="1d", period="20d"),
    ]

    response_3 = fetch_batch_ohlc_sync(requests_3, exclude_weekends=True)

    print(f"Results:")
    for ohlc in response_3.successful:
        print(f"  {ohlc.pair} {ohlc.interval} {ohlc.period}: {ohlc.data_count} rows")

    if response_3.failed:
        print(f"Failed:")
        for err in response_3.failed:
            print(f"  {err.pair} {err.interval} {err.period}: {err.error_message}")

    # Compare results
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)

    # Get 1h data from both tests
    data_1h_test1 = next((ohlc for ohlc in response_2.successful if ohlc.interval == "1h"), None)
    data_1h_test2 = next((ohlc for ohlc in response_3.successful if ohlc.interval == "1h"), None)

    if data_1h_test1 and data_1h_test2:
        print(f"\n1h/5d data count:")
        print(f"  Test 1 (2 fetches): {data_1h_test1.data_count} rows")
        print(f"  Test 2 (3 fetches): {data_1h_test2.data_count} rows")
        print(f"  Difference: {data_1h_test1.data_count - data_1h_test2.data_count} rows")

        if data_1h_test2.data_count < 10:
            print(f"\n  [ISSUE REPRODUCED] 1h data has only {data_1h_test2.data_count} rows!")
            print(f"  Expected: ~80-97 rows, Got: {data_1h_test2.data_count} rows")
        else:
            print(f"\n  [OK] Both tests have similar data counts")

    # Get 15m data from both tests
    data_15m_test1 = next((ohlc for ohlc in response_2.successful if ohlc.interval == "15m"), None)
    data_15m_test2 = next((ohlc for ohlc in response_3.successful if ohlc.interval == "15m"), None)

    if data_15m_test1 and data_15m_test2:
        print(f"\n15m/1d data count:")
        print(f"  Test 1 (2 fetches): {data_15m_test1.data_count} rows")
        print(f"  Test 2 (3 fetches): {data_15m_test2.data_count} rows")

    # Show daily data if exists
    data_1d_test2 = next((ohlc for ohlc in response_3.successful if ohlc.interval == "1d"), None)
    if data_1d_test2:
        print(f"\n1d/20d data count (only in Test 2):")
        print(f"  Test 2: {data_1d_test2.data_count} rows")

    # Detailed analysis of 1h data in Test 2
    if data_1h_test2 and data_1h_test2.data_count < 10:
        print("\n" + "=" * 70)
        print("DETAILED ANALYSIS OF PROBLEMATIC 1h DATA")
        print("=" * 70)

        print(f"\nAll rows in 1h/5d data (Test 2):")
        for i, row in enumerate(data_1h_test2.rows):
            dt_str = row['Datetime']
            dt = datetime.strptime(dt_str[:19], '%Y-%m-%d %H:%M:%S')
            print(f"  Row {i+1}: {dt.strftime('%Y-%m-%d %H:%M (%A)')}")

    print("\n")


def test_gold_3fetch():
    """Test the same issue with Gold Futures"""
    print("=" * 70)
    print("TESTING GOLD (GC=F) WITH 3 INTERVALS")
    print("=" * 70)

    print("\n[Test] XAUUSD: 1h/5d + 15m/1d + 1d/20d")
    print("-" * 70)

    requests = [
        OHLCRequest(pair="XAUUSD", interval="1h", period="5d"),
        OHLCRequest(pair="XAUUSD", interval="15m", period="1d"),
        OHLCRequest(pair="XAUUSD", interval="1d", period="20d"),
    ]

    response = fetch_batch_ohlc_sync(requests, exclude_weekends=True)

    print(f"Results:")
    for ohlc in response.successful:
        print(f"  {ohlc.pair} {ohlc.interval} {ohlc.period}: {ohlc.data_count} rows")

    if response.failed:
        print(f"Failed:")
        for err in response.failed:
            print(f"  {err.pair} {err.interval} {err.period}: {err.error_message}")

    # Check if 1h data has the issue
    data_1h = next((ohlc for ohlc in response.successful if ohlc.interval == "1h"), None)
    if data_1h:
        if data_1h.data_count < 10:
            print(f"\n  [ISSUE CONFIRMED] Gold 1h data also has only {data_1h.data_count} rows!")
        else:
            print(f"\n  [OK] Gold 1h data looks normal: {data_1h.data_count} rows")

    print("\n")


if __name__ == "__main__":
    test_2_vs_3_fetch()
    test_gold_3fetch()
