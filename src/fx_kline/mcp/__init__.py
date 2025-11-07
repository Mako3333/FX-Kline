"""
FX-Kline MCP Server Module

This module provides Model Context Protocol (MCP) server functionality
for fetching FX OHLC data through Claude Desktop and other MCP clients.
"""

from .server import main

__all__ = ["main"]
