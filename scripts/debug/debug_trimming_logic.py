"""
Debug script to understand the trimming logic issue
"""

import pandas as pd
import pytz
from datetime import datetime, timedelta

JST_TZ = pytz.timezone('Asia/Tokyo')

def simulate_trimming_issue():
    """Simulate the trimming logic to understand the issue"""
    print("=" * 70)
    print("DEBUGGING TRIMMING LOGIC")
    print("=" * 70)

    # Create sample hourly data (like 1h/5d would have)
    # Should have multiple hours per day
    dates = []
    base_date = datetime(2025, 10, 27, 9, 0, 0, tzinfo=JST_TZ)

    for day in range(5):  # 5 days
        for hour in range(10):  # 10 hours per day
            dates.append(base_date + timedelta(days=day, hours=hour))

    df = pd.DataFrame({
        'Open': range(len(dates)),
        'Close': range(len(dates)),
    }, index=pd.DatetimeIndex(dates))

    print(f"\nOriginal data:")
    print(f"  Total rows: {len(df)}")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    print(f"  First 5 rows:")
    for i in range(5):
        print(f"    {df.index[i]}")
    print(f"  Last 5 rows:")
    for i in range(-5, 0):
        print(f"    {df.index[i]}")

    # Apply the trimming logic from data_fetcher.py line 194-199
    expected_business_days = 5

    print(f"\n\nApplying trimming logic (expected_business_days = {expected_business_days}):")
    print("-" * 70)

    # Step 1: Normalize index
    normalized_index = df.index.normalize()
    print(f"\nStep 1: Normalized index (first 5):")
    for i in range(5):
        print(f"  Original: {df.index[i]} -> Normalized: {normalized_index[i]}")

    # Step 2: Get unique days
    unique_days = normalized_index.unique()
    print(f"\nStep 2: Unique days:")
    for day in unique_days:
        print(f"  {day}")
    print(f"  Total unique days: {len(unique_days)}")

    # Step 3: Keep last N days
    if len(unique_days) > expected_business_days:
        keep_days = set(unique_days[-expected_business_days:])
        print(f"\nStep 3: Keep last {expected_business_days} days:")
        for day in sorted(keep_days):
            print(f"  {day}")

        # Step 4: Filter data
        print(f"\nStep 4: Filter using normalized_index.isin(keep_days)")
        mask = normalized_index.isin(keep_days)
        print(f"  Mask created: {mask.sum()} rows will be kept")

        df_trimmed = df[mask]
        print(f"\nResult after trimming:")
        print(f"  Total rows: {len(df_trimmed)}")
        print(f"  All rows:")
        for idx in df_trimmed.index:
            print(f"    {idx}")

    # Now test what happens if df.index already contains normalized timestamps
    print("\n\n" + "=" * 70)
    print("TESTING WITH NORMALIZED TIMESTAMPS (Like Daily Data)")
    print("=" * 70)

    # Create daily data (timestamps are already at 09:00:00, like yfinance daily data)
    daily_dates = []
    for day in range(5):
        daily_dates.append(base_date + timedelta(days=day))

    df_daily = pd.DataFrame({
        'Open': range(len(daily_dates)),
        'Close': range(len(daily_dates)),
    }, index=pd.DatetimeIndex(daily_dates))

    print(f"\nDaily data (timestamps at 09:00:00):")
    for idx in df_daily.index:
        print(f"  {idx}")

    # Apply same trimming logic
    normalized_daily = df_daily.index.normalize()
    print(f"\nNormalized daily data:")
    for i, idx in enumerate(normalized_daily):
        print(f"  Original: {df_daily.index[i]} -> Normalized: {idx}")

    print("\n\n" + "=" * 70)
    print("HYPOTHESIS: Is there a pandas MultiIndex issue?")
    print("=" * 70)

    # Check if there's something weird with the DataFrame structure
    print(f"\ndf.index type: {type(df.index)}")
    print(f"df.columns type: {type(df.columns)}")
    print(f"df.shape: {df.shape}")

    # Check timezone info
    print(f"\nTimezone info:")
    print(f"  df.index.tzinfo: {df.index.tzinfo}")
    print(f"  normalized_index.tzinfo: {normalized_index.tzinfo}")


if __name__ == "__main__":
    simulate_trimming_issue()
