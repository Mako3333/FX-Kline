"""
Aggregate OHLC CSV files and compute lightweight technical indicators.

Outputs a JSON document (schema_version=1) per input file with:
    - trend
    - support/resistance levels
    - RSI14
    - ATR14
    - average volatility
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .timezone_utils import get_jst_now

# Expected column names (normalized to lowercase)
_EXPECTED_COLUMNS = {"datetime", "open", "high", "low", "close", "volume"}
_FILENAME_PATTERN = re.compile(
    r"^(?P<pair>[A-Za-z]+)_(?P<interval>\d+[a-zA-Z]+)_(?P<period>\d+[a-zA-Z]+)$"
)
_TREND_THRESHOLD = 0.002  # ~0.2% drift threshold before calling UP/DOWN

# Support/Resistance detection constants
INTRADAY_LOOKBACK_BARS = 240  # ~10 business days for 1h interval
FOUR_HOUR_LOOKBACK_BARS = 84  # ~2 weeks for 4h interval (14 days * 6 bars/day)
DAILY_LOOKBACK_BARS = 60  # ~30-60 business days for 1d interval

INTRADAY_REVERSAL_HOURS = 5  # Hours to confirm reversal
DAILY_REVERSAL_CANDLES = 3  # Consecutive candles for reversal
DAILY_PRICE_TOLERANCE_RATE = 0.005  # 0.5% tolerance for 1d levels (percentage-based)

# 4H fallback merge tolerance (5 pips / 0.05 yen for JPY pairs)
FOUR_HOUR_MERGE_TOLERANCE = 0.05

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    pair: str
    interval: str
    period: str
    trend: str
    support_levels: List[float]
    resistance_levels: List[float]
    rsi: Optional[float]
    atr: Optional[float]
    average_volatility: Optional[float]
    generated_at: str
    schema_version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


def parse_metadata_from_filename(file_path: Path) -> Tuple[str, str, str]:
    """
    Extract pair, interval, and period from a CSV filename.
    Expected pattern: <PAIR>_<INTERVAL>_<PERIOD>.csv (e.g., USDJPY_1h_10d.csv)
    """
    match = _FILENAME_PATTERN.match(file_path.stem)
    if not match:
        raise ValueError(
            f"Filename '{file_path.name}' does not match '<PAIR>_<INTERVAL>_<PERIOD>.csv'"
        )

    pair = match.group("pair").upper()
    interval = match.group("interval")
    period = match.group("period")
    return pair, interval, period


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip column names for consistent downstream access."""
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


def load_ohlc_csv(file_path: Path) -> pd.DataFrame:
    """Load a CSV containing datetime, open, high, low, close, volume."""
    df = pd.read_csv(file_path)
    df = _normalize_columns(df)

    missing = _EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns {sorted(missing)} in {file_path.name}")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df = df.dropna(subset=["datetime"])

    for price_col in ["open", "high", "low", "close", "volume"]:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])

    return df.sort_values("datetime").reset_index(drop=True)


