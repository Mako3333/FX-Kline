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
            result = {
                "success": False,
                "error": {
                    "type": error.error_type,
                    "message": error.error_message,
                    "pair": error.pair,
                    "interval": error.interval,
                    "period": error.period,
                }
            }
            return _normalize_datetime(result)
    except Exception as e:
        result = {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": str(e),
                "pair": pair,
                "interval": interval,
                "period": period,
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
            result = {
                "success": False,
                "error": {
                    "type": "BatchSizeExceeded",
                    "message": f"Batch size ({len(requests)}) exceeds maximum allowed ({MAX_BATCH_SIZE})",
                    "max_batch_size": MAX_BATCH_SIZE,
                    "requested_size": len(requests),
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
                "message": error.error_message,
                "pair": error.pair,
                "interval": error.interval,
                "period": error.period,
                "timestamp": error.timestamp,
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
        result = {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": str(e),
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
        result = {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": str(e),
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
        result = {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": str(e),
            }
        }
        return _normalize_datetime(result)
