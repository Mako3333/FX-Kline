#!/usr/bin/env python3
"""
CLI wrapper for consolidating multi-timeframe analysis reports.

Consolidates individual timeframe analysis JSON files into unified summary files
per currency pair for comprehensive market environment understanding.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_kline.core import summary_consolidator

if __name__ == "__main__":
    raise SystemExit(summary_consolidator.main())
