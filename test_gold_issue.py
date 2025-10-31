"""
Test to diagnose GC=F (Gold Futures) data fetching issue
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fx_kline.core import fetch_single_ohlc
from datetime import datetime

def test_gold_data():
    """Test gold data fetching with GC=F"""
    print("=" * 60)
    print("Testing GC=F (Gold Futures) Data Fetching")
    print("=" * 60)

    # Test 1: 1h interval, 5d period
    print("\nTest 1: XAUUSD (GC=F) - 1h interval, 5d period")
    print("-" * 60)

    ohlc_data, error = fetch_single_ohlc(
        pair="XAUUSD",
        interval="1h",
        period="5d",
        exclude_weekends=True
    )

    if error:
        print(f"[ERROR] {error.error_message}")
        print(f"Error type: {error.error_type}")
    else:
        print(f"Data count: {ohlc_data.data_count}")
        print(f"\nFirst 5 rows:")
        for i, row in enumerate(ohlc_data.rows[:5]):
            dt_str = row['Datetime']
            dt = datetime.strptime(dt_str[:19], '%Y-%m-%d %H:%M:%S')
            print(f"  {dt.strftime('%Y-%m-%d %H:%M (%A)')}: O={row['Open']:.2f}")

        print(f"\nLast 5 rows:")
        for i, row in enumerate(ohlc_data.rows[-5:]):
            dt_str = row['Datetime']
            dt = datetime.strptime(dt_str[:19], '%Y-%m-%d %H:%M:%S')
            print(f"  {dt.strftime('%Y-%m-%d %H:%M (%A)')}: O={row['Open']:.2f}")

        # Count by day
        day_counts = {}
        for row in ohlc_data.rows:
            dt_str = row['Datetime']
            dt = datetime.strptime(dt_str[:19], '%Y-%m-%d %H:%M:%S')
            day_name = dt.strftime('%A')
            day_counts[day_name] = day_counts.get(day_name, 0) + 1

        print(f"\nData distribution by day:")
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day in day_counts:
                print(f"  {day}: {day_counts[day]} rows")

    # Test 2: 15m interval, 1d period
    print("\n\nTest 2: XAUUSD (GC=F) - 15m interval, 1d period")
    print("-" * 60)

    ohlc_data, error = fetch_single_ohlc(
        pair="XAUUSD",
        interval="15m",
        period="1d",
        exclude_weekends=True
    )

    if error:
        print(f"[ERROR] {error.error_message}")
        print(f"Error type: {error.error_type}")
    else:
        print(f"Data count: {ohlc_data.data_count}")
        print(f"First row: {ohlc_data.rows[0]['Datetime']}")
        print(f"Last row: {ohlc_data.rows[-1]['Datetime']}")

    # Compare with USDJPY
    print("\n\n" + "=" * 60)
    print("Comparison: USDJPY (FX) vs XAUUSD (Gold Futures)")
    print("=" * 60)

    print("\nUSDJPY - 1h interval, 5d period")
    print("-" * 60)
    ohlc_usdjpy, error = fetch_single_ohlc(
        pair="USDJPY",
        interval="1h",
        period="5d",
        exclude_weekends=True
    )

    if error:
        print(f"[ERROR] {error.error_message}")
    else:
        print(f"Data count: {ohlc_usdjpy.data_count}")

        # Count by day
        day_counts = {}
        for row in ohlc_usdjpy.rows:
            dt_str = row['Datetime']
            dt = datetime.strptime(dt_str[:19], '%Y-%m-%d %H:%M:%S')
            day_name = dt.strftime('%A')
            day_counts[day_name] = day_counts.get(day_name, 0) + 1

        print(f"Data distribution by day:")
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day in day_counts:
                print(f"  {day}: {day_counts[day]} rows")

    print("\n")


# Test raw yfinance data to understand the issue
def test_raw_yfinance():
    """Test raw yfinance data for GC=F"""
    import yfinance as yf

    print("=" * 60)
    print("Raw yfinance Data Analysis")
    print("=" * 60)

    # Download GC=F data
    print("\nDownloading GC=F data (5d, 1h)...")
    df_gold = yf.download("GC=F", interval="1h", period="5d", auto_adjust=False, progress=False)

    print(f"Raw data shape: {df_gold.shape}")
    print(f"Raw data count: {len(df_gold)}")
    print(f"\nFirst 10 rows (UTC timezone):")
    print(df_gold.head(10))
    print(f"\nLast 10 rows (UTC timezone):")
    print(df_gold.tail(10))

    # Download USDJPY data for comparison
    print("\n\nDownloading USDJPY=X data (5d, 1h)...")
    df_usdjpy = yf.download("USDJPY=X", interval="1h", period="5d", auto_adjust=False, progress=False)

    print(f"Raw data shape: {df_usdjpy.shape}")
    print(f"Raw data count: {len(df_usdjpy)}")

    print("\n")


if __name__ == "__main__":
    test_gold_data()
    test_raw_yfinance()
