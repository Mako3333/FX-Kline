"""
Test to investigate if yfinance has issues with parallel downloads
"""

import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def download_data(symbol, interval, period, label):
    """Download data and print results"""
    print(f"\n[{label}] Downloading {symbol} {interval} {period}...")
    df = yf.download(symbol, interval=interval, period=period, auto_adjust=False, progress=False)
    print(f"[{label}] Downloaded {len(df)} rows")

    # Check columns structure
    if isinstance(df.columns, pd.MultiIndex):
        print(f"[{label}] MultiIndex columns detected!")
        df.columns = df.columns.get_level_values(0)

    print(f"[{label}] First row: {df.index[0]}")
    print(f"[{label}] Last row: {df.index[-1]}")

    return label, df


def test_sequential():
    """Test sequential downloads"""
    print("=" * 70)
    print("SEQUENTIAL DOWNLOADS")
    print("=" * 70)

    label1, df1 = download_data("USDJPY=X", "1h", "5d", "1h/5d")
    label2, df2 = download_data("USDJPY=X", "15m", "1d", "15m/1d")
    label3, df3 = download_data("USDJPY=X", "1d", "20d", "1d/20d")

    print("\n\nRESULTS:")
    print(f"  {label1}: {len(df1)} rows")
    print(f"  {label2}: {len(df2)} rows")
    print(f"  {label3}: {len(df3)} rows")

    return df1, df2, df3


def test_parallel():
    """Test parallel downloads using ThreadPoolExecutor"""
    print("\n\n" + "=" * 70)
    print("PARALLEL DOWNLOADS (ThreadPoolExecutor)")
    print("=" * 70)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(download_data, "USDJPY=X", "1h", "5d", "1h/5d"),
            executor.submit(download_data, "USDJPY=X", "15m", "1d", "15m/1d"),
            executor.submit(download_data, "USDJPY=X", "1d", "20d", "1d/20d"),
        ]

        results = [future.result() for future in futures]

    print("\n\nRESULTS:")
    for label, df in results:
        print(f"  {label}: {len(df)} rows")

    return [df for _, df in results]


def test_parallel_with_inspection():
    """Test parallel downloads with detailed inspection"""
    print("\n\n" + "=" * 70)
    print("PARALLEL DOWNLOADS WITH DETAILED INSPECTION")
    print("=" * 70)

    results = {}

    def download_and_store(key, symbol, interval, period):
        """Download and store in shared dict"""
        print(f"\n[{key}] START download {symbol} {interval} {period}")
        df = yf.download(symbol, interval=interval, period=period, auto_adjust=False, progress=False)

        # Flatten MultiIndex immediately
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Store a COPY to avoid reference issues
        results[key] = df.copy()

        print(f"[{key}] FINISH download - {len(df)} rows")
        print(f"[{key}] First: {df.index[0]}, Last: {df.index[-1]}")
        return key

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(download_and_store, "1h", "USDJPY=X", "1h", "5d"),
            executor.submit(download_and_store, "15m", "USDJPY=X", "15m", "1d"),
            executor.submit(download_and_store, "1d", "USDJPY=X", "1d", "20d"),
        ]

        for future in futures:
            future.result()

    print("\n\nFINAL STORED RESULTS:")
    for key, df in results.items():
        print(f"  {key}: {len(df)} rows")
        print(f"    First row: {df.index[0]}")
        print(f"    Last row: {df.index[-1]}")
        print(f"    Sample timestamps:")
        for i in range(min(5, len(df))):
            print(f"      {df.index[i]}")

    return results


if __name__ == "__main__":
    # Test 1: Sequential
    dfs_seq = test_sequential()

    # Test 2: Parallel
    dfs_par = test_parallel()

    # Test 3: Parallel with inspection
    dfs_inspect = test_parallel_with_inspection()

    print("\n\n" + "=" * 70)
    print("SUMMARY COMPARISON")
    print("=" * 70)
    print(f"\nSequential:")
    print(f"  1h: {len(dfs_seq[0])} rows")
    print(f"  15m: {len(dfs_seq[1])} rows")
    print(f"  1d: {len(dfs_seq[2])} rows")

    print(f"\nParallel:")
    print(f"  1h: {len(dfs_par[0])} rows")
    print(f"  15m: {len(dfs_par[1])} rows")
    print(f"  1d: {len(dfs_par[2])} rows")

    print(f"\nParallel with inspection:")
    print(f"  1h: {len(dfs_inspect['1h'])} rows")
    print(f"  15m: {len(dfs_inspect['15m'])} rows")
    print(f"  1d: {len(dfs_inspect['1d'])} rows")
