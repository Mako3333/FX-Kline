"""
MCP Tools Implementation for FX-Kline

Defines the MCP tools that interact with the core FX-Kline functionality.
"""

from typing import Any, Dict, List
from datetime import datetime

from ..core import (
    OHLCRequest,
    fetch_batch_ohlc_sync,
    get_supported_pairs,
    get_preset_pairs,
    get_supported_timeframes,
    get_preset_timeframes,
)

# Maximum number of requests allowed in a single batch
MAX_BATCH_SIZE = 50

# Supported interval ranges for specialized tools
INTRADAY_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "4h"}
DAILY_INTERVALS = {"1d", "1wk", "1mo"}


def _categorize_error(error_type: str) -> str:
    """
    Categorize error type into high-level categories.

    Args:
        error_type: Specific error type

    Returns:
        Error category: ClientError, ServerError, or DataError
    """
    client_errors = {"ValidationError", "BatchSizeExceeded"}
    data_errors = {"NoDataAvailable", "AllWeekendData", "NoOHLCColumns"}

    if error_type in client_errors:
        return "ClientError"
    elif error_type in data_errors:
        return "DataError"
    else:
        return "ServerError"


def _generate_hint(error_type: str) -> str:
    """
    Generate recovery hint based on error type.

    Args:
        error_type: Specific error type

    Returns:
        Hint message for error recovery
    """
    hints = {
        "ValidationError": "Call 'list_pairs' or 'list_timeframes' to see supported values",
        "BatchSizeExceeded": f"Reduce the number of requests to {MAX_BATCH_SIZE} or fewer and try again",
        "NoDataAvailable": "Try extending the time period or choosing a different interval",
        "AllWeekendData": "Extend the time period to include weekdays, or set exclude_weekends=false",
        "NoOHLCColumns": "This may be a temporary issue with the data source. Try again later",
        "UnexpectedError": "Check the error message for details and try again",
    }
    return hints.get(error_type, "Review the error message and adjust your request")


def _is_recoverable(error_type: str) -> bool:
    """
    Determine if an error is recoverable through user action.

    Args:
        error_type: Specific error type

    Returns:
        True if the error can be recovered from
    """
    recoverable_errors = {
        "ValidationError",
        "BatchSizeExceeded",
        "NoDataAvailable",
        "AllWeekendData",
    }
    return error_type in recoverable_errors


def _suggest_tools(error_type: str) -> List[str]:
    """
    Suggest tools that might help recover from the error.

    Args:
        error_type: Specific error type

    Returns:
        List of suggested tool names
    """
    suggestions = {
        "ValidationError": ["list_pairs", "list_timeframes"],
        "NoDataAvailable": [],
        "AllWeekendData": [],
        "BatchSizeExceeded": [],
        "NoOHLCColumns": [],
        "UnexpectedError": [],
    }
    return suggestions.get(error_type, [])


