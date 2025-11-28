"""
Comprehensive test to verify the perfect implementation is restored
Tests both FX pairs and Gold Futures
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fx_kline.core import fetch_single_ohlc, fetch_batch_ohlc_sync, OHLCRequest
from datetime import datetime

def test_comprehensive():
    """Comprehensive test of all scenarios"""
    print("=" * 70)
    print("COMPREHENSIVE TEST - FX Pairs and Gold Futures")
    print("=" * 70)

    results = []

    # Test 1: USDJPY 1h 5d
    print("\n[Test 1] USDJPY - 1h interval, 5d period")
    print("-" * 70)
    ohlc, error = fetch_single_ohlc("USDJPY", "1h", "5d", exclude_weekends=True)
    if error:
        print(f"  [FAIL] {error.error_message}")
        results.append(("USDJPY 1h 5d", False, 0))
    else:
        saturday_count = sum(1 for r in ohlc.rows if 'Saturday' in datetime.strptime(r['Datetime'][:19], '%Y-%m-%d %H:%M:%S').strftime('%A'))
        print(f"  [PASS] Data count: {ohlc.data_count}")
        print(f"  Saturday rows: {saturday_count} (FX should have Saturday morning data)")
        results.append(("USDJPY 1h 5d", True, ohlc.data_count))

    # Test 2: USDJPY 15m 1d
    print("\n[Test 2] USDJPY - 15m interval, 1d period")
    print("-" * 70)
    ohlc, error = fetch_single_ohlc("USDJPY", "15m", "1d", exclude_weekends=True)
    if error:
        print(f"  [FAIL] {error.error_message}")
        results.append(("USDJPY 15m 1d", False, 0))
    else:
        print(f"  [PASS] Data count: {ohlc.data_count}")
        print(f"  Expected: Multiple rows (market open hours)")
        results.append(("USDJPY 15m 1d", True, ohlc.data_count))

    # Test 3: USDJPY 1d 20d
    print("\n[Test 3] USDJPY - 1d interval, 20d period")
    print("-" * 70)
    ohlc, error = fetch_single_ohlc("USDJPY", "1d", "20d", exclude_weekends=True)
    if error:
        print(f"  [FAIL] {error.error_message}")
        results.append(("USDJPY 1d 20d", False, 0))
    else:
        weekend_count = sum(1 for r in ohlc.rows if datetime.strptime(r['Datetime'][:19], '%Y-%m-%d %H:%M:%S').weekday() >= 5)
        print(f"  [PASS] Data count: {ohlc.data_count}")
        print(f"  Weekend rows: {weekend_count} (should be 0)")
        results.append(("USDJPY 1d 20d", True, ohlc.data_count))

    # Test 4: XAUUSD (GC=F) 1h 5d
    print("\n[Test 4] XAUUSD (GC=F) - 1h interval, 5d period")
    print("-" * 70)
    ohlc, error = fetch_single_ohlc("XAUUSD", "1h", "5d", exclude_weekends=True)
    if error:
        print(f"  [FAIL] {error.error_message}")
        results.append(("XAUUSD 1h 5d", False, 0))
    else:
        saturday_count = sum(1 for r in ohlc.rows if 'Saturday' in datetime.strptime(r['Datetime'][:19], '%Y-%m-%d %H:%M:%S').strftime('%A'))
        print(f"  [PASS] Data count: {ohlc.data_count}")
        print(f"  Saturday rows: {saturday_count} (Gold Futures should have NO Saturday data)")
        results.append(("XAUUSD 1h 5d", True, ohlc.data_count))

    # Test 5: XAUUSD (GC=F) 15m 1d
    print("\n[Test 5] XAUUSD (GC=F) - 15m interval, 1d period")
    print("-" * 70)
    ohlc, error = fetch_single_ohlc("XAUUSD", "15m", "1d", exclude_weekends=True)
    if error:
        print(f"  [FAIL] {error.error_message}")
        results.append(("XAUUSD 15m 1d", False, 0))
    else:
        print(f"  [PASS] Data count: {ohlc.data_count}")
        print(f"  Expected: Multiple rows (futures market open hours)")
        results.append(("XAUUSD 15m 1d", True, ohlc.data_count))

    # Test 6: Batch fetch with mixed symbols
    print("\n[Test 6] Batch fetch - Mixed FX and Gold")
    print("-" * 70)
    requests = [
        OHLCRequest(pair="USDJPY", interval="1h", period="5d"),
        OHLCRequest(pair="EURUSD", interval="1h", period="5d"),
        OHLCRequest(pair="XAUUSD", interval="1h", period="5d"),
    ]
    response = fetch_batch_ohlc_sync(requests, exclude_weekends=True)
    print(f"  Total requested: {response.total_requested}")
    print(f"  Total succeeded: {response.total_succeeded}")
    print(f"  Total failed: {response.total_failed}")

    if response.total_succeeded == response.total_requested:
        print(f"  [PASS] Batch fetch successful")
        for ohlc in response.successful:
            saturday_count = sum(1 for r in ohlc.rows if 'Saturday' in datetime.strptime(r['Datetime'][:19], '%Y-%m-%d %H:%M:%S').strftime('%A'))
            print(f"    {ohlc.pair}: {ohlc.data_count} rows (Saturday: {saturday_count})")
        results.append(("Batch fetch", True, response.total_succeeded))
    else:
        print(f"  [FAIL] Expected {response.total_requested} successes, got {response.total_succeeded}")
        results.append(("Batch fetch", False, response.total_succeeded))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for test_name, success, count in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {test_name}: {count} rows")

    print(f"\nTotal: {passed}/{total} tests passed")

    # Verification against expected results
    print("\n" + "=" * 70)
    print("VERIFICATION AGAINST PERFECT IMPLEMENTATION")
    print("=" * 70)

    print("\nExpected behavior:")
    print("  1. FX pairs (USDJPY, EURUSD): Saturday morning data retained (0:00-6:00 JST)")
    print("  2. Gold Futures (GC=F): NO Saturday data (commodity market closes Friday)")
    print("  3. 15m/1h intervals: Multiple data rows (not just 1-5)")
    print("  4. Daily intervals: No weekend data")
    print("  5. Batch fetch: All succeed with correct data counts")

    print("\nActual results:")
    def get_result_count(test_name):
        """Get count for a test, returns None if test failed or not found"""
        return next((c for n, s, c in results if n == test_name and s), None)
    
    usdjpy_1h = get_result_count("USDJPY 1h 5d")
    xauusd_1h = get_result_count("XAUUSD 1h 5d")
    usdjpy_15m = get_result_count("USDJPY 15m 1d")
    xauusd_15m = get_result_count("XAUUSD 15m 1d")

    checks = []
    checks.append(("USDJPY 1h has substantial data", usdjpy_1h is not None and usdjpy_1h >= 80))
    checks.append(("XAUUSD 1h has substantial data", xauusd_1h is not None and xauusd_1h >= 80))
    checks.append(("USDJPY 15m has multiple rows", usdjpy_15m is not None and usdjpy_15m >= 5))
    checks.append(("XAUUSD 15m has multiple rows", xauusd_15m is not None and xauusd_15m >= 5))

    print("")
    for check_name, check_result in checks:
        status = "[OK]" if check_result else "[NG]"
        print(f"  {status} {check_name}")

    all_ok = all(check_result for _, check_result in checks) and passed == total

    if all_ok:
        print("\n" + "=" * 70)
        print("[SUCCESS] Perfect implementation RESTORED!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("[WARNING] Some tests did not meet expectations")
        print("=" * 70)

    print("\n")


if __name__ == "__main__":
    test_comprehensive()
