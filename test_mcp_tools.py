#!/usr/bin/env python3
"""
Test script for MCP tools functionality.

Tests basic functionality of each MCP tool without starting the full server.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fx_kline.mcp.tools import (
    fetch_ohlc_tool,
    fetch_ohlc_batch_tool,
    list_available_pairs_tool,
    list_available_timeframes_tool,
)


def test_list_available_pairs():
    """Test listing available currency pairs."""
    print("=" * 60)
    print("Test 1: List Available Pairs")
    print("=" * 60)

    result = list_available_pairs_tool(preset_only=True)
    print(f"Success: {result['success']}")
    print(f"Pairs: {result['pairs']}")
    print(f"Count: {result['count']}")
    print()

    assert result['success'], "list_available_pairs_tool should succeed"
    assert result['count'] > 0, "Should have at least one currency pair"


def test_list_available_timeframes():
    """Test listing available timeframes."""
    print("=" * 60)
    print("Test 2: List Available Timeframes")
    print("=" * 60)

    result = list_available_timeframes_tool(preset_only=True)
    print(f"Success: {result['success']}")
    print(f"Timeframes: {result['timeframes']}")
    print(f"Count: {result['count']}")
    print()

    assert result['success'], "list_available_timeframes_tool should succeed"
    assert result['count'] > 0, "Should have at least one timeframe"


def test_fetch_ohlc():
    """Test fetching single OHLC data."""
    print("=" * 60)
    print("Test 3: Fetch Single OHLC (USDJPY, 1d, 5d)")
    print("=" * 60)

    result = fetch_ohlc_tool(
        pair="USDJPY",
        interval="1d",
        period="5d",
        exclude_weekends=True
    )

    print(f"Success: {result['success']}")

    if result['success']:
        data = result['data']
        print(f"Pair: {data['pair']}")
        print(f"Interval: {data['interval']}")
        print(f"Period: {data['period']}")
        print(f"Data Count: {data['data_count']}")
        print(f"Timestamp: {data['timestamp_jst']}")
        print(f"Columns: {data['columns']}")
        print(f"First Row: {data['rows'][0] if data['rows'] else 'No data'}")
        print(f"Last Row: {data['rows'][-1] if data['rows'] else 'No data'}")
    else:
        print(f"Error Type: {result['error']['type']}")
        print(f"Error Message: {result['error']['message']}")

    print()
    assert result['success'], "fetch_ohlc_tool should succeed"
    assert result['data']['data_count'] > 0, "Should have data"


def test_fetch_ohlc_batch():
    """Test batch fetching OHLC data."""
    print("=" * 60)
    print("Test 4: Fetch Batch OHLC (USDJPY, EURUSD)")
    print("=" * 60)

    requests = [
        {"pair": "USDJPY", "interval": "1d", "period": "5d"},
        {"pair": "EURUSD", "interval": "1d", "period": "5d"},
    ]

    result = fetch_ohlc_batch_tool(
        requests=requests,
        exclude_weekends=True
    )

    print(f"Success: {result['success']}")

    if result['success']:
        stats = result['statistics']
        print(f"Total Requested: {stats['total_requested']}")
        print(f"Total Succeeded: {stats['total_succeeded']}")
        print(f"Total Failed: {stats['total_failed']}")
        print(f"Summary: {result['summary']}")

        print("\nSuccessful Results:")
        for i, data in enumerate(result['successful'], 1):
            print(f"  {i}. {data['pair']} - {data['interval']} - {data['data_count']} rows")

        if result['failed']:
            print("\nFailed Results:")
            for i, error in enumerate(result['failed'], 1):
                print(f"  {i}. {error['pair']} - {error['type']}: {error['message']}")
    else:
        print(f"Error Type: {result['error']['type']}")
        print(f"Error Message: {result['error']['message']}")

    print()
    assert result['success'], "fetch_ohlc_batch_tool should succeed"
    assert result['statistics']['total_succeeded'] > 0, "Should have at least one success"


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MCP Tools Functionality Test")
    print("=" * 60 + "\n")

    try:
        test_list_available_pairs()
        test_list_available_timeframes()
        test_fetch_ohlc()
        test_fetch_ohlc_batch()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nMCP server is ready to use.")
        print("Next step: Configure Claude Desktop with claude_desktop_config.example.json")

    except AssertionError as e:
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print("=" * 60)
        print(f"❌ Unexpected error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