def _normalize_datetime(obj: Any) -> Any:
    """
    Recursively normalize datetime objects to ISO format strings for JSON serialization.

    Args:
        obj: Object to normalize

    Returns:
        Normalized object with datetime converted to ISO format strings
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _normalize_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_normalize_datetime(item) for item in obj]
    else:
        return obj


def fetch_ohlc_tool(
    pair: str,
    interval: str = "1d",
    period: str = "30d",
    exclude_weekends: bool = True
) -> Dict[str, Any]:
    """
    Fetch OHLC data for a single currency pair and timeframe.

    Args:
        pair: Currency pair code (e.g., "USDJPY", "EURUSD", "XAUUSD")
        interval: Timeframe (e.g., "1m", "5m", "15m", "1h", "1d")
        period: Time period (e.g., "1d", "5d", "30d", "3mo")
        exclude_weekends: Filter out weekend data (default: True)

    Returns:
        Dictionary containing OHLC data or error information
    """
    try:
        request = OHLCRequest(pair=pair, interval=interval, period=period)
        response = fetch_batch_ohlc_sync([request], exclude_weekends=exclude_weekends)

        if response.total_succeeded > 0:
            ohlc_data = response.successful[0]
            result = {
                "success": True,
                "data": {
                    "pair": ohlc_data.pair,
                    "interval": ohlc_data.interval,
                    "period": ohlc_data.period,
                    "data_count": ohlc_data.data_count,
                    "timestamp_jst": ohlc_data.timestamp_jst,
                    "columns": ohlc_data.columns,
                    "rows": ohlc_data.rows,
                }
            }
            return _normalize_datetime(result)
        else:
            error = response.failed[0]
            error_type = error.error_type
            result = {
                "success": False,
                "error": {
                    "type": error_type,
                    "category": _categorize_error(error_type),
                    "message": error.error_message,
                    "hint": _generate_hint(error_type),
                    "recoverable": _is_recoverable(error_type),
                    "suggested_tools": _suggest_tools(error_type),
                    "context": {
                        "pair": error.pair,
                        "interval": error.interval,
                        "period": error.period,
                    }
                }
            }
            return _normalize_datetime(result)
    except Exception as e:
        error_type = "UnexpectedError"
        result = {
            "success": False,
            "error": {
                "type": error_type,
                "category": _categorize_error(error_type),
                "message": str(e),
                "hint": _generate_hint(error_type),
                "recoverable": _is_recoverable(error_type),
                "suggested_tools": _suggest_tools(error_type),
                "context": {
                    "pair": pair,
                    "interval": interval,
                    "period": period,
                }
            }
        }
        return _normalize_datetime(result)


def fetch_ohlc_batch_tool(
    requests: List[Dict[str, str]],
    exclude_weekends: bool = True
) -> Dict[str, Any]:
    """
    Fetch OHLC data for multiple currency pairs and timeframes in parallel.

    Args:
        requests: List of request dictionaries, each containing:
            - pair: Currency pair code
            - interval: Timeframe
            - period: Time period
        exclude_weekends: Filter out weekend data (default: True)

    Returns:
        Dictionary containing batch results with successful and failed requests

    Example:
        requests = [
            {"pair": "USDJPY", "interval": "1d", "period": "30d"},
            {"pair": "EURUSD", "interval": "1h", "period": "5d"},
        ]
    """
    try:
        # Validate batch size to prevent excessive API requests
        if len(requests) > MAX_BATCH_SIZE:
            error_type = "BatchSizeExceeded"
            result = {
                "success": False,
                "error": {
                    "type": error_type,
                    "category": _categorize_error(error_type),
                    "message": f"Batch size ({len(requests)}) exceeds maximum allowed ({MAX_BATCH_SIZE})",
                    "hint": _generate_hint(error_type),
                    "recoverable": _is_recoverable(error_type),
                    "suggested_tools": _suggest_tools(error_type),
                    "context": {
                        "max_batch_size": MAX_BATCH_SIZE,
                        "requested_size": len(requests),
                    }
                }
            }
            return _normalize_datetime(result)

        ohlc_requests = [
            OHLCRequest(
                pair=req["pair"],
                interval=req.get("interval", "1d"),
                period=req.get("period", "30d")
            )
            for req in requests
        ]

        response = fetch_batch_ohlc_sync(ohlc_requests, exclude_weekends=exclude_weekends)

        successful_data = [
            {
                "pair": ohlc.pair,
                "interval": ohlc.interval,
                "period": ohlc.period,
                "data_count": ohlc.data_count,
                "timestamp_jst": ohlc.timestamp_jst,
                "columns": ohlc.columns,
                "rows": ohlc.rows,
            }
            for ohlc in response.successful
        ]

        failed_data = [
            {
                "type": error.error_type,
                "category": _categorize_error(error.error_type),
                "message": error.error_message,
                "hint": _generate_hint(error.error_type),
                "recoverable": _is_recoverable(error.error_type),
                "suggested_tools": _suggest_tools(error.error_type),
                "context": {
                    "pair": error.pair,
                    "interval": error.interval,
                    "period": error.period,
                    "timestamp": error.timestamp,
                }
            }
            for error in response.failed
        ]

        result = {
            "success": True,
            "summary": response.summary,
            "successful": successful_data,
            "failed": failed_data,
            "statistics": {
                "total_requested": response.total_requested,
                "total_succeeded": response.total_succeeded,
                "total_failed": response.total_failed,
            }
        }
        return _normalize_datetime(result)
    except Exception as e:
        error_type = "UnexpectedError"
        result = {
            "success": False,
            "error": {
                "type": error_type,
                "category": _categorize_error(error_type),
                "message": str(e),
                "hint": _generate_hint(error_type),
                "recoverable": _is_recoverable(error_type),
                "suggested_tools": _suggest_tools(error_type),
                "context": {}
            }
        }
        return _normalize_datetime(result)


def get_intraday_ohlc(
    pair: str,
    interval: str = "1h",
    period: str = "5d",
    exclude_weekends: bool = True
) -> Dict[str, Any]:
    """
    Fetch intraday OHLC data for scalping and day trading (1m-4h intervals).

    Args:
        pair: Currency pair code (e.g., "USDJPY", "EURUSD", "XAUUSD")
        interval: Intraday timeframe (1m, 5m, 15m, 30m, 1h, 4h)
        period: Time period (e.g., "1d", "5d", "30d")
        exclude_weekends: Filter out weekend data (default: True)

    Returns:
        Dictionary containing OHLC data or error information
    """
    try:
        # Validate interval is intraday
        if interval.lower() not in INTRADAY_INTERVALS:
            error_type = "ValidationError"
            valid_intervals = ", ".join(sorted(INTRADAY_INTERVALS))
            result = {
                "success": False,
                "error": {
                    "type": error_type,
                    "category": _categorize_error(error_type),
                    "message": f"Invalid intraday interval: {interval}. This tool only supports intraday intervals.",
                    "hint": f"Use one of: {valid_intervals}. For daily/weekly/monthly data, use 'get_daily_ohlc' instead.",
                    "recoverable": True,
                    "suggested_tools": ["list_available_timeframes", "get_daily_ohlc"],
                    "context": {
                        "attempted_interval": interval,
                        "valid_intervals": list(INTRADAY_INTERVALS),
                        "pair": pair,
                    }
                }
            }
            return _normalize_datetime(result)

        request = OHLCRequest(pair=pair, interval=interval, period=period)
        response = fetch_batch_ohlc_sync([request], exclude_weekends=exclude_weekends)

        if response.total_succeeded > 0:
            ohlc_data = response.successful[0]
            result = {
                "success": True,
                "data": {
                    "pair": ohlc_data.pair,
                    "interval": ohlc_data.interval,
                    "period": ohlc_data.period,
                    "data_count": ohlc_data.data_count,
                    "timestamp_jst": ohlc_data.timestamp_jst,
                    "columns": ohlc_data.columns,
                    "rows": ohlc_data.rows,
                }
            }
            return _normalize_datetime(result)
        else:
            error = response.failed[0]
            error_type = error.error_type
            result = {
                "success": False,
                "error": {
                    "type": error_type,
                    "category": _categorize_error(error_type),
                    "message": error.error_message,
                    "hint": _generate_hint(error_type),
                    "recoverable": _is_recoverable(error_type),
                    "suggested_tools": _suggest_tools(error_type),
                    "context": {
                        "pair": error.pair,
                        "interval": error.interval,
                        "period": error.period,
                    }
                }
            }
            return _normalize_datetime(result)
    except Exception as e:
        error_type = "UnexpectedError"
        result = {
            "success": False,
            "error": {
                "type": error_type,
                "category": _categorize_error(error_type),
                "message": str(e),
                "hint": _generate_hint(error_type),
                "recoverable": _is_recoverable(error_type),
                "suggested_tools": _suggest_tools(error_type),
                "context": {
                    "pair": pair,
                    "interval": interval,
                    "period": period,
                }
            }
        }
        return _normalize_datetime(result)


def get_daily_ohlc(
    pair: str,
    interval: str = "1d",
    period: str = "30d",
    exclude_weekends: bool = True
) -> Dict[str, Any]:
    """
    Fetch daily/weekly/monthly OHLC data for swing and position trading.

    Args:
        pair: Currency pair code (e.g., "USDJPY", "EURUSD", "XAUUSD")
        interval: Daily timeframe (1d, 1wk, 1mo)
        period: Time period (e.g., "30d", "3mo", "1y")
        exclude_weekends: Filter out weekend data (default: True)

    Returns:
        Dictionary containing OHLC data or error information
    """
    try:
        # Validate interval is daily/weekly/monthly
        if interval.lower() not in DAILY_INTERVALS:
            error_type = "ValidationError"
            valid_intervals = ", ".join(sorted(DAILY_INTERVALS))
            result = {
                "success": False,
                "error": {
                    "type": error_type,
                    "category": _categorize_error(error_type),
                    "message": f"Invalid daily interval: {interval}. This tool only supports daily/weekly/monthly intervals.",
                    "hint": f"Use one of: {valid_intervals}. For intraday data, use 'get_intraday_ohlc' instead.",
                    "recoverable": True,
                    "suggested_tools": ["list_available_timeframes", "get_intraday_ohlc"],
                    "context": {
                        "attempted_interval": interval,
                        "valid_intervals": list(DAILY_INTERVALS),
                        "pair": pair,
                    }
                }
            }
            return _normalize_datetime(result)

        request = OHLCRequest(pair=pair, interval=interval, period=period)
        response = fetch_batch_ohlc_sync([request], exclude_weekends=exclude_weekends)

        if response.total_succeeded > 0:
            ohlc_data = response.successful[0]
            result = {
                "success": True,
                "data": {
                    "pair": ohlc_data.pair,
                    "interval": ohlc_data.interval,
                    "period": ohlc_data.period,
                    "data_count": ohlc_data.data_count,
                    "timestamp_jst": ohlc_data.timestamp_jst,
                    "columns": ohlc_data.columns,
                    "rows": ohlc_data.rows,
                }
            }
            return _normalize_datetime(result)
        else:
            error = response.failed[0]
            error_type = error.error_type
            result = {
                "success": False,
                "error": {
                    "type": error_type,
                    "category": _categorize_error(error_type),
                    "message": error.error_message,
                    "hint": _generate_hint(error_type),
                    "recoverable": _is_recoverable(error_type),
                    "suggested_tools": _suggest_tools(error_type),
                    "context": {
                        "pair": error.pair,
                        "interval": error.interval,
                        "period": error.period,
                    }
                }
            }
            return _normalize_datetime(result)
    except Exception as e:
        error_type = "UnexpectedError"
        result = {
            "success": False,
            "error": {
                "type": error_type,
                "category": _categorize_error(error_type),
                "message": str(e),
                "hint": _generate_hint(error_type),
                "recoverable": _is_recoverable(error_type),
                "suggested_tools": _suggest_tools(error_type),
                "context": {
                    "pair": pair,
                    "interval": interval,
                    "period": period,
                }
            }
        }
        return _normalize_datetime(result)


def list_available_pairs_tool(preset_only: bool = False) -> Dict[str, Any]:
    """
    List all available currency pairs.

    Args:
        preset_only: If True, return only preset pairs (default: False)

    Returns:
        Dictionary containing list of currency pairs
    """
    try:
        if preset_only:
            pairs = get_preset_pairs()
        else:
            pairs = get_supported_pairs()

        result = {
            "success": True,
            "pairs": pairs,
            "count": len(pairs),
        }
        return _normalize_datetime(result)
    except Exception as e:
        error_type = "UnexpectedError"
        result = {
            "success": False,
            "error": {
                "type": error_type,
                "category": _categorize_error(error_type),
                "message": str(e),
                "hint": _generate_hint(error_type),
                "recoverable": _is_recoverable(error_type),
                "suggested_tools": _suggest_tools(error_type),
                "context": {}
            }
        }
        return _normalize_datetime(result)


def list_available_timeframes_tool(preset_only: bool = False) -> Dict[str, Any]:
    """
    List all available timeframes.

    Args:
        preset_only: If True, return only preset timeframes (default: False)

    Returns:
        Dictionary containing list of timeframes
    """
    try:
        if preset_only:
            timeframes = get_preset_timeframes()
        else:
            timeframes = get_supported_timeframes()

        result = {
            "success": True,
            "timeframes": timeframes,
            "count": len(timeframes),
        }
        return _normalize_datetime(result)
    except Exception as e:
        error_type = "UnexpectedError"
        result = {
            "success": False,
            "error": {
                "type": error_type,
                "category": _categorize_error(error_type),
                "message": str(e),
                "hint": _generate_hint(error_type),
                "recoverable": _is_recoverable(error_type),
                "suggested_tools": _suggest_tools(error_type),
                "context": {}
            }
        }
        return _normalize_datetime(result)


# New simplified tool names (aliases for better UX)
def get_ohlc_batch(
    requests: List[Dict[str, str]],
    exclude_weekends: bool = True
) -> Dict[str, Any]:
    """
    Alias for fetch_ohlc_batch_tool with a simpler name.

    Fetch OHLC data for multiple currency pairs and timeframes in parallel.
    """
    return fetch_ohlc_batch_tool(requests, exclude_weekends)


def list_pairs(preset_only: bool = False) -> Dict[str, Any]:
    """
    Alias for list_available_pairs_tool with a simpler name.

    List all available currency pairs that can be fetched.
    """
    return list_available_pairs_tool(preset_only)


def list_timeframes(preset_only: bool = False) -> Dict[str, Any]:
    """
    Alias for list_available_timeframes_tool with a simpler name.

    List all available timeframes/intervals for data fetching.
    """
    return list_available_timeframes_tool(preset_only)


def ping() -> Dict[str, Any]:
    """
    Health check endpoint to verify server connectivity and capabilities.

    Returns:
        Dictionary containing server status and capabilities
    """
    try:
        from importlib.metadata import version, PackageNotFoundError
        from datetime import datetime, timezone

        # Get version
        try:
            server_version = version("fx-kline")
        except PackageNotFoundError:
            server_version = "0.1.0"

        # Get current timestamp
        current_time = datetime.now(timezone.utc)

        # Get supported pairs and timeframes counts
        all_pairs = get_supported_pairs()
        all_timeframes = get_supported_timeframes()

        result = {
            "success": True,
            "server": "fx-kline",
            "version": server_version,
            "status": "healthy",
            "timestamp": current_time.isoformat(),
            "capabilities": {
                "supported_pairs": len(all_pairs),
                "supported_timeframes": len(all_timeframes),
                "max_batch_size": MAX_BATCH_SIZE,
                "features": [
                    "intraday_ohlc",
                    "daily_ohlc",
                    "batch_requests",
                    "weekend_filtering",
                    "jst_timezone",
                ]
            },
            "endpoints": {
                "data_fetching": ["get_intraday_ohlc", "get_daily_ohlc", "get_ohlc_batch"],
                "metadata": ["list_pairs", "list_timeframes"],
                "health": ["ping"],
                "deprecated": ["fetch_ohlc", "fetch_ohlc_batch", "list_available_pairs", "list_available_timeframes"]
            }
        }
        return _normalize_datetime(result)
    except Exception as e:
        error_type = "UnexpectedError"
        result = {
            "success": False,
            "error": {
                "type": error_type,
                "category": _categorize_error(error_type),
                "message": str(e),
                "hint": "Server health check failed. Please check server logs.",
                "recoverable": False,
                "suggested_tools": [],
                "context": {}
            }
        }
        return _normalize_datetime(result)
