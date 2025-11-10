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

# Note: This path manipulation is required when the package is not installed in editable mode.
# Without this, `uv run python run_mcp_server.py` would fail with ModuleNotFoundError.
# Alternative: Install package in editable mode with `uv pip install -e .`
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fx_kline.mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())
