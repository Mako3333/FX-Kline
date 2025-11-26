#!/usr/bin/env python3
"""
Test script to verify which gold symbol works best with yfinance
Compares GC=F (Gold Futures) and GOLD symbols
"""

import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import yfinance as yf


def run_symbol_test(symbol: str, interval: str, period: str) -> dict:
    """
    Test a specific symbol with given interval and period
    
    Returns:
        dict with test results
    """
    result = {
        "symbol": symbol,
        "interval": interval,
        "period": period,
        "success": False,
        "data_count": 0,
        "error": None,
        "first_date": None,
        "last_date": None,
        "sample_close": None,
        "has_multiindex": False,
        "columns": []
    }
    
    try:
        print(f"  Testing {symbol} with {interval}/{period}...", end=" ")
        df = yf.download(
            symbol,
            interval=interval,
            period=period,
            auto_adjust=False,
            progress=False
        )
        
        # Check for multi-index columns
        if isinstance(df.columns, pd.MultiIndex):
            result["has_multiindex"] = True
            result["columns"] = [col[0] for col in df.columns]
            df.columns = df.columns.get_level_values(0)
        else:
            result["columns"] = df.columns.tolist()
        
        if df.empty:
            result["error"] = "Empty DataFrame returned"
            print("❌ EMPTY")
            return result
        
        result["success"] = True
        result["data_count"] = len(df)
        result["first_date"] = str(df.index[0])
        result["last_date"] = str(df.index[-1])
        
        if 'Close' in df.columns:
            result["sample_close"] = float(df['Close'].iloc[-1])
        
        close_str = f"${result['sample_close']:.2f}" if result['sample_close'] is not None else "N/A"
        print(f"✅ SUCCESS ({len(df)} rows, last close: {close_str})")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ ERROR: {str(e)}")
    
    return result


def main():
    """Run comprehensive gold symbol tests"""
    print("=" * 70)
    print("Gold Symbol Verification Test")
    print("=" * 70)
    print()
    
    # Symbols to test
    symbols = ["GC=F", "GOLD"]
    
    # Test cases matching the error report
    test_cases = [
        ("1h", "5d"),
        ("15m", "2d"),
        ("1d", "20d"),
    ]
    
    all_results = []
    
    for symbol in symbols:
        print(f"\n{'=' * 70}")
        print(f"Testing Symbol: {symbol}")
        print(f"{'=' * 70}")
        
        symbol_results = []
        
        for interval, period in test_cases:
            result = run_symbol_test(symbol, interval, period)
            symbol_results.append(result)
            all_results.append(result)
        
        # Summary for this symbol
        successful = sum(1 for r in symbol_results if r["success"])
        print(f"\n  Summary for {symbol}: {successful}/{len(test_cases)} tests passed")
    
    # Final comparison
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    # Group by symbol
    for symbol in symbols:
        symbol_results = [r for r in all_results if r["symbol"] == symbol]
        successful = sum(1 for r in symbol_results if r["success"])
        total = len(symbol_results)
        
        print(f"\n{symbol}:")
        print(f"  Success Rate: {successful}/{total} ({100*successful/total:.0f}%)")
        
        if successful > 0:
            sample_result = next(r for r in symbol_results if r["success"])
            print(f"  Columns Available: {', '.join(sample_result['columns'])}")
            print(f"  Multi-index Columns: {'Yes' if sample_result['has_multiindex'] else 'No'}")
            
            # Show price samples
            for r in symbol_results:
                if r["success"] and r["sample_close"]:
                    print(f"  Sample Price ({r['interval']}/{r['period']}): ${r['sample_close']:.2f}")
        
        # Show errors if any
        failed = [r for r in symbol_results if not r["success"]]
        if failed:
            print(f"  Failures:")
            for r in failed:
                print(f"    {r['interval']}/{r['period']}: {r['error']}")
    
    # Recommendation
    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    
    gc_f_results = [r for r in all_results if r["symbol"] == "GC=F"]
    gold_results = [r for r in all_results if r["symbol"] == "GOLD"]
    
    gc_f_success = sum(1 for r in gc_f_results if r["success"])
    gold_success = sum(1 for r in gold_results if r["success"])
    
    print()
    if gc_f_success > gold_success:
        print("✅ RECOMMENDED: GC=F")
        print("   Reason: Better data availability")
    elif gold_success > gc_f_success:
        print("✅ RECOMMENDED: GOLD")
        print("   Reason: Better data availability")
    elif gc_f_success == gold_success and gc_f_success > 0:
        print("✅ RECOMMENDED: GC=F")
        print("   Reason: Both work equally well, GC=F is more standard for gold futures")
    else:
        print("❌ WARNING: Neither symbol works reliably")
        print("   Alternative approaches may be needed")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()

