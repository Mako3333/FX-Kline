"""
MCP Server Implementation for FX-Kline

Provides Model Context Protocol server functionality for fetching FX OHLC data.
"""

import asyncio
import json
from typing import Any, Dict

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types

from .tools import (
    fetch_ohlc_tool,
    fetch_ohlc_batch_tool,
    list_available_pairs_tool,
    list_available_timeframes_tool,
)


# Create MCP server instance
server = Server("fx-kline")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available MCP tools.

    Returns:
        List of tool definitions
    """
    return [
        types.Tool(
            name="fetch_ohlc",
            description=(
                "Fetch OHLC (Open-High-Low-Close) data for a single FX currency pair. "
                "Supports multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d) and automatically "
                "converts to JST timezone with business day filtering. "
                "Available pairs: USDJPY, EURUSD, GBPUSD, AUDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD (Gold)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pair": {
                        "type": "string",
                        "description": "Currency pair code (e.g., USDJPY, EURUSD, XAUUSD)",
                    },
                    "interval": {
                        "type": "string",
                        "description": "Timeframe interval (e.g., 1m, 5m, 15m, 1h, 4h, 1d)",
                        "default": "1d",
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period to fetch (e.g., 1d, 5d, 30d, 3mo, 1y)",
                        "default": "30d",
                    },
                    "exclude_weekends": {
                        "type": "boolean",
                        "description": "Filter out weekend data (default: true)",
                        "default": True,
                    },
                },
                "required": ["pair"],
            },
        ),
        types.Tool(
            name="fetch_ohlc_batch",
            description=(
                "Fetch OHLC data for multiple currency pairs and timeframes in parallel. "
                "More efficient than multiple single requests. Returns aggregated results "
                "with success/failure statistics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "requests": {
                        "type": "array",
                        "description": "Array of fetch requests",
                        "items": {
                            "type": "object",
                            "properties": {
                                "pair": {
                                    "type": "string",
                                    "description": "Currency pair code",
                                },
                                "interval": {
                                    "type": "string",
                                    "description": "Timeframe interval",
                                    "default": "1d",
                                },
                                "period": {
                                    "type": "string",
                                    "description": "Time period to fetch",
                                    "default": "30d",
                                },
                            },
                            "required": ["pair"],
                        },
                    },
                    "exclude_weekends": {
                        "type": "boolean",
                        "description": "Filter out weekend data (default: true)",
                        "default": True,
                    },
                },
                "required": ["requests"],
            },
        ),
        types.Tool(
            name="list_available_pairs",
            description=(
                "List all available currency pairs that can be fetched. "
                "Includes major FX pairs and commodities like Gold (XAUUSD)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "preset_only": {
                        "type": "boolean",
                        "description": "Return only preset pairs (default: false)",
                        "default": False,
                    },
                },
            },
        ),
        types.Tool(
            name="list_available_timeframes",
            description=(
                "List all available timeframes/intervals for data fetching. "
                "Ranges from 1-minute to monthly data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "preset_only": {
                        "type": "boolean",
                        "description": "Return only preset timeframes (default: false)",
                        "default": False,
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of content items with tool results
    """
    if arguments is None:
        arguments = {}

    try:
        if name == "fetch_ohlc":
            result = fetch_ohlc_tool(
                pair=arguments["pair"],
                interval=arguments.get("interval", "1d"),
                period=arguments.get("period", "30d"),
                exclude_weekends=arguments.get("exclude_weekends", True),
            )
        elif name == "fetch_ohlc_batch":
            result = fetch_ohlc_batch_tool(
                requests=arguments["requests"],
                exclude_weekends=arguments.get("exclude_weekends", True),
            )
        elif name == "list_available_pairs":
            result = list_available_pairs_tool(
                preset_only=arguments.get("preset_only", False)
            )
        elif name == "list_available_timeframes":
            result = list_available_timeframes_tool(
                preset_only=arguments.get("preset_only", False)
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [
            types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]
    except Exception as e:
        error_result = {
            "success": False,
            "error": {
                "type": "ToolExecutionError",
                "message": str(e),
                "tool": name,
            }
        }
        return [
            types.TextContent(
                type="text",
                text=json.dumps(error_result, indent=2, ensure_ascii=False)
            )
        ]


async def main():
    """
    Main entry point for the MCP server.

    Runs the server using stdio transport.
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fx-kline",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
