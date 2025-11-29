#!/usr/bin/env python3
"""
Pytest-style tests for MCP tools functionality.

These tests exercise the basic behavior of each MCP tool without starting
the full MCP server.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project src/ directory is on sys.path when running this file directly:
#   uv run python tests/test_mcp_tools.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_kline.mcp.tools import (  # noqa: E402
    get_daily_ohlc,
    get_intraday_ohlc,
    get_ohlc_batch,
    list_pairs,
    list_timeframes,
)


def test_list_available_pairs():
    """Test listing available currency pairs."""
    print("=" * 60)
    print("Test 1: List Available Pairs")
    print("=" * 60)

    result = list_pairs(preset_only=True)
    print(f"Success: {result['success']}")
    print(f"Pairs: {result['pairs']}")
    print(f"Count: {result['count']}")
    print()

    assert result["success"], (
        f"list_pairs should succeed. Error: {result.get('error')}"
    )
    assert result["count"] > 0, (
        f"Should have at least one currency pair. Got: {result.get('count')}"
    )


def test_list_available_timeframes():
    """Test listing available timeframes."""
    print("=" * 60)
    print("Test 2: List Available Timeframes")
    print("=" * 60)

    result = list_timeframes(preset_only=True)
    print(f"Success: {result['success']}")
    print(f"Timeframes: {result['timeframes']}")
    print(f"Count: {result['count']}")
    print()

    assert result["success"], (
        f"list_timeframes should succeed. Error: {result.get('error')}"
    )
    assert result["count"] > 0, (
        f"Should have at least one timeframe. Got: {result.get('count')}"
    )


def test_fetch_ohlc():
    """Test fetching single OHLC data."""
    print("=" * 60)
    print("Test 3: Fetch Single OHLC (USDJPY, 1d, 5d)")
    print("=" * 60)

    result = get_daily_ohlc(
        pair="USDJPY",
        interval="1d",
        period="5d",
        exclude_weekends=True,
    )

    print(f"Success: {result['success']}")

    if result["success"]:
        data = result["data"]
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
    assert result["success"], (
        f"get_daily_ohlc should succeed. Error: {result.get('error')}"
    )
    if result["success"]:
        assert result["data"]["data_count"] > 0, (
            f"Should have data. Got: {result['data'].get('data_count')} rows"
        )


def test_fetch_ohlc_batch():
    """Test batch fetching OHLC data."""
    print("=" * 60)
    print("Test 4: Fetch Batch OHLC (USDJPY, EURUSD)")
    print("=" * 60)

    requests = [
        {"pair": "USDJPY", "interval": "1d", "period": "5d"},
        {"pair": "EURUSD", "interval": "1d", "period": "5d"},
    ]

    result = get_ohlc_batch(
        requests=requests,
        exclude_weekends=True,
    )

    print(f"Success: {result['success']}")

    if result["success"]:
        stats = result["statistics"]
        print(f"Total Requested: {stats['total_requested']}")
        print(f"Total Succeeded: {stats['total_succeeded']}")
        print(f"Total Failed: {stats['total_failed']}")
        print(f"Summary: {result['summary']}")

        print("\nSuccessful Results:")
        for i, data in enumerate(result["successful"], 1):
            print(
                f"  {i}. {data['pair']} - {data['interval']} - {data['data_count']} rows"
            )

        if result["failed"]:
            print("\nFailed Results:")
            for i, error in enumerate(result["failed"], 1):
                print(
                    f"  {i}. {error['pair']} - {error['type']}: {error['message']}"
                )
    else:
        print(f"Error Type: {result['error']['type']}")
        print(f"Error Message: {result['error']['message']}")

    print()
    assert result["success"], (
        f"get_ohlc_batch should succeed. Error: {result.get('error')}"
    )
    if result["success"]:
        assert result["statistics"]["total_succeeded"] > 0, (
            "Should have at least one success. "
            f"Succeeded: {result['statistics']['total_succeeded']}, "
            f"Failed: {result['statistics']['total_failed']}"
        )


def main() -> None:
    """Run all tests in a standalone script mode."""
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

    except AssertionError as e:  # pragma: no cover - manual script mode
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:  # pragma: no cover - manual script mode
        print("=" * 60)
        print(f"❌ Unexpected error: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - manual script mode
    main()


