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


def compute_support_resistance(df: pd.DataFrame, levels: int = 2) -> Tuple[List[float], List[float]]:
    """Pick the N lowest lows and highest highs as support/resistance."""
    lows = df["low"].dropna()
    highs = df["high"].dropna()

    support_levels = sorted(lows.nsmallest(levels).round(4).tolist())
    resistance_levels = sorted(highs.nlargest(levels).round(4).tolist(), reverse=True)

    return support_levels, resistance_levels


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
    support_levels, resistance_levels = compute_support_resistance(df)
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
