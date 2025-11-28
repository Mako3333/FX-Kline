"""
Debug actual fetch with detailed logging to understand the issue
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yfinance as yf
import pandas as pd
from fx_kline.core.timezone_utils import convert_dataframe_to_jst
from fx_kline.core.business_days import filter_business_days_fx
from fx_kline.core.validators import validate_currency_pair

def debug_single_fetch_detailed(pair, interval, period):
    """Detailed debug of a single fetch operation"""
    print("=" * 70)
    print(f"DEBUGGING: {pair} {interval} {period}")
    print("=" * 70)

    # Step 1: Validate and format pair
    pair_formatted = validate_currency_pair(pair)
    print(f"\nStep 1: Pair validation")
    print(f"  Input: {pair}")
    print(f"  Formatted: {pair_formatted}")

    # Step 2: Download from yfinance
    print(f"\nStep 2: Download from yfinance")
    df = yf.download(pair_formatted, interval=interval, period=period, auto_adjust=False, progress=False)
    print(f"  Raw data shape: {df.shape}")
    print(f"  Raw data index type: {type(df.index)}")
    print(f"  Raw data columns: {df.columns.tolist()}")

    # Check if MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        print(f"  MultiIndex detected!")
        print(f"  Levels: {df.columns.levels}")
        print(f"  Flattening...")
        df.columns = df.columns.get_level_values(0)

    print(f"  First 3 rows (UTC):")
    for i in range(min(3, len(df))):
        print(f"    {df.index[i]}: O={df['Open'].iloc[i]:.2f}")

    # Step 3: Convert to JST
    print(f"\nStep 3: Convert to JST")
    df_jst = convert_dataframe_to_jst(df)
    print(f"  JST data shape: {df_jst.shape}")
    print(f"  First 3 rows (JST):")
    for i in range(min(3, len(df_jst))):
        print(f"    {df_jst.index[i]}: O={df_jst['Open'].iloc[i]:.2f}")

    # Step 4: Apply weekend filtering
    print(f"\nStep 4: Apply weekend filtering")
    df_filtered = filter_business_days_fx(df_jst, interval, pair_formatted)
    print(f"  Filtered data shape: {df_filtered.shape}")
    print(f"  Rows removed: {len(df_jst) - len(df_filtered)}")

    # Step 5: Extract expected business days
    print(f"\nStep 5: Extract expected business days from period")
    import re
    match = re.match(r"^(\d+)([a-z]+)$", period)
    if match and match.group(2) == "d":
        expected_business_days = int(match.group(1))
        print(f"  Expected business days: {expected_business_days}")
    else:
        expected_business_days = None
        print(f"  Expected business days: None (not a day-based period)")

    # Step 6: Check unique business days
    print(f"\nStep 6: Count unique business days")
    normalized_index = df_filtered.index.normalize()
    unique_days = normalized_index.unique()
    print(f"  Normalized index (first 5):")
    for i in range(min(5, len(normalized_index))):
        print(f"    Original: {df_filtered.index[i]} -> Normalized: {normalized_index[i]}")
    print(f"  Unique days count: {len(unique_days)}")
    print(f"  Unique days:")
    for day in unique_days:
        print(f"    {day}")

    # Step 7: Apply trimming logic (THE CRITICAL PART)
    print(f"\nStep 7: Apply trimming logic")
    if expected_business_days is not None and len(unique_days) > expected_business_days:
        print(f"  Condition met: {len(unique_days)} > {expected_business_days}")
        keep_days = set(unique_days[-expected_business_days:])
        print(f"  Keep last {expected_business_days} days:")
        for day in sorted(keep_days):
            print(f"    {day}")

        print(f"\n  Applying filter: normalized_index.isin(keep_days)")
        mask = normalized_index.isin(keep_days)
        print(f"  Mask stats: {mask.sum()} True, {(~mask).sum()} False")

        df_trimmed = df_filtered[mask]
        print(f"  Data shape after trimming: {df_trimmed.shape}")
        print(f"  All rows after trimming:")
        for idx in df_trimmed.index:
            print(f"    {idx}")
    else:
        print(f"  Trimming NOT applied")
        print(f"  Reason: len(unique_days)={len(unique_days)}, expected={expected_business_days}")
        df_trimmed = df_filtered

    return df_trimmed


def debug_batch_fetch():
    """Debug batch fetch to see if there's interference"""
    print("\n\n" + "=" * 70)
    print("DEBUGGING BATCH FETCH (3 intervals)")
    print("=" * 70)

    # Simulate fetching 3 intervals
    print("\n[1] Fetching 1h/5d...")
    df_1h = debug_single_fetch_detailed("USDJPY", "1h", "5d")

    print("\n\n[2] Fetching 15m/1d...")
    df_15m = debug_single_fetch_detailed("USDJPY", "15m", "1d")

    print("\n\n[3] Fetching 1d/20d...")
    df_1d = debug_single_fetch_detailed("USDJPY", "1d", "20d")

    print("\n\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"1h/5d: {len(df_1h)} rows")
    print(f"15m/1d: {len(df_15m)} rows")
    print(f"1d/20d: {len(df_1d)} rows")


if __name__ == "__main__":
    debug_batch_fetch()
