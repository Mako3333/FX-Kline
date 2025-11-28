"""
Data fetcher for FX OHLC data using yfinance
Supports parallel fetching with business day filtering and JST timezone conversion
"""

import asyncio
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

from .business_days import filter_business_days_fx, get_business_days_back
from .models import BatchOHLCResponse, FetchError, OHLCData, OHLCRequest
from .validators import validate_currency_pair, validate_period, validate_timeframe
from .timezone_utils import convert_dataframe_to_jst, get_jst_now, JST_TZ

logger = logging.getLogger(__name__)

# Thread pool for async yfinance calls
# NOTE: max_workers=1 to avoid yfinance parallel execution bug
# yfinance is not thread-safe and returns incorrect data when called in parallel
# See: https://github.com/ranaroussi/yfinance/issues (known issue)
_executor = ThreadPoolExecutor(max_workers=1)

_PERIOD_PATTERN = re.compile(r"^(\d+)([a-z]+)$")
_INTERVAL_PATTERN = re.compile(r"^(\d+)([a-z]+)$")


def _download_with_period(pair: str, interval: str, period: str) -> pd.DataFrame:
    """Fetch data from yfinance using period-based window."""
    return yf.download(
        pair,
        interval=interval,
        period=period,
        auto_adjust=False,
        progress=False
    )


