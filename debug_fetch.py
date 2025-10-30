#!/usr/bin/env python3
"""
Debug script to check yfinance data structure
"""

import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fx_kline.core.validators import validate_currency_pair, validate_timeframe, validate_period
import yfinance as yf

# Fetch test data
pair = validate_currency_pair("USDJPY")
interval = validate_timeframe("1h")
period = validate_period("1d")

print(f"Fetching {pair} {interval} {period}...")
df = yf.download(pair, interval=interval, period=period, auto_adjust=False, progress=False)

print(f"\nDataFrame shape: {df.shape}")
print(f"DataFrame columns: {df.columns.tolist()}")
print(f"DataFrame index type: {type(df.index)}")
print(f"Index name: {df.index.name}")
print(f"\nFirst 3 rows:")
print(df.head(3))

print(f"\nData types:")
print(df.dtypes)

# Test iteration
print("\n\n--- Testing iteration ---")
ohlc_columns = ['Open', 'High', 'Low', 'Close']
if 'Volume' in df.columns:
    ohlc_columns.append('Volume')

df_ohlc = df[ohlc_columns].copy()

print(f"Selected columns: {df_ohlc.columns.tolist()}")
print(f"df_ohlc shape: {df_ohlc.shape}")
print(f"\nFirst row iteration:")
for idx, row in df_ohlc.head(1).iterrows():
    print(f"  idx: {idx} (type: {type(idx)})")
    print(f"  row type: {type(row)}")
    print(f"  row.Open: {row['Open']} (type: {type(row['Open'])})")
    print(f"  row['Open'] value: {row['Open']}")
    if hasattr(row['Open'], 'item'):
        print(f"  row['Open'].item(): {row['Open'].item()}")