def detect_trend(closes: pd.Series) -> str:
    """
    Decide UP/DOWN/SIDEWAYS based on start-end drift and a smoothed slope.
    Falls back to SIDEWAYS when data is insufficient or movement is tiny.
    """
    closes = closes.dropna()
    if closes.shape[0] < 2:
        return "SIDEWAYS"

    start = closes.iloc[0]
    end = closes.iloc[-1]

    if start == 0:
        return "SIDEWAYS"

    pct_change = (end - start) / start

    window = max(3, min(20, closes.shape[0]))
    rolling_mean = closes.rolling(window=window, min_periods=max(2, window // 2)).mean().dropna()

    slope_ratio = 0.0
    if rolling_mean.shape[0] >= 2 and rolling_mean.iloc[0] != 0:
        slope_ratio = (rolling_mean.iloc[-1] - rolling_mean.iloc[0]) / rolling_mean.iloc[0]

    blended = 0.6 * pct_change + 0.4 * slope_ratio

    if blended > _TREND_THRESHOLD:
        return "UP"
    if blended < -_TREND_THRESHOLD:
        return "DOWN"
    return "SIDEWAYS"


def _get_time_column(df: pd.DataFrame) -> str:
    if "datetime" in df.columns:
        return "datetime"
    if "timestamp" in df.columns:
        return "timestamp"
    raise ValueError("DataFrame must include a 'datetime' or 'timestamp' column")


def _rank_levels(
    candidates: List[Tuple[float, pd.Timestamp]],
    last_close: float,
    max_levels: int,
    *,
    sort_desc: bool,
    mode: str = "distance",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[float]:
    """
    Pick levels based on priority mode with optional price constraints.

    Args:
        candidates: List of (price, timestamp) tuples
        last_close: Current price for proximity ranking
        max_levels: Maximum number of levels to return
        sort_desc: If True, sort output descending (for resistances)
        mode: "distance" (prioritize proximity to current price) or
              "structure_first" (prioritize structural/historical importance)
        min_price: If set, exclude candidates below this price (for resistances)
        max_price: If set, exclude candidates above this price (for supports)

    Returns:
        List of selected price levels, sorted for readability
    """
    if not candidates:
        return []

    # Deduplicate candidates
    seen = set()
    unique: List[Tuple[float, pd.Timestamp]] = []
    for price, ts in candidates:
        rounded = round(float(price), 4)
        key = f"{rounded:.4f}"
        if key in seen:
            continue
        seen.add(key)
        unique.append((rounded, pd.Timestamp(ts)))

    # Apply price constraints (filter before ranking)
    filtered = unique
    if min_price is not None:
        filtered = [(p, ts) for p, ts in filtered if p >= min_price]
    if max_price is not None:
        filtered = [(p, ts) for p, ts in filtered if p <= max_price]

    # Fallback: if filtering removes all candidates, use unfiltered top result
    # This ensures we always return at least something when candidates exist
    if not filtered and unique:
        filtered = unique[:1]

    # Sort based on mode
    if mode == "structure_first":
        # Structure priority: older levels first (necklines), then proximity
        ranked = sorted(filtered, key=lambda item: (item[1].timestamp(), abs(item[0] - last_close)))
    else:  # mode == "distance"
        # Distance priority: closest to current price first, then recency
        ranked = sorted(filtered, key=lambda item: (abs(item[0] - last_close), -item[1].timestamp()))

    selected = [price for price, _ in ranked[:max_levels]]
    return sorted(selected, reverse=sort_desc)


def _fallback_extremes(df: pd.DataFrame, levels: int) -> Tuple[List[float], List[float]]:
    """
    Fallback method to extract simple extremes when no reversal patterns detected.

    This is used when interval-specific algorithms fail to find qualified levels,
    or when the interval is not recognized. Returns the N lowest lows and N highest
    highs from the provided DataFrame.

    Args:
        df: OHLC DataFrame
        levels: Number of extreme levels to extract per side

    Returns:
        Tuple of (support_levels, resistance_levels)
    """
    lows = df["low"].dropna()
    highs = df["high"].dropna()
    supports = sorted(lows.nsmallest(levels).round(4).tolist())
    resistances = sorted(highs.nlargest(levels).round(4).tolist(), reverse=True)
    return supports, resistances


def _merge_nearby_levels(
    levels: List[float],
    all_values: pd.Series,
    tolerance: float,
    is_support: bool,
) -> List[float]:
    """
    Merge nearby levels that are too close together and find alternatives.

    When two levels are within the tolerance threshold, keep the more extreme one
    and try to find an alternative level that is sufficiently distant.

    Args:
        levels: List of price levels (supports sorted ascending, resistances descending)
        all_values: Full series of prices to search for alternatives (lows for support, highs for resistance)
        tolerance: Minimum distance required between levels
        is_support: True for support levels (find lower alternatives), False for resistance

    Returns:
        List of merged/deduped price levels
    """
    if len(levels) < 2:
        return levels

    result: List[float] = [levels[0]]

    for candidate in levels[1:]:
        # Check if candidate is too close to any existing result level
        too_close = any(abs(candidate - existing) < tolerance for existing in result)
        if not too_close:
            result.append(candidate)

    # If we lost levels due to merging, try to find alternatives
    if len(result) < len(levels):
        all_sorted = sorted(all_values.round(4).unique(), reverse=not is_support)
        for alt in all_sorted:
            if len(result) >= len(levels):
                break
            # Check if this alternative is sufficiently distant from all existing levels
            if all(abs(alt - existing) >= tolerance for existing in result):
                result.append(alt)

    # Re-sort the result
    result = sorted(result, reverse=not is_support)
    return result


def _compute_intraday_reversals(
    df: pd.DataFrame, ts_col: str, levels: int, last_close: float
) -> Tuple[List[float], List[float]]:
    """
    Detect intraday support/resistance for 1-hour timeframe.

    Algorithm:
        1. Analyze last ~10 business days (240 bars for 1h interval)
        2. Group bars by session date
        3. Identify each day's high and low
        4. Confirm reversal if price doesn't return for 5+ hours after high/low

    Args:
        df: OHLC DataFrame with datetime column
        ts_col: Name of the timestamp column
        levels: Maximum number of levels to return per side
        last_close: Current price for proximity ranking

    Returns:
        Tuple of (support_levels, resistance_levels)
    """
    window = df.tail(INTRADAY_LOOKBACK_BARS).copy()
    window["session_date"] = window[ts_col].dt.date

    support_candidates: List[Tuple[float, pd.Timestamp]] = []
    resistance_candidates: List[Tuple[float, pd.Timestamp]] = []

    for session_date in sorted(window["session_date"].unique(), reverse=True):
        daily = window[window["session_date"] == session_date]
        if daily.empty:
            continue

        high_idx = daily["high"].idxmax()
        low_idx = daily["low"].idxmin()

        high_time = window.loc[high_idx, ts_col]
        low_time = window.loc[low_idx, ts_col]

        day_high = float(window.loc[high_idx, "high"])
        day_low = float(window.loc[low_idx, "low"])

        # Check if high was not revisited in the next 5 hours
        post_high = window[window[ts_col] > high_time].head(INTRADAY_REVERSAL_HOURS)
        if post_high.shape[0] >= INTRADAY_REVERSAL_HOURS and post_high["high"].max() < day_high:
            resistance_candidates.append((day_high, pd.Timestamp(high_time)))

        # Check if low was not revisited in the next 5 hours
        post_low = window[window[ts_col] > low_time].head(INTRADAY_REVERSAL_HOURS)
        if post_low.shape[0] >= INTRADAY_REVERSAL_HOURS and post_low["low"].min() > day_low:
            support_candidates.append((day_low, pd.Timestamp(low_time)))

    # For supports: no upper constraint (can be below current price)
    supports = _rank_levels(
        support_candidates, last_close, levels, sort_desc=False, max_price=last_close
    )

    # For resistances: must be above current price to be valid resistance
    # Also ensure resistance is above the highest support to maintain structural integrity
    min_resistance_price = last_close
    if supports:
        min_resistance_price = max(min_resistance_price, max(supports))

    resistances = _rank_levels(
        resistance_candidates, last_close, levels, sort_desc=True, min_price=min_resistance_price
    )
    return supports, resistances


def _compute_four_hour_levels(
    df: pd.DataFrame, ts_col: str, levels: int, last_close: float
) -> Tuple[List[float], List[float]]:
    """
    Detect 4-hour support/resistance using weekly neckline logic.

    Algorithm:
        1. Analyze last ~2-4 weeks (60 bars for 4h interval)
        2. Group by week (W-SUN)
        3. Compare last week vs previous week
        4. Higher-high breakout → both weeks' highs/lows as candidates
        5. Lower-low breakdown → both weeks' highs/lows as candidates
        6. Prioritize structural levels (necklines) over price proximity

    Args:
        df: OHLC DataFrame with datetime column
        ts_col: Name of the timestamp column
        levels: Maximum number of levels to return per side
        last_close: Current price for proximity ranking

    Returns:
        Tuple of (support_levels, resistance_levels) sorted for readability
    """
    window = df.tail(FOUR_HOUR_LOOKBACK_BARS).copy()
    # Note: to_period("W-SUN") drops timezone info, but this is acceptable for weekly grouping
    window["week"] = window[ts_col].dt.to_period("W-SUN")

    weekly = (
        window.groupby("week")
        .agg(
            week_high=("high", "max"),
            week_low=("low", "min"),
            week_end=(ts_col, "max"),
        )
        .reset_index()
        .sort_values("week")
    )

    support_candidates: List[Tuple[float, pd.Timestamp]] = []
    resistance_candidates: List[Tuple[float, pd.Timestamp]] = []

    if weekly.shape[0] >= 2:
        last_week = weekly.iloc[-1]
        prev_week = weekly.iloc[-2]

        # Collect candidates from all weeks for structure-first ranking
        if last_week.week_high > prev_week.week_high:
            # Higher-high breakout: collect all weekly lows and highs
            for _, week_row in weekly.iterrows():
                support_candidates.append((float(week_row.week_low), pd.Timestamp(week_row.week_end)))
                resistance_candidates.append((float(week_row.week_high), pd.Timestamp(week_row.week_end)))
        elif last_week.week_low < prev_week.week_low:
            # Lower-low breakdown: collect all weekly lows and highs
            for _, week_row in weekly.iterrows():
                support_candidates.append((float(week_row.week_low), pd.Timestamp(week_row.week_end)))
                resistance_candidates.append((float(week_row.week_high), pd.Timestamp(week_row.week_end)))

    # Fallback to simple extremes if no structural levels found
    if not support_candidates and not resistance_candidates:
        supports, resistances = _fallback_extremes(window, levels)
        # Merge nearby levels to avoid redundant information
        # (e.g., 152.814 and 152.826 are effectively the same level)
        supports = _merge_nearby_levels(
            supports, window["low"], FOUR_HOUR_MERGE_TOLERANCE, is_support=True
        )
        resistances = _merge_nearby_levels(
            resistances, window["high"], FOUR_HOUR_MERGE_TOLERANCE, is_support=False
        )
        return supports, resistances

    # Use structure_first mode to prioritize necklines over proximity
    supports = _rank_levels(support_candidates, last_close, levels, sort_desc=False, mode="structure_first")
    resistances = _rank_levels(resistance_candidates, last_close, levels, sort_desc=True, mode="structure_first")
    return supports, resistances


def _compute_daily_reversals(
    df: pd.DataFrame, ts_col: str, levels: int, last_close: float
) -> Tuple[List[float], List[float]]:
    """
    Detect daily support/resistance with three-candle reversal confirmation.

    Algorithm:
        1. Analyze last ~30-60 business days (60 bars for 1d interval)
        2. Filter to levels within ±0.5% of current price
        3. High followed by 3 consecutive bearish candles → resistance
        4. Low followed by 3 consecutive bullish candles → support
        5. Prioritize oldest/deepest reversals (structural importance)

    Args:
        df: OHLC DataFrame with datetime column
        ts_col: Name of the timestamp column
        levels: Maximum number of levels to return per side
        last_close: Current price for proximity ranking

    Returns:
        Tuple of (support_levels, resistance_levels)
        May return fewer than 'levels' if only limited qualified candidates exist
    """
    window = df.tail(DAILY_LOOKBACK_BARS).copy()
    tolerance = last_close * DAILY_PRICE_TOLERANCE_RATE

    support_candidates: List[Tuple[float, pd.Timestamp]] = []
    resistance_candidates: List[Tuple[float, pd.Timestamp]] = []

    for idx in range(window.shape[0] - DAILY_REVERSAL_CANDLES):
        current_row = window.iloc[idx]
        next_slice = window.iloc[idx + 1 : idx + 1 + DAILY_REVERSAL_CANDLES]
        if next_slice.shape[0] < DAILY_REVERSAL_CANDLES:
            break

        is_bearish_follow_through = (
            next_slice["close"] < next_slice["open"]
        ).all()
        is_bullish_follow_through = (
            next_slice["close"] > next_slice["open"]
        ).all()

        high_price = float(current_row["high"])
        low_price = float(current_row["low"])
        timestamp = pd.Timestamp(current_row[ts_col])

        # Resistance: high within tolerance, followed by bearish reversal
        if (
            abs(high_price - last_close) <= tolerance
            and is_bearish_follow_through
        ):
            resistance_candidates.append((high_price, timestamp))

        # Support: low within tolerance, followed by bullish reversal
        if (
            abs(low_price - last_close) <= tolerance
            and is_bullish_follow_through
        ):
            support_candidates.append((low_price, timestamp))

    # Use structure_first mode to prioritize oldest/most structural reversals
    supports = _rank_levels(
        support_candidates, last_close, levels, sort_desc=False, mode="structure_first"
    )
    resistances = _rank_levels(
        resistance_candidates,
        last_close,
        levels,
        sort_desc=True,
        mode="structure_first",
    )

    # Fallback to simple extremes within lookback window if no qualified levels found
    # This ensures daily levels are always within the 60-bar window, not the full DataFrame
    if not supports:
        supports, _ = _fallback_extremes(window, levels)
    if not resistances:
        _, resistances = _fallback_extremes(window, levels)

    return supports, resistances


def compute_support_resistance(df: pd.DataFrame, interval: str, levels: int = 2) -> Tuple[List[float], List[float]]:
    """
    Detect support/resistance levels using interval-specific algorithms.

    Each timeframe uses a tailored reversal detection algorithm optimized for
    HITL (Human-In-The-Loop) trading decisions:

    - **1h (intraday)**: Time-priority approach
      - Analyzes last ~10 business days (240 bars)
      - Identifies daily highs/lows confirmed by 5+ hours of non-revisit
      - Prioritizes proximity to current price

    - **4h (swing)**: Structure-priority approach
      - Analyzes last ~2-4 weeks (60 bars)
      - Detects week-over-week breakouts/breakdowns
      - Prioritizes necklines and structural levels over proximity

    - **1d (position)**: Structure-priority approach
      - Analyzes last ~30-60 business days (60 bars)
      - Filters to levels within ±5 yen of current price
      - Confirms reversals with 3 consecutive candles
      - Prioritizes oldest/deepest reversals

    Args:
        df: OHLC DataFrame with columns [datetime/timestamp, open, high, low, close, volume]
        interval: Timeframe identifier ('1h', '4h', '1d', etc.)
        levels: Maximum number of levels to return per side (default: 2)

    Returns:
        Tuple of (support_levels, resistance_levels)
        - support_levels: List of price levels (sorted ascending)
        - resistance_levels: List of price levels (sorted descending)
        - May return fewer than 'levels' if limited qualified candidates exist
        - Returns empty lists if DataFrame is empty

    Fallback:
        - If no qualified levels found for one side, falls back to simple extremes
        - If interval is unrecognized, uses simple min/max extremes

    Example:
        >>> df = pd.read_csv("USDJPY_1h_10d.csv")
        >>> supports, resistances = compute_support_resistance(df, "1h", levels=2)
        >>> print(f"Support: {supports}, Resistance: {resistances}")
        Support: [149.20, 149.85], Resistance: [151.20, 150.95]
    """
    ts_col = _get_time_column(df)
    working = df.copy()
    working[ts_col] = pd.to_datetime(working[ts_col], errors="coerce", utc=True)
    working = working.dropna(subset=[ts_col, "high", "low", "close"]).sort_values(ts_col)

    if working.empty:
        return [], []

    last_close = float(working["close"].iloc[-1])

    interval_key = interval.lower()
    if interval_key == "1h":
        supports, resistances = _compute_intraday_reversals(working, ts_col, levels, last_close)
    elif interval_key == "4h":
        supports, resistances = _compute_four_hour_levels(working, ts_col, levels, last_close)
    elif interval_key == "1d":
        supports, resistances = _compute_daily_reversals(working, ts_col, levels, last_close)
    else:
        supports, resistances = _fallback_extremes(working, levels)

    # Fallback to extremes if no qualified levels were found for one side
    if not supports:
        supports, _ = _fallback_extremes(working, levels)
    if not resistances:
        _, resistances = _fallback_extremes(working, levels)

    return supports, resistances


def compute_rsi(closes: pd.Series, period: int = 14) -> Optional[float]:
    """Compute RSI using Wilder's smoothing approximation."""
    closes = closes.dropna()
    if closes.shape[0] < 2:
        return None

    delta = closes.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    # Wilder's smoothing (EWM): alpha = 1/period
    avg_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    avg_loss_safe = avg_loss.replace(0, np.nan)
    rs = avg_gain / avg_loss_safe
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan).dropna()

    if rsi.empty:
        # Handle edge cases: all gains, all losses, or flat series
        latest_gain = float(avg_gain.dropna().iloc[-1]) if not avg_gain.dropna().empty else 0.0
        latest_loss = float(avg_loss.dropna().iloc[-1]) if not avg_loss.dropna().empty else 0.0
        if latest_gain > 0 and latest_loss == 0:
            return 100.0
        if latest_loss > 0 and latest_gain == 0:
            return 0.0
        if latest_gain == 0 and latest_loss == 0:
            return 50.0
        # Fallback: both gain and loss are positive (shouldn't happen normally,
        # but compute RSI manually to avoid IndexError)
        if latest_gain > 0 and latest_loss > 0:
            rs_fallback = latest_gain / latest_loss
            rsi_fallback = 100 - (100 / (1 + rs_fallback))
            return round(float(rsi_fallback), 2)
        # Ultimate fallback: return None if we can't determine RSI
        return None

    return round(float(rsi.iloc[-1]), 2)


def compute_atr(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    """Average True Range over the provided lookback."""
    if df.shape[0] < 2:
        return None

    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.shift(1)
    tr_components = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    )
    true_range = tr_components.max(axis=1)

    atr_series = true_range.rolling(window=period, min_periods=min(period, len(true_range))).mean()
    atr_value = atr_series.dropna().iloc[-1] if not atr_series.dropna().empty else true_range.mean()

    if pd.isna(atr_value):
        return None
    return round(float(atr_value), 4)


def compute_average_volatility(df: pd.DataFrame) -> Optional[float]:
    """
    Average intrabar range (high-low). Falls back to std of returns if needed.
    """
    hl_range = (df["high"] - df["low"]).dropna()
    volatility = hl_range.mean() if not hl_range.empty else None

    if volatility is None or pd.isna(volatility):
        returns = df["close"].pct_change().dropna()
        volatility = returns.std() if not returns.empty else None

    if volatility is None or pd.isna(volatility):
        return None

    return round(float(volatility), 4)


def analyze_dataframe(df: pd.DataFrame, pair: str, interval: str, period: str) -> AnalysisResult:
    """Compute all analytics for a single OHLC dataframe."""
    trend = detect_trend(df["close"])
    support_levels, resistance_levels = compute_support_resistance(df, interval)
    rsi = compute_rsi(df["close"])
    atr = compute_atr(df)
    avg_volatility = compute_average_volatility(df)

    return AnalysisResult(
        pair=pair,
        interval=interval,
        period=period,
        trend=trend,
        support_levels=support_levels,
        resistance_levels=resistance_levels,
        rsi=rsi,
        atr=atr,
        average_volatility=avg_volatility,
        generated_at=get_jst_now().isoformat(),
    )


def analyze_file(file_path: Path) -> AnalysisResult:
    """Load CSV, infer metadata, and compute analytics."""
    pair, interval, period = parse_metadata_from_filename(file_path)
    df = load_ohlc_csv(file_path)

    if df.empty:
        raise ValueError(f"No data rows in {file_path.name}")

    return analyze_dataframe(df, pair, interval, period)


def _resolve_paths_from_patterns(patterns: Iterable[str]) -> List[Path]:
    """Expand glob patterns relative to CWD."""
    paths: List[Path] = []
    for pattern in patterns:
        matches = list(Path().glob(pattern))
        if matches:
            paths.extend(matches)
        else:
            candidate = Path(pattern)
            if candidate.exists():
                paths.append(candidate)
    return paths


def collect_input_files(input_dir: Optional[Path], glob_patterns: Sequence[str], extra_files: Sequence[str]) -> List[Path]:
    """
    Collect CSV paths from an input directory (with glob) plus any explicit file paths/globs.
    """
    paths: List[Path] = []

    if input_dir:
        for pattern in glob_patterns:
            paths.extend(sorted(input_dir.glob(pattern)))

    paths.extend(_resolve_paths_from_patterns(extra_files))

    # Deduplicate while preserving order
    unique_paths: List[Path] = []
    seen = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_paths.append(resolved)

    return unique_paths


def write_analysis(result: AnalysisResult, destination: Path) -> None:
    """Write analysis to JSON with stable formatting."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as fp:
        json.dump(result.to_dict(), fp, ensure_ascii=True, indent=2)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute technical summaries from OHLC CSV files and emit JSON reports."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing CSV files (used with --glob).",
    )
    parser.add_argument(
        "--glob",
        dest="glob_patterns",
        nargs="+",
        default=["*.csv"],
        help="Glob pattern(s) to select CSV files (default: *.csv).",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        default=[],
        help="Explicit CSV file paths or glob expressions (optional).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write JSON analysis outputs.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    input_files = collect_input_files(args.input_dir, args.glob_patterns, args.files)
    if not input_files:
        parser.error("No CSV files found. Provide --input-dir/--glob or --files.")

    written = 0
    for csv_path in input_files:
        if csv_path.suffix.lower() != ".csv":
            logger.debug("Skipping non-CSV file %s", csv_path)
            continue

        try:
            result = analyze_file(csv_path)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to analyze %s: %s", csv_path.name, exc)
            continue

        output_path = args.output_dir / f"{csv_path.stem}_analysis.json"
        write_analysis(result, output_path)
        written += 1
        logger.info("Wrote analysis for %s -> %s", csv_path.name, output_path)

    if written == 0:
        logger.warning("No analysis files were written.")
        return 1

    logger.info("Generated %d analysis file(s) in %s", written, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