def _download_with_fallback_window(pair: str, interval: str, business_days: int) -> pd.DataFrame:
    """Fetch data using an explicit date window when period-based fetch under-delivers."""
    end_jst = get_jst_now()
    # Pad the lookback so we have slack for holidays and API quirks
    buffer_days = max(2, business_days // 2)
    lookback_days = business_days + buffer_days
    start_jst = get_business_days_back(lookback_days, end_jst)

    start_utc = start_jst.astimezone(timezone.utc)
    end_utc = end_jst.astimezone(timezone.utc)

    return yf.download(
        pair,
        interval=interval,
        start=start_utc,
        end=end_utc,
        auto_adjust=False,
        progress=False
    )


def _prepare_dataframe(df: pd.DataFrame, interval: str, symbol: str, exclude_weekends: bool) -> pd.DataFrame:
    """Apply weekend filtering, flatten columns, and convert to JST."""
    if df.empty:
        return df

    processed = df.copy()

    # Flatten multi-index columns first (before timezone conversion)
    if isinstance(processed.columns, pd.MultiIndex):
        processed.columns = processed.columns.get_level_values(0)

    if processed.empty:
        return processed

    # Convert to JST timezone
    processed = convert_dataframe_to_jst(processed)

    if processed.empty:
        return processed

    # Apply market-specific weekend filtering (after timezone conversion to JST)
    if exclude_weekends:
        processed = filter_business_days_fx(processed, interval, symbol)

    return processed


def _extract_business_days(period: str) -> Optional[int]:
    """Extract desired business-day lookback from a period string like '5d'."""
    match = _PERIOD_PATTERN.match(period)
    if not match:
        return None

    value, unit = match.groups()
    if unit != "d":
        return None

    try:
        days = int(value)
    except ValueError:
        return None

    return days if days > 0 else None


def _parse_interval(interval: str) -> Tuple[Optional[int], Optional[str]]:
    """Extract numeric value and unit suffix from an interval string."""
    match = _INTERVAL_PATTERN.match(interval)
    if not match:
        return None, None

    value_str, unit = match.groups()
    try:
        value = int(value_str)
    except ValueError:
        return None, unit

    return value, unit


def _count_unique_business_days(df: pd.DataFrame) -> int:
    """Count the number of distinct business days represented in JST."""
    if df.empty:
        return 0

    normalized = df.index.normalize()
    try:
        return len(normalized.unique())
    except Exception:
        return len(set(normalized))


def fetch_ohlc_range_dataframe(
    pair: str,
    interval: str,
    start: datetime,
    end: datetime,
    exclude_weekends: bool = True,
) -> pd.DataFrame:
    """
    Fetch OHLC data for a specific start/end window, returned as a JST-indexed DataFrame.

    Args:
        pair: Currency pair code (e.g., 'USDJPY')
        interval: Timeframe (e.g., '1h', '15m', '1d')
        start: Start datetime (timezone-aware preferred, naive datetimes assumed to be JST)
        end: End datetime (timezone-aware preferred, naive datetimes assumed to be JST)
        exclude_weekends: Filter out weekend data

    Returns:
        DataFrame with JST-indexed DatetimeIndex
    """
    pair_formatted = validate_currency_pair(pair)
    interval_validated = validate_timeframe(interval)

    # Handle naive datetimes by assuming they are JST (project standard)
    if start.tzinfo is None:
        start = JST_TZ.localize(start)
    if end.tzinfo is None:
        end = JST_TZ.localize(end)

    start_utc = start.astimezone(timezone.utc)
    end_utc = end.astimezone(timezone.utc)

    df = yf.download(
        pair_formatted,
        interval=interval_validated,
        start=start_utc,
        end=end_utc,
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        return df

    return _prepare_dataframe(df, interval_validated, pair_formatted, exclude_weekends)


def fetch_single_ohlc(
    pair: str,
    interval: str,
    period: str,
    exclude_weekends: bool = True
) -> Tuple[Optional[OHLCData], Optional[FetchError]]:
    """
    Fetch OHLC data for a single currency pair (synchronous)

    Args:
        pair: Currency pair code (e.g., 'USDJPY')
        interval: Timeframe (e.g., '1h', '1d')
        period: Period (e.g., '30d')
        exclude_weekends: Filter out weekend data

    Returns:
        Tuple of (OHLCData or None, FetchError or None)
        One will be populated, the other None
    """
    try:
        # Validate inputs
        pair_formatted = validate_currency_pair(pair)
        interval_validated = validate_timeframe(interval)
        period_validated = validate_period(period)

        expected_business_days = _extract_business_days(period_validated)
        interval_value, interval_unit = _parse_interval(interval_validated)
        is_minute_interval = interval_unit == "m"

        # Fetch data from yfinance
        df = _download_with_period(pair_formatted, interval_validated, period_validated)
        raw_data_present = not df.empty

        df_jst = _prepare_dataframe(df, interval_validated, pair_formatted, exclude_weekends)

        # Attempt fallback if coverage is clearly insufficient
        if (
            not is_minute_interval
            and expected_business_days is not None
            and _count_unique_business_days(df_jst) < expected_business_days
        ):
            df_fallback = _download_with_fallback_window(pair_formatted, interval_validated, expected_business_days)
            raw_data_present = raw_data_present or not df_fallback.empty
            df_fallback_jst = _prepare_dataframe(df_fallback, interval_validated, pair_formatted, exclude_weekends)

            if _count_unique_business_days(df_fallback_jst) >= _count_unique_business_days(df_jst):
                df_jst = df_fallback_jst.copy()
            elif df_jst.empty and not df_fallback_jst.empty:
                df_jst = df_fallback_jst.copy()

        # Handle empty data
        if df_jst.empty:
            error_type = "AllWeekendData" if raw_data_present and exclude_weekends else "NoDataAvailable"
            error = FetchError(
                pair=pair,
                interval=interval,
                period=period,
                error_type=error_type,
                error_message=f"No data available for {pair} with interval {interval} and period {period}"
            )
            return None, error

        # Trim to the requested number of business days (if applicable)
        if expected_business_days is not None and not df_jst.empty:
            normalized_index = df_jst.index.normalize()
            unique_days = normalized_index.unique()
            if len(unique_days) > expected_business_days:
                keep_days = set(unique_days[-expected_business_days:])
                df_jst = df_jst[normalized_index.isin(keep_days)]

        # Prepare OHLC data
        ohlc_columns = []
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df_jst.columns:
                ohlc_columns.append(col)

        if 'Volume' in df_jst.columns:
            ohlc_columns.append('Volume')

        if not ohlc_columns:
            error = FetchError(
                pair=pair,
                interval=interval,
                period=period,
                error_type="NoOHLCColumns",
                error_message=f"No OHLC columns found in fetched data."
            )
            return None, error

        df_ohlc = df_jst[ohlc_columns].copy()

        # Convert DataFrame to list of dicts
        rows = []
        for idx, row in df_ohlc.iterrows():
            try:
                row_dict = {
                    'Datetime': idx.strftime('%Y-%m-%d %H:%M:%S %Z') if hasattr(idx, 'strftime') else str(idx),
                    'Open': float(row['Open']) if 'Open' in ohlc_columns else 0.0,
                    'High': float(row['High']) if 'High' in ohlc_columns else 0.0,
                    'Low': float(row['Low']) if 'Low' in ohlc_columns else 0.0,
                    'Close': float(row['Close']) if 'Close' in ohlc_columns else 0.0,
                }
                if 'Volume' in ohlc_columns:
                    row_dict['Volume'] = int(row['Volume']) if pd.notna(row['Volume']) else 0
                rows.append(row_dict)
            except Exception as e:
                # Log and skip rows with errors
                logger.debug(f"Skipping row {idx} due to conversion error: {e}")
                continue

        if not rows:
            error = FetchError(
                pair=pair,
                interval=interval,
                period=period,
                error_type="NoDataAvailable",
                error_message=f"No valid OHLC rows generated for {pair} ({interval}/{period})"
            )
            return None, error

        ohlc_data = OHLCData(
            pair=pair,
            interval=interval,
            period=period,
            data_count=len(rows),
            columns=ohlc_columns,
            rows=rows,
            timestamp_jst=get_jst_now()
        )

        return ohlc_data, None

    except Exception as e:
        error = FetchError(
            pair=pair,
            interval=interval,
            period=period,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        return None, error


async def fetch_single_ohlc_async(
    pair: str,
    interval: str,
    period: str,
    exclude_weekends: bool = True
) -> Tuple[Optional[OHLCData], Optional[FetchError]]:
    """
    Async wrapper for single OHLC fetch

    Args:
        pair: Currency pair code
        interval: Timeframe
        period: Period
        exclude_weekends: Filter out weekend data

    Returns:
        Tuple of (OHLCData or None, FetchError or None)
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        fetch_single_ohlc,
        pair,
        interval,
        period,
        exclude_weekends
    )


async def fetch_batch_ohlc(
    requests: List[OHLCRequest],
    exclude_weekends: bool = True
) -> BatchOHLCResponse:
    """
    Fetch OHLC data for multiple currency pairs in parallel

    Args:
        requests: List of OHLCRequest objects
        exclude_weekends: Filter out weekend data for all requests

    Returns:
        BatchOHLCResponse with successful and failed requests
    """
    # Create async tasks
    tasks = [
        fetch_single_ohlc_async(req.pair, req.interval, req.period, exclude_weekends)
        for req in requests
    ]

    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Separate successes and failures
    successful = []
    failed = []

    for result in results:
        ohlc_data, error = result
        if ohlc_data:
            successful.append(ohlc_data)
        elif error:
            failed.append(error)

    # Create response
    response = BatchOHLCResponse(
        successful=successful,
        failed=failed,
        total_requested=len(requests),
        total_succeeded=len(successful),
        total_failed=len(failed)
    )

    return response


def fetch_batch_ohlc_sync(
    requests: List[OHLCRequest],
    exclude_weekends: bool = True
) -> BatchOHLCResponse:
    """
    Synchronous wrapper for batch OHLC fetch

    Args:
        requests: List of OHLCRequest objects
        exclude_weekends: Filter out weekend data for all requests

    Returns:
        BatchOHLCResponse with successful and failed requests
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(fetch_batch_ohlc(requests, exclude_weekends))
    finally:
        loop.close()


def export_to_csv(ohlc_data: OHLCData) -> str:
    """
    Export OHLC data to CSV format

    Args:
        ohlc_data: OHLCData object

    Returns:
        CSV string
    """
    # Create DataFrame from rows
    df = pd.DataFrame(ohlc_data.rows)

    # Convert to CSV
    csv_string = df.to_csv(index=False)
    return csv_string


def export_to_json(ohlc_data: OHLCData) -> str:
    """
    Export OHLC data to JSON format

    Args:
        ohlc_data: OHLCData object

    Returns:
        JSON string
    """
    import json

    # Convert to dict and then to JSON
    data_dict = {
        "pair": ohlc_data.pair,
        "interval": ohlc_data.interval,
        "period": ohlc_data.period,
        "data_count": ohlc_data.data_count,
        "rows": ohlc_data.rows
    }

    return json.dumps(data_dict, indent=2, ensure_ascii=False)


def export_to_csv_string(ohlc_data: OHLCData, include_header: bool = True) -> str:
    """
    Export OHLC data to comma-separated string (for clipboard)

    Args:
        ohlc_data: OHLCData object
        include_header: Include header row

    Returns:
        Comma-separated string
    """
    lines = []

    if include_header and ohlc_data.rows:
        # Get column names from first row
        header = ",".join(ohlc_data.rows[0].keys())
        lines.append(header)

    # Add data rows
    for row in ohlc_data.rows:
        values = [str(v) for v in row.values()]
        lines.append(",".join(values))

    return "\n".join(lines)


def get_batch_csv_export(response: BatchOHLCResponse) -> Dict[str, str]:
    """
    Export all successful batch results to CSV

    Args:
        response: BatchOHLCResponse object

    Returns:
        Dictionary with pair as key and CSV string as value
    """
    exports = {}
    for ohlc_data in response.successful:
        key = f"{ohlc_data.pair}_{ohlc_data.interval}_{ohlc_data.period}"
        exports[key] = export_to_csv(ohlc_data)

    return exports


def get_batch_json_export(response: BatchOHLCResponse) -> str:
    """
    Export all successful batch results to JSON

    Args:
        response: BatchOHLCResponse object

    Returns:
        JSON string with all results
    """
    import json

    data = {
        "summary": response.summary,
        "successful": [
            {
                "pair": ohlc.pair,
                "interval": ohlc.interval,
                "period": ohlc.period,
                "data_count": ohlc.data_count,
                "rows": ohlc.rows
            }
            for ohlc in response.successful
        ],
        "failed": [
            {
                "pair": err.pair,
                "interval": err.interval,
                "period": err.period,
                "error_type": err.error_type,
                "error_message": err.error_message
            }
            for err in response.failed
        ]
    }

    return json.dumps(data, indent=2, ensure_ascii=False)
