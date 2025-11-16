"""
MCP Server Implementation for FX-Kline

Provides Model Context Protocol server functionality for fetching FX OHLC data.
"""

import asyncio
import json
import logging
from importlib.metadata import version, PackageNotFoundError

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types
from mcp.types import ToolAnnotations

from .tools import (
    fetch_ohlc_tool,
    fetch_ohlc_batch_tool,
    list_available_pairs_tool,
    list_available_timeframes_tool,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
                "\n\n"
                "Supports multiple timeframes (1m-1mo) and automatically converts to JST timezone "
                "with business day filtering. "
                "\n\n"
                "When to use: Single pair analysis, chart visualization, technical indicator calculation. "
                "For multiple pairs, use 'fetch_ohlc_batch' for better performance. "
                "\n\n"
                "Tip: If you're unsure about supported pairs or timeframes, call "
                "'list_available_pairs' or 'list_available_timeframes' first. "
                "\n\n"
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
            annotations=ToolAnnotations(
                title="FX OHLC データ取得",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="fetch_ohlc_batch",
            description=(
                "Fetch OHLC data for multiple currency pairs and timeframes in parallel. "
                "\n\n"
                "More efficient than multiple single 'fetch_ohlc' calls. Returns aggregated results "
                "with detailed success/failure statistics. Maximum 50 requests per batch. "
                "\n\n"
                "When to use: Multi-pair correlation analysis, portfolio analysis, market overview, "
                "comparing multiple timeframes for the same pair. "
                "\n\n"
                "Tip: Batch requests are processed in parallel for optimal performance. "
                "Failed requests don't affect successful ones."
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
            annotations=ToolAnnotations(
                title="FX OHLC バッチ取得",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="list_available_pairs",
            description=(
                "List all available currency pairs that can be fetched. "
                "\n\n"
                "Returns a complete list of supported pairs with their full names. "
                "Includes major FX pairs (USD, EUR, GBP, AUD crosses) and commodities (Gold). "
                "\n\n"
                "When to use: Before calling fetch_ohlc/fetch_ohlc_batch to validate pair names, "
                "for UI dropdowns, to discover available pairs, or when you encounter a ValidationError. "
                "\n\n"
                "Tip: Call this tool first when you're unsure which currency pairs are supported."
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
            annotations=ToolAnnotations(
                title="対応通貨ペア一覧",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=False,
            ),
        ),
        types.Tool(
            name="list_available_timeframes",
            description=(
                "List all available timeframes/intervals for data fetching. "
                "\n\n"
                "Returns supported intervals ranging from 1-minute (1m) to monthly (1mo) data. "
                "Includes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1wk, 1mo. "
                "\n\n"
                "When to use: Before calling fetch_ohlc/fetch_ohlc_batch to validate interval values, "
                "for UI dropdowns, to discover available timeframes, or when you encounter a ValidationError. "
                "\n\n"
                "Tip: Shorter timeframes (1m-4h) are for intraday analysis, longer ones (1d-1mo) "
                "for swing/position trading."
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
            annotations=ToolAnnotations(
                title="対応時間足一覧",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=False,
            ),
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
            # Validate required parameters
            if "pair" not in arguments:
                raise ValueError("Missing required parameter: pair")

            result = fetch_ohlc_tool(
                pair=arguments["pair"],
                interval=arguments.get("interval", "1d"),
                period=arguments.get("period", "30d"),
                exclude_weekends=arguments.get("exclude_weekends", True),
            )
        elif name == "fetch_ohlc_batch":
            # Validate required parameters
            if "requests" not in arguments:
                raise ValueError("Missing required parameter: requests")

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
        # Log the error with full traceback
        logger.exception(
            f"Error executing tool '{name}' with arguments {arguments}: {str(e)}"
        )

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
    # Get version dynamically from package metadata
    try:
        server_version = version("fx-kline")
    except PackageNotFoundError:
        # Fallback to hardcoded version if package is not installed
        server_version = "0.1.0"
        logger.warning("Package 'fx-kline' not found in metadata, using fallback version")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fx-kline",
                server_version=server_version,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
