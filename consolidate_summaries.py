#!/usr/bin/env python3
"""
CLI wrapper for consolidating multi-timeframe analysis reports.

Consolidates individual timeframe analysis JSON files into unified summary files
per currency pair for comprehensive market environment understanding.
"""

from fx_kline.core import summary_consolidator

if __name__ == "__main__":
    raise SystemExit(summary_consolidator.main())
