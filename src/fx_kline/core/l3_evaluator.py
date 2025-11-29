"""
L3/L4 Prediction Evaluator for HITL Trading System (Schema v2.3)

This module evaluates trading predictions from both L3 (AI-only) and L4 (HITL)
against actual market outcomes, providing comprehensive performance metrics
and comparative analysis.

Supports schema_version 2.3 with:
- Multiple strategies per prediction (Top 3 pairs)
- confidence_score and confidence_breakdown
- risk_reward_ratio
- reasoning and alternative_scenario

Usage:
    # Evaluate L3 (AI-only) prediction
    python -m fx_kline.core.l3_evaluator --mode ai \
        --prediction data/2025-11-27/L3_prediction.json \
        --actual data/2025-11-28/ohlc_summary.json \
        --output data/2025-11-27/L3_evaluation.json

    # Evaluate L4 (HITL) trade plan
    python -m fx_kline.core.l3_evaluator --mode hitl \
        --prediction data/2025-11-27/L4_tradeplan.json \
        --actual data/2025-11-28/ohlc_summary.json \
        --output data/2025-11-27/L4_evaluation.json
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .timezone_utils import get_jst_now

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes for Schema v2.3
# =============================================================================


@dataclass
class ConfidenceBreakdown:
    """Confidence breakdown from v2.3 schema"""
    technical_alignment: float = 0.0
    trend_strength: float = 0.0
    support_resistance_proximity: float = 0.0
    fundamental_alignment: float = 0.0


@dataclass
class AlternativeScenario:
    """Alternative scenario from v2.3 schema"""
    direction: str = "WAIT"
    probability: float = 0.0
    reason: str = ""


@dataclass
class StrategyEntry:
    """Entry zone from v2.3 schema"""
    zone_min: Optional[float] = None
    zone_max: Optional[float] = None
    strict_limit: Optional[float] = None


@dataclass
class StrategyExit:
    """Exit targets from v2.3 schema"""
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    invalidation: Optional[float] = None


@dataclass
class StrategyPrediction:
    """Single strategy from v2.3 schema strategies[] array"""
    pair: str
    rank: int
    strategy_type: str  # DIP_BUY | RALLY_SELL | BREAKOUT
    direction: str  # LONG | SHORT | WAIT
    valid_sessions: List[str] = field(default_factory=list)
    entry: StrategyEntry = field(default_factory=StrategyEntry)
    exit: StrategyExit = field(default_factory=StrategyExit)
    confidence_score: float = 0.0
    confidence_breakdown: ConfidenceBreakdown = field(default_factory=ConfidenceBreakdown)
    risk_reward_ratio: Optional[float] = None
    reasoning: str = ""
    alternative_scenario: AlternativeScenario = field(default_factory=AlternativeScenario)

    # L4-specific fields (HITL modifications)
    position_size: Optional[float] = None
    risk_percent: Optional[float] = None
    modifications: Optional[List[dict]] = None


@dataclass
class L3Prediction:
    """Full L3 prediction from v2.3 schema"""
    meta: Dict[str, Any]
    market_environment: Dict[str, Dict[str, str]]
    ranking: Dict[str, Any]
    strategies: List[StrategyPrediction]


@dataclass
class ActualOutcome:
    """Actual market movement for a single pair"""
    pair: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    period_return: float  # Percentage change
    volatility: float  # ATR or similar measure


@dataclass
class TradeMetrics:
    """Individual trade evaluation metrics"""
    direction_correct: bool
    entry_timing_score: Optional[float] = None  # -1 to 1
    exit_timing_score: Optional[float] = None
    pips_outcome: Optional[float] = None
    risk_reward_realized: Optional[float] = None
    confidence_calibration: Optional[float] = None  # abs(confidence - accuracy)
    entry_hit: bool = False  # Whether entry zone was reached
    stop_loss_hit: bool = False
    take_profit_hit: bool = False


@dataclass
class StrategyEvaluationResult:
    """Evaluation result for a single strategy"""
    pair: str
    rank: int
    direction: str
    strategy_type: str
    metrics: TradeMetrics
    prediction: StrategyPrediction
    actual: ActualOutcome
    market_regime: Optional[str] = None
    event_proximity: bool = False
    intervention_type: Optional[str] = None
    intervention_success: Optional[bool] = None

    def to_dict(self) -> dict:
        result = asdict(self)
        return result


@dataclass
class L3EvaluationResult:
    """Comprehensive evaluation result for all strategies"""
    date: str
    mode: str  # "ai" or "hitl"
    schema_version: str
    strategy_evaluations: List[StrategyEvaluationResult]
    aggregated_metrics: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: get_jst_now().isoformat())

    def to_dict(self) -> dict:
        result = {
            "date": self.date,
            "mode": self.mode,
            "schema_version": self.schema_version,
            "strategy_evaluations": [e.to_dict() for e in self.strategy_evaluations],
            "aggregated_metrics": self.aggregated_metrics,
            "generated_at": self.generated_at,
        }
        return result


# =============================================================================
# Loading Functions
# =============================================================================


def parse_strategy(data: dict) -> StrategyPrediction:
    """Parse a single strategy from JSON"""
    entry_data = data.get("entry", {})
    exit_data = data.get("exit", {})
    conf_data = data.get("confidence_breakdown", {})
    alt_data = data.get("alternative_scenario", {})

    return StrategyPrediction(
        pair=data.get("pair", "UNKNOWN"),
        rank=data.get("rank", 0),
        strategy_type=data.get("strategy_type", "UNKNOWN"),
        direction=data.get("direction", "WAIT").upper(),
        valid_sessions=data.get("valid_sessions", []),
        entry=StrategyEntry(
            zone_min=entry_data.get("zone_min"),
            zone_max=entry_data.get("zone_max"),
            strict_limit=entry_data.get("strict_limit"),
        ),
        exit=StrategyExit(
            take_profit=exit_data.get("take_profit"),
            stop_loss=exit_data.get("stop_loss"),
            invalidation=exit_data.get("invalidation"),
        ),
        confidence_score=data.get("confidence_score", 0.0) or 0.0,
        confidence_breakdown=ConfidenceBreakdown(
            technical_alignment=conf_data.get("technical_alignment", 0.0) or 0.0,
            trend_strength=conf_data.get("trend_strength", 0.0) or 0.0,
            support_resistance_proximity=conf_data.get("support_resistance_proximity", 0.0) or 0.0,
            fundamental_alignment=conf_data.get("fundamental_alignment", 0.0) or 0.0,
        ),
        risk_reward_ratio=data.get("risk_reward_ratio"),
        reasoning=data.get("reasoning", ""),
        alternative_scenario=AlternativeScenario(
            direction=alt_data.get("direction", "WAIT"),
            probability=alt_data.get("probability", 0.0) or 0.0,
            reason=alt_data.get("reason", ""),
        ),
        modifications=data.get("modifications"),
    )


def load_l3_prediction(file_path: Path) -> L3Prediction:
    """Load L3 prediction from v2.3 schema JSON

    Args:
        file_path: Path to L3_prediction.json

    Returns:
        L3Prediction object
    """
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    market_env = data.get("market_environment", {})
    ranking = data.get("ranking", {})
    strategies_data = data.get("strategies", [])

    strategies = [parse_strategy(s) for s in strategies_data]

    return L3Prediction(
        meta=meta,
        market_environment=market_env,
        ranking=ranking,
        strategies=strategies,
    )


def get_session_time_range(session: str) -> Tuple[int, int]:
    """Get session time range in JST hours

    Args:
        session: Session name ("TOKYO", "LONDON", "NY")

    Returns:
        Tuple of (start_hour, end_hour) in JST
    """
    session_ranges = {
        "TOKYO": (9, 15),      # 09:00-15:00 JST
        "LONDON": (16, 21),    # 16:00-21:00 JST
        "NY": (22, 6),         # 22:00-06:00 JST (crosses midnight)
    }
    normalized = session.upper()
    if normalized not in session_ranges:
        logger.warning(f"Unknown session '{session}', defaulting to full day (0-24)")
    return session_ranges.get(normalized, (0, 24))


def filter_df_by_sessions(
    df: pd.DataFrame,
    sessions: List[str],
) -> pd.DataFrame:
    """Filter DataFrame to include only specified trading sessions

    Args:
        df: DataFrame with datetime index (JST timezone)
        sessions: List of session names ["TOKYO", "LONDON", etc.]

    Returns:
        Filtered DataFrame
    """
    if not sessions or df.empty:
        return df

    mask = pd.Series(False, index=df.index)

    for session in sessions:
        start_hour, end_hour = get_session_time_range(session)

        if start_hour < end_hour:
            # Normal range (e.g., TOKYO 9-15)
            session_mask = (df.index.hour >= start_hour) & (df.index.hour < end_hour)
        else:
            # Crosses midnight (e.g., NY 22-6)
            session_mask = (df.index.hour >= start_hour) | (df.index.hour < end_hour)

        mask = mask | session_mask

    return df[mask]


def load_actual_outcome_from_ohlc(
    df: pd.DataFrame,
    pair: str,
    atr: Optional[float] = None,
    sessions: Optional[List[str]] = None,
) -> ActualOutcome:
    """Load actual outcome from 15-minute OHLC DataFrame

    Args:
        df: DataFrame with 15-minute OHLC data (datetime index in JST, ohlc columns)
        pair: Currency pair name
        atr: ATR value (optional)
        sessions: List of valid sessions to filter (optional, e.g., ["TOKYO", "LONDON"])

    Returns:
        ActualOutcome object aggregated from 15-minute bars
    """
    if df.empty:
        raise ValueError(f"Empty DataFrame for {pair}")

    # Filter by sessions if specified
    if sessions:
        df = filter_df_by_sessions(df, sessions)
        if df.empty:
            raise ValueError(f"No data for {pair} in sessions {sessions}")

    # Aggregate 15-minute bars to session/daily OHLC
    open_price = float(df["open"].iloc[0])
    high_price = float(df["high"].max())
    low_price = float(df["low"].min())
    close_price = float(df["close"].iloc[-1])

    period_return = ((close_price - open_price) / open_price) if open_price > 0 else 0.0

    return ActualOutcome(
        pair=pair,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        period_return=period_return,
        volatility=atr or 0.0,
    )


def load_actual_outcome_from_summary(file_path: Path, pair: str) -> ActualOutcome:
    """Load actual market outcome from OHLC summary JSON

    Args:
        file_path: Path to ohlc_summary.json, {pair}_summary.json, or directory containing summaries
        pair: Currency pair to extract

    Returns:
        ActualOutcome object

    Raises:
        ValueError: If file not found or data missing
        FileNotFoundError: If per-pair file not found in directory
    """
    # If file_path is a directory, look for {pair}_summary.json
    if file_path.is_dir():
        pair_file = file_path / f"{pair}_summary.json"
        if not pair_file.exists():
            raise FileNotFoundError(
                f"Summary file for {pair} not found in {file_path}. "
                f"Expected: {pair_file}"
            )
        file_path = pair_file

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Verify pair matches if present in JSON
    json_pair = data.get("pair")
    if json_pair and json_pair != pair:
        logger.warning(
            f"Pair mismatch: requested {pair}, but JSON contains {json_pair}. "
            f"Using data from {file_path}"
        )

    # Assume ohlc_summary.json has timeframe-specific data
    timeframes = data.get("timeframes", {})
    daily_data = timeframes.get("1d", {})

    if not daily_data:
        raise ValueError(f"No 1d timeframe data found for {pair} in {file_path}")

    open_price = daily_data.get("open", 0.0)
    high_price = daily_data.get("high", 0.0)
    low_price = daily_data.get("low", 0.0)
    close_price = daily_data.get("close", 0.0)
    atr = daily_data.get("atr", 0.0)

    period_return = ((close_price - open_price) / open_price) if open_price > 0 else 0.0

    return ActualOutcome(
        pair=pair,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        period_return=period_return,
        volatility=atr,
    )


# =============================================================================
# Evaluation Functions
# =============================================================================


def get_pip_value(pair: str) -> float:
    """Get pip value for a currency pair"""
    if "JPY" in pair.upper():
        return 0.01
    elif "XAU" in pair.upper():
        return 0.1
    else:
        return 0.0001


def evaluate_direction_accuracy(
    prediction: StrategyPrediction,
    actual: ActualOutcome,
) -> bool:
    """Check if predicted direction matches actual market movement"""
    if prediction.direction == "WAIT":
        # WAIT is considered correct if price movement was small (within 0.5%)
        return abs(actual.period_return) < 0.005

    if prediction.direction == "LONG":
        return actual.close_price > actual.open_price

    if prediction.direction == "SHORT":
        return actual.close_price < actual.open_price

    return False


def evaluate_entry_hit(
    prediction: StrategyPrediction,
    actual: ActualOutcome,
) -> bool:
    """Check if entry zone was reached during the trading session"""
    if prediction.direction == "WAIT":
        return False

    zone_min = prediction.entry.zone_min
    zone_max = prediction.entry.zone_max

    if zone_min is None or zone_max is None:
        return False

    # Check if price entered the zone
    if prediction.direction == "LONG":
        # For LONG, we want price to dip into zone
        return actual.low_price <= zone_max
    else:  # SHORT
        # For SHORT, we want price to rally into zone
        return actual.high_price >= zone_min

    return False


def calculate_entry_timing_score(
    prediction: StrategyPrediction,
    actual: ActualOutcome,
) -> Optional[float]:
    """Evaluate entry timing quality

    Returns:
        Score from -1 (too early) to 1 (too late), 0 is ideal
        None if not applicable
    """
    if prediction.direction == "WAIT":
        return None

    entry = prediction.entry.strict_limit or prediction.entry.zone_min
    if entry is None:
        return None

    if prediction.direction == "LONG":
        ideal_entry = actual.low_price
        worst_entry = actual.high_price
    else:  # SHORT
        ideal_entry = actual.high_price
        worst_entry = actual.low_price

    if worst_entry == ideal_entry:
        return 0.0

    score = (entry - ideal_entry) / (worst_entry - ideal_entry)
    score = max(-1.0, min(1.0, score * 2 - 1))

    return round(score, 3)


def calculate_pips_outcome(
    prediction: StrategyPrediction,
    actual: ActualOutcome,
) -> Optional[float]:
    """Calculate pips outcome if trade was executed"""
    if prediction.direction == "WAIT":
        return None

    entry = prediction.entry.strict_limit or prediction.entry.zone_min
    if entry is None:
        return None

    pip_value = get_pip_value(prediction.pair)
    stop_loss = prediction.exit.stop_loss
    take_profit = prediction.exit.take_profit

    if prediction.direction == "LONG":
        # Check if stop loss was hit
        if stop_loss and actual.low_price <= stop_loss:
            exit_price = stop_loss
        # Check if take profit was hit
        elif take_profit and actual.high_price >= take_profit:
            exit_price = take_profit
        else:
            exit_price = actual.close_price

        pips = (exit_price - entry) / pip_value

    else:  # SHORT
        if stop_loss and actual.high_price >= stop_loss:
            exit_price = stop_loss
        elif take_profit and actual.low_price <= take_profit:
            exit_price = take_profit
        else:
            exit_price = actual.close_price

        pips = (entry - exit_price) / pip_value

    return round(pips, 1)


def evaluate_single_strategy(
    prediction: StrategyPrediction,
    actual: ActualOutcome,
    market_regime: Optional[str] = None,
    event_proximity: bool = False,
) -> StrategyEvaluationResult:
    """Evaluate a single strategy against actual outcome"""
    # Direction accuracy
    direction_correct = evaluate_direction_accuracy(prediction, actual)

    # Entry hit
    entry_hit = evaluate_entry_hit(prediction, actual)

    # Timing scores
    entry_timing = calculate_entry_timing_score(prediction, actual)

    # Pips outcome
    pips = calculate_pips_outcome(prediction, actual)

    # Stop loss / Take profit hit
    stop_loss_hit = False
    take_profit_hit = False
    if prediction.exit.stop_loss:
        if prediction.direction == "LONG":
            stop_loss_hit = actual.low_price <= prediction.exit.stop_loss
        elif prediction.direction == "SHORT":
            stop_loss_hit = actual.high_price >= prediction.exit.stop_loss

    if prediction.exit.take_profit:
        if prediction.direction == "LONG":
            take_profit_hit = actual.high_price >= prediction.exit.take_profit
        elif prediction.direction == "SHORT":
            take_profit_hit = actual.low_price <= prediction.exit.take_profit

    # Risk-reward realized
    rr_realized = None
    entry = prediction.entry.strict_limit or prediction.entry.zone_min
    if pips is not None and prediction.exit.stop_loss and entry is not None:
        pip_value = get_pip_value(prediction.pair)
        risk_pips = abs(entry - prediction.exit.stop_loss) / pip_value
        if risk_pips > 0:
            rr_realized = round(pips / risk_pips, 2)

    # Confidence calibration
    conf_calibration = None
    if prediction.confidence_score > 0:
        actual_accuracy = 1.0 if direction_correct else 0.0
        conf_calibration = round(abs(prediction.confidence_score - actual_accuracy), 3)

    metrics = TradeMetrics(
        direction_correct=direction_correct,
        entry_timing_score=entry_timing,
        pips_outcome=pips,
        risk_reward_realized=rr_realized,
        confidence_calibration=conf_calibration,
        entry_hit=entry_hit,
        stop_loss_hit=stop_loss_hit,
        take_profit_hit=take_profit_hit,
    )

    # HITL intervention analysis
    intervention_type = None
    intervention_success = None
    if prediction.modifications:
        for mod in prediction.modifications:
            mod_type = mod.get("modification_type", "")
            if "risk" in mod_type.lower():
                intervention_type = "risk_reduction"
            elif "aggressive" in mod_type.lower():
                intervention_type = "aggressive_adjustment"
            elif "cancellation" in mod_type.lower() or "wait" in mod_type.lower():
                intervention_type = "trade_cancellation"

        intervention_success = direction_correct

    return StrategyEvaluationResult(
        pair=prediction.pair,
        rank=prediction.rank,
        direction=prediction.direction,
        strategy_type=prediction.strategy_type,
        metrics=metrics,
        prediction=prediction,
        actual=actual,
        market_regime=market_regime,
        event_proximity=event_proximity,
        intervention_type=intervention_type,
        intervention_success=intervention_success,
    )


def calculate_aggregated_metrics(
    evaluations: List[StrategyEvaluationResult],
    mode: str,
) -> Dict[str, Any]:
    """Calculate aggregated metrics across all strategy evaluations"""
    if not evaluations:
        return {
            "total_strategies": 0,
            "direction_accuracy": 0.0,
            "avg_confidence": 0.0,
            "avg_confidence_calibration": 0.0,
        }

    total = len(evaluations)
    correct = sum(1 for e in evaluations if e.metrics.direction_correct)
    direction_accuracy = round(correct / total, 3) if total > 0 else 0.0

    # Average confidence
    confidences = [e.prediction.confidence_score for e in evaluations if e.prediction.confidence_score > 0]
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

    # Average confidence calibration
    calibrations = [e.metrics.confidence_calibration for e in evaluations if e.metrics.confidence_calibration is not None]
    avg_calibration = round(sum(calibrations) / len(calibrations), 3) if calibrations else 0.0

    # Entry hit rate
    entry_hits = sum(1 for e in evaluations if e.metrics.entry_hit)
    entry_hit_rate = round(entry_hits / total, 3) if total > 0 else 0.0

    # Pips summary
    pips_list = [e.metrics.pips_outcome for e in evaluations if e.metrics.pips_outcome is not None]
    total_pips = round(sum(pips_list), 1) if pips_list else 0.0
    avg_pips = round(sum(pips_list) / len(pips_list), 1) if pips_list else 0.0

    # By market regime
    accuracy_by_regime = {}
    regimes = set(e.market_regime for e in evaluations if e.market_regime)
    for regime in regimes:
        regime_evals = [e for e in evaluations if e.market_regime == regime]
        regime_correct = sum(1 for e in regime_evals if e.metrics.direction_correct)
        accuracy_by_regime[regime] = round(regime_correct / len(regime_evals), 3)

    # By rank
    accuracy_by_rank = {}
    ranks = set(e.rank for e in evaluations)
    for rank in ranks:
        rank_evals = [e for e in evaluations if e.rank == rank]
        rank_correct = sum(1 for e in rank_evals if e.metrics.direction_correct)
        accuracy_by_rank[str(rank)] = round(rank_correct / len(rank_evals), 3)

    result = {
        "total_strategies": total,
        "direction_accuracy": direction_accuracy,
        "avg_confidence": avg_confidence,
        "avg_confidence_calibration": avg_calibration,
        "entry_hit_rate": entry_hit_rate,
        "total_pips": total_pips,
        "avg_pips": avg_pips,
        "accuracy_by_regime": accuracy_by_regime,
        "accuracy_by_rank": accuracy_by_rank,
    }

    # HITL-specific metrics
    if mode == "hitl":
        interventions = [e for e in evaluations if e.intervention_type is not None]
        total_interventions = len(interventions)
        result["total_interventions"] = total_interventions

        if total_interventions > 0:
            successes = sum(1 for e in interventions if e.intervention_success)
            result["intervention_success_rate"] = round(successes / total_interventions, 3)

            intervention_impact = {}
            types = set(e.intervention_type for e in interventions if e.intervention_type)
            for itype in types:
                type_evals = [e for e in interventions if e.intervention_type == itype]
                type_successes = sum(1 for e in type_evals if e.intervention_success)
                intervention_impact[itype] = {
                    "count": len(type_evals),
                    "success_rate": round(type_successes / len(type_evals), 3),
                }
            result["intervention_impact"] = intervention_impact

    return result


# =============================================================================
# L3Evaluator Class (programmatic interface)
# =============================================================================


class L3Evaluator:
    """Evaluator class for L3 predictions (v2.3 schema)

    This class provides a convenient interface for evaluating L3 predictions
    against actual market data.
    """

    def __init__(
        self,
        l3_json: Dict[str, Any],
        market_data: Dict[str, pd.DataFrame],
        atr_data: Optional[Dict[str, float]] = None,
        mode: str = "ai",
    ):
        """Initialize evaluator

        Args:
            l3_json: Parsed L3_prediction.json data
            market_data: Dict of pair -> DataFrame with OHLC data
            atr_data: Dict of pair -> ATR value
            mode: "ai" or "hitl"
        """
        self.l3_json = l3_json
        self.market_data = market_data
        self.atr_data = atr_data or {}
        self.mode = mode

    def run(self) -> Dict[str, Any]:
        """Run evaluation and return results

        Uses 15-minute OHLC data filtered by valid_sessions for each strategy.
        """
        meta = self.l3_json.get("meta", {})
        schema_version = meta.get("schema_version", "2.3")
        strategies_data = self.l3_json.get("strategies", [])

        evaluations: List[StrategyEvaluationResult] = []

        for strat_data in strategies_data:
            strategy = parse_strategy(strat_data)
            pair = strategy.pair

            if pair not in self.market_data:
                logger.warning(f"No market data for {pair}, skipping evaluation")
                continue

            df = self.market_data[pair]
            atr = self.atr_data.get(pair)

            # Use valid_sessions from strategy to filter 15-minute data
            sessions = strategy.valid_sessions if strategy.valid_sessions else None

            try:
                actual = load_actual_outcome_from_ohlc(df, pair, atr, sessions=sessions)
                eval_result = evaluate_single_strategy(strategy, actual)
                evaluations.append(eval_result)
                logger.debug(
                    f"Evaluated {pair} (sessions={sessions}): "
                    f"open={actual.open_price}, high={actual.high_price}, "
                    f"low={actual.low_price}, close={actual.close_price}"
                )
            except Exception as exc:
                logger.error(f"Failed to evaluate {pair}: {exc}")
                continue

        aggregated = calculate_aggregated_metrics(evaluations, self.mode)

        result = L3EvaluationResult(
            date=get_jst_now().strftime("%Y-%m-%d"),
            mode=self.mode,
            schema_version=schema_version,
            strategy_evaluations=evaluations,
            aggregated_metrics=aggregated,
        )

        return result.to_dict()


# =============================================================================
# CLI Entry Point
# =============================================================================


def write_evaluation(result: Dict[str, Any], output_path: Path) -> None:
    """Write evaluation result to JSON"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Wrote evaluation to {output_path}")


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point

    Returns:
        0 on success, 1 on failure
    """
    parser = argparse.ArgumentParser(
        description="Evaluate L3/L4 predictions against actual market outcomes (v2.3 schema)"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["ai", "hitl"],
        help="Evaluation mode: 'ai' for L3, 'hitl' for L4",
    )
    parser.add_argument(
        "--prediction",
        type=Path,
        required=True,
        help="Path to prediction file (L3_prediction.json or L4_tradeplan.json)",
    )
    parser.add_argument(
        "--actual",
        type=Path,
        required=True,
        help="Path to actual outcome file (e.g., next day's ohlc_summary.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to output evaluation file",
    )
    parser.add_argument(
        "--market-regime",
        choices=["TRENDING", "RANGING", "CHOPPY"],
        help="Market regime during the trade (optional)",
    )
    parser.add_argument(
        "--event-proximity",
        action="store_true",
        help="Flag if high-impact event was within 24 hours",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    try:
        # Load L3 prediction (v2.3 schema)
        l3_pred = load_l3_prediction(args.prediction)
        logger.info(f"Loaded {len(l3_pred.strategies)} strategies from {args.prediction}")

        # Evaluate each strategy
        evaluations: List[StrategyEvaluationResult] = []

        for strategy in l3_pred.strategies:
            try:
                actual = load_actual_outcome_from_summary(args.actual, strategy.pair)
                eval_result = evaluate_single_strategy(
                    strategy,
                    actual,
                    market_regime=args.market_regime,
                    event_proximity=args.event_proximity,
                )
                evaluations.append(eval_result)
                logger.info(f"Evaluated {strategy.pair}: {strategy.direction} -> {'✅' if eval_result.metrics.direction_correct else '❌'}")
            except Exception as exc:
                logger.error(f"Failed to evaluate {strategy.pair}: {exc}")
                continue

        # Calculate aggregated metrics
        aggregated = calculate_aggregated_metrics(evaluations, args.mode)

        # Build result
        result = L3EvaluationResult(
            date=get_jst_now().strftime("%Y-%m-%d"),
            mode=args.mode,
            schema_version=l3_pred.meta.get("schema_version", "2.3"),
            strategy_evaluations=evaluations,
            aggregated_metrics=aggregated,
        )

        # Write output
        write_evaluation(result.to_dict(), args.output)

        # Print summary
        print(f"\n{'='*60}")
        print(f"L3 Evaluation Result ({args.mode.upper()}) - Schema v{l3_pred.meta.get('schema_version', '2.3')}")
        print(f"{'='*60}")
        print(f"Total Strategies: {aggregated['total_strategies']}")
        print(f"Direction Accuracy: {aggregated['direction_accuracy']:.1%}")
        print(f"Avg Confidence: {aggregated['avg_confidence']:.2f}")
        print(f"Avg Calibration Error: {aggregated['avg_confidence_calibration']:.3f}")
        print(f"Entry Hit Rate: {aggregated['entry_hit_rate']:.1%}")
        print(f"Total Pips: {aggregated['total_pips']:+.1f}")

        print(f"\n--- Per Strategy ---")
        for eval_result in evaluations:
            status = "✅" if eval_result.metrics.direction_correct else "❌"
            pips = eval_result.metrics.pips_outcome
            pips_str = f"{pips:+.1f} pips" if pips is not None else "N/A"
            print(f"  Rank {eval_result.rank}: {eval_result.pair} {eval_result.direction} {status} ({pips_str})")

        print(f"{'='*60}\n")

        return 0

    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
