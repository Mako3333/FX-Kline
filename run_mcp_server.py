#!/usr/bin/env python3
"""
Entry point for running the FX-Kline MCP server.

Usage:
    python run_mcp_server.py

Or with uv:
    uv run python run_mcp_server.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fx_kline.mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())
