"""
MCP Server Implementation for FX-Kline

Provides Model Context Protocol server functionality for fetching FX OHLC data.
"""

import asyncio
import json
import logging
from importlib.metadata import version, PackageNotFoundError
from typing import Any

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
    get_intraday_ohlc,
    get_daily_ohlc,
    get_ohlc_batch,
    list_pairs,
    list_timeframes,
    ping,
    INTRADAY_INTERVALS,
    DAILY_INTERVALS,
)
from ..core import get_supported_pairs, get_supported_timeframes


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
            name="get_intraday_ohlc",
            description=(
                "Fetch intraday OHLC data for scalping and day trading (1m-4h intervals only). "
                "\n\n"
                "This tool is specialized for intraday analysis with minute and hour-based intervals. "
                "It validates that the interval is appropriate for intraday trading. "
                "\n\n"
                "Supported intervals: 1m, 5m, 15m, 30m, 1h, 4h. "
                "\n\n"
                "When to use: Scalping analysis, day trading strategies, intraday technical indicators, "
                "real-time market monitoring. "
                "\n\n"
                "For daily/weekly/monthly data, use 'get_daily_ohlc' instead. "
                "\n\n"
                "Tip: This tool will return a clear error if you try to use daily intervals, "
                "guiding you to the correct tool."
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
                        "description": "Intraday interval: 1m, 5m, 15m, 30m, 1h, or 4h",
                        "default": "1h",
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period to fetch (e.g., 1d, 5d, 30d)",
                        "default": "5d",
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
                title="日中足OHLC取得（スキャルピング・デイトレード用）",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="get_daily_ohlc",
            description=(
                "Fetch daily/weekly/monthly OHLC data for swing and position trading. "
                "\n\n"
                "This tool is specialized for longer-term analysis with daily, weekly, and monthly intervals. "
                "It validates that the interval is appropriate for swing/position trading. "
                "\n\n"
                "Supported intervals: 1d, 1wk, 1mo. "
                "\n\n"
                "When to use: Swing trading, position trading, long-term trend analysis, "
                "monthly/quarterly reports. "
                "\n\n"
                "For intraday data (1m-4h), use 'get_intraday_ohlc' instead. "
                "\n\n"
                "Tip: This tool will return a clear error if you try to use intraday intervals, "
                "guiding you to the correct tool."
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
                        "description": "Daily interval: 1d, 1wk, or 1mo",
                        "default": "1d",
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period to fetch (e.g., 30d, 3mo, 1y)",
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
                title="日足以上OHLC取得（スイング・ポジション取引用）",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="fetch_ohlc",
            description=(
                "⚠️ DEPRECATED: Use 'get_intraday_ohlc' or 'get_daily_ohlc' instead. "
                "This tool will be removed in 6 months (2026-05-16). "
                "\n\n"
                "Fetch OHLC (Open-High-Low-Close) data for a single FX currency pair. "
                "\n\n"
                "Migration guide: "
                "For intraday intervals (1m-4h), use 'get_intraday_ohlc'. "
                "For daily intervals (1d, 1wk, 1mo), use 'get_daily_ohlc'. "
                "\n\n"
                "Supports multiple timeframes (1m-1mo) and automatically converts to JST timezone "
                "with business day filtering. "
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
                "⚠️ DEPRECATED: Use 'get_ohlc_batch' instead. "
                "This tool will be removed in 6 months (2026-05-16). "
                "\n\n"
                "Fetch OHLC data for multiple currency pairs and timeframes in parallel. "
                "\n\n"
                "Migration guide: Simply rename 'fetch_ohlc_batch' to 'get_ohlc_batch'. "
                "The parameters and behavior are identical. "
                "\n\n"
                "More efficient than multiple single calls. Returns aggregated results "
                "with detailed success/failure statistics. Maximum 50 requests per batch."
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
                "⚠️ DEPRECATED: Use 'list_pairs' instead. "
                "This tool will be removed in 6 months (2026-05-16). "
                "\n\n"
                "List all available currency pairs that can be fetched. "
                "\n\n"
                "Migration guide: Simply rename 'list_available_pairs' to 'list_pairs'. "
                "The parameters and behavior are identical. "
                "\n\n"
                "Returns a complete list of supported pairs with their full names. "
                "Includes major FX pairs (USD, EUR, GBP, AUD crosses) and commodities (Gold)."
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
                "⚠️ DEPRECATED: Use 'list_timeframes' instead. "
                "This tool will be removed in 6 months (2026-05-16). "
                "\n\n"
                "List all available timeframes/intervals for data fetching. "
                "\n\n"
                "Migration guide: Simply rename 'list_available_timeframes' to 'list_timeframes'. "
                "The parameters and behavior are identical. "
                "\n\n"
                "Returns supported intervals ranging from 1-minute (1m) to monthly (1mo) data. "
                "Includes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1wk, 1mo."
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
        types.Tool(
            name="get_ohlc_batch",
            description=(
                "Fetch OHLC data for multiple currency pairs and timeframes in parallel (simplified name). "
                "\n\n"
                "More efficient than multiple single calls. Returns aggregated results "
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
                title="OHLC バッチ取得",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="list_pairs",
            description=(
                "List all available currency pairs (simplified name). "
                "\n\n"
                "Returns a complete list of supported pairs with their full names. "
                "Includes major FX pairs (USD, EUR, GBP, AUD crosses) and commodities (Gold). "
                "\n\n"
                "When to use: Before calling any OHLC fetch tools to validate pair names, "
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
                title="通貨ペア一覧",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=False,
            ),
        ),
        types.Tool(
            name="list_timeframes",
            description=(
                "List all available timeframes/intervals (simplified name). "
                "\n\n"
                "Returns supported intervals ranging from 1-minute (1m) to monthly (1mo) data. "
                "Includes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1wk, 1mo. "
                "\n\n"
                "When to use: Before calling any OHLC fetch tools to validate interval values, "
                "for UI dropdowns, to discover available timeframes, or when you encounter a ValidationError. "
                "\n\n"
                "Tip: Shorter timeframes (1m-4h) are for intraday analysis, longer ones (1d-1mo) "
                "for swing/position trading. Use 'get_intraday_ohlc' for 1m-4h and 'get_daily_ohlc' for 1d-1mo."
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
                title="時間足一覧",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=False,
            ),
        ),
        types.Tool(
            name="ping",
            description=(
                "Health check and server capabilities endpoint. "
                "\n\n"
                "Returns server status, version, supported features, and available endpoints. "
                "Useful for debugging connectivity issues and discovering server capabilities. "
                "\n\n"
                "When to use: Connection testing, debugging, discovering available features, "
                "monitoring server health. "
                "\n\n"
                "Returns: Server version, timestamp, capabilities (supported pairs/timeframes count, "
                "max batch size), feature list, and endpoint categories (data_fetching, metadata, health, deprecated)."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
            annotations=ToolAnnotations(
                title="サーバーヘルスチェック",
                readOnlyHint=True,
                idempotentHint=True,
                openWorldHint=False,
            ),
        ),
    ]


def _to_bool(value: Any, default: bool) -> bool:
    """
    Convert argument value to boolean, handling string representations.

    This helper ensures backward compatibility with clients that may send
    boolean parameters as strings ("true"/"false") instead of actual booleans.

    Args:
        value: The value to convert (bool, str, or None)
        default: Default value if value is None

    Returns:
        Boolean value

    Examples:
        >>> _to_bool(True, False)
        True
        >>> _to_bool("true", False)
        True
        >>> _to_bool("false", True)
        False
        >>> _to_bool(None, True)
        True
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    # For other types, use Python's truthiness
    return bool(value)


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
        if name == "get_intraday_ohlc":
            # Validate required parameters
            if "pair" not in arguments:
                raise ValueError("Missing required parameter: pair")

            result = get_intraday_ohlc(
                pair=arguments["pair"],
                interval=arguments.get("interval", "1h"),
                period=arguments.get("period", "5d"),
                exclude_weekends=_to_bool(arguments.get("exclude_weekends"), True),
            )
        elif name == "get_daily_ohlc":
            # Validate required parameters
            if "pair" not in arguments:
                raise ValueError("Missing required parameter: pair")

            result = get_daily_ohlc(
                pair=arguments["pair"],
                interval=arguments.get("interval", "1d"),
                period=arguments.get("period", "30d"),
                exclude_weekends=_to_bool(arguments.get("exclude_weekends"), True),
            )
        elif name == "fetch_ohlc":
            # Validate required parameters
            if "pair" not in arguments:
                raise ValueError("Missing required parameter: pair")

            result = fetch_ohlc_tool(
                pair=arguments["pair"],
                interval=arguments.get("interval", "1d"),
                period=arguments.get("period", "30d"),
                exclude_weekends=_to_bool(arguments.get("exclude_weekends"), True),
            )
        elif name == "fetch_ohlc_batch":
            # Validate required parameters
            if "requests" not in arguments:
                raise ValueError("Missing required parameter: requests")

            result = fetch_ohlc_batch_tool(
                requests=arguments["requests"],
                exclude_weekends=_to_bool(arguments.get("exclude_weekends"), True),
            )
        elif name == "list_available_pairs":
            result = list_available_pairs_tool(
                preset_only=_to_bool(arguments.get("preset_only"), False)
            )
        elif name == "list_available_timeframes":
            result = list_available_timeframes_tool(
                preset_only=_to_bool(arguments.get("preset_only"), False)
            )
        elif name == "get_ohlc_batch":
            # Validate required parameters
            if "requests" not in arguments:
                raise ValueError("Missing required parameter: requests")

            result = get_ohlc_batch(
                requests=arguments["requests"],
                exclude_weekends=_to_bool(arguments.get("exclude_weekends"), True),
            )
        elif name == "list_pairs":
            result = list_pairs(
                preset_only=_to_bool(arguments.get("preset_only"), False)
            )
        elif name == "list_timeframes":
            result = list_timeframes(
                preset_only=_to_bool(arguments.get("preset_only"), False)
            )
        elif name == "ping":
            result = ping()
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


@server.set_completions()
async def handle_completions(
    ref: types.CompletionRef,
) -> list[types.Completion]:
    """
    Provide argument completion suggestions for tools.

    Args:
        ref: Completion reference containing tool name and argument name

    Returns:
        List of completion suggestions
    """
    # Completion for 'pair' parameter (all data fetching tools)
    if ref.argument == "pair":
        pairs = get_supported_pairs()
        return [
            types.Completion(
                value=pair_code,
                label=f"{pair_code} - {description}",
                description=description
            )
            for pair_code, description in pairs.items()
        ]

    # Completion for 'interval' parameter
    if ref.argument == "interval":
        # Tool-specific interval suggestions
        if ref.name == "get_intraday_ohlc":
            # Only intraday intervals (1m-4h)
            intervals = sorted(INTRADAY_INTERVALS)
            descriptions = {
                "1m": "1 minute - Ultra short-term scalping",
                "5m": "5 minutes - Short-term scalping",
                "15m": "15 minutes - Scalping/Day trading",
                "30m": "30 minutes - Day trading",
                "1h": "1 hour - Day trading (recommended)",
                "4h": "4 hours - Swing day trading",
            }
        elif ref.name == "get_daily_ohlc":
            # Only daily+ intervals (1d, 1wk, 1mo)
            intervals = sorted(DAILY_INTERVALS)
            descriptions = {
                "1d": "1 day - Daily analysis (recommended)",
                "1wk": "1 week - Weekly trends",
                "1mo": "1 month - Monthly trends",
            }
        else:
            # All intervals for deprecated/batch tools
            timeframes = get_supported_timeframes()
            return [
                types.Completion(
                    value=interval,
                    label=f"{interval} - {description}",
                    description=description
                )
                for interval, description in timeframes.items()
            ]

        return [
            types.Completion(
                value=interval,
                label=f"{interval} - {descriptions.get(interval, interval)}",
                description=descriptions.get(interval, interval)
            )
            for interval in intervals
        ]

    # Completion for 'period' parameter
    if ref.argument == "period":
        # Common period values with descriptions
        period_suggestions = [
            ("1d", "1 day - Very short term"),
            ("5d", "5 days - Short term"),
            ("30d", "30 days - Medium term (recommended)"),
            ("3mo", "3 months - Quarterly"),
            ("6mo", "6 months - Semi-annual"),
            ("1y", "1 year - Annual"),
            ("2y", "2 years - Long term"),
            ("5y", "5 years - Very long term"),
            ("ytd", "Year to date"),
            ("max", "Maximum available data"),
        ]

        return [
            types.Completion(
                value=period,
                label=f"{period} - {description}",
                description=description
            )
            for period, description in period_suggestions
        ]

    # Completion for 'preset_only' parameter
    if ref.argument == "preset_only":
        return [
            types.Completion(
                value=False,
                label="false - All available (default)",
                description="Return all supported pairs/timeframes"
            ),
            types.Completion(
                value=True,
                label="true - Preset only",
                description="Return only preset pairs/timeframes for UI"
            ),
        ]

    # Completion for 'exclude_weekends' parameter
    if ref.argument == "exclude_weekends":
        return [
            types.Completion(
                value=True,
                label="true - Exclude weekends (default)",
                description="Filter out weekend data for cleaner analysis"
            ),
            types.Completion(
                value=False,
                label="false - Include weekends",
                description="Include all data including weekends"
            ),
        ]

    # No completions for other parameters
    return []


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
