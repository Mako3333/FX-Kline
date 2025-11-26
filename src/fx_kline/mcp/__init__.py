"""
FX-Kline MCP package.

This package exposes:
    - `fx_kline.mcp.tools`: MCP tool implementations (pure functions)
    - `fx_kline.mcp.server`: MCP server wiring and stdio entrypoint

The server module is intentionally not imported at package import time
to avoid side effects (e.g., constructing a Server instance) during
test discovery or when only the tools are needed.
"""

from . import tools

__all__ = ["tools"]
