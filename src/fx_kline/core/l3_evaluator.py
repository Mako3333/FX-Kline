"""
L3/L4 Prediction Evaluator for HITL Trading System

This module evaluates trading predictions from both L3 (AI-only) and L4 (HITL)
against actual market outcomes, providing comprehensive performance metrics
and comparative analysis.

Usage:
    # Evaluate L3 (AI-only) prediction
    python -m fx_kline.core.l3_evaluator --mode ai \\
        --prediction data/2025-11-27/L3_prediction.json \\
        --actual data/2025-11-28/ohlc_summary.json \\
        --output data/2025-11-27/L4_ai_evaluation.json

    # Evaluate L4 (HITL) trade plan
    python -m fx_kline.core.l3_evaluator --mode hitl \\
        --prediction data/2025-11-27/L4_tradeplan.json \\
        --actual data/2025-11-28/ohlc_summary.json \\
        --output data/2025-11-27/L4_hitl_evaluation.json
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .timezone_utils import get_jst_now

logger = logging.getLogger(__name__)


@dataclass
class PredictionInput:
    """Prediction/Trade plan input (L3 or L4)"""
    direction: str  # "LONG" | "SHORT" | "WAIT"
    pair: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence_score: Optional[float] = None  # 0.0-1.0
    reasoning: Optional[str] = None

    # L4-specific fields
    position_size: Optional[float] = None
    risk_percent: Optional[float] = None
    modifications: Optional[List[dict]] = None  # HITL interventions


@dataclass
class ActualOutcome:
    """Actual market movement"""
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
    entry_timing_score: Optional[float] = None  # -1 to 1 (-1=too early, 0=perfect, 1=too late)
    exit_timing_score: Optional[float] = None
    pips_outcome: Optional[float] = None  # Actual pips if executed
    risk_reward_realized: Optional[float] = None
    confidence_calibration: Optional[float] = None  # abs(confidence - accuracy)


@dataclass
class EvaluationResult:
    """Comprehensive evaluation result"""
    # Basic info
    date: str
    pair: str
    mode: str  # "ai" or "hitl"
    prediction: PredictionInput
    actual: ActualOutcome

    # Evaluation metrics
    metrics: TradeMetrics

    # Market context
    market_regime: Optional[str] = None  # "TRENDING" | "RANGING" | "CHOPPY"
    event_proximity: bool = False  # High-impact event within 24h

    # HITL-specific
    intervention_type: Optional[str] = None  # "risk_reduction" | "aggressive" | "cancellation"
    intervention_success: Optional[bool] = None

    generated_at: str = field(default_factory=lambda: get_jst_now().isoformat())

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        result = asdict(self)
        return result


@dataclass
class AggregatedMetrics:
    """Aggregated performance metrics across multiple trades"""
    total_trades: int
    direction_accuracy: float  # Win rate
    avg_confidence: float
    avg_confidence_calibration: float

    # By market regime
    accuracy_by_regime: Dict[str, float] = field(default_factory=dict)

    # HITL-specific
    total_interventions: Optional[int] = None
    intervention_success_rate: Optional[float] = None
    intervention_impact: Optional[Dict[str, dict]] = None

    # Risk-adjusted metrics
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


def load_prediction(file_path: Path, mode: str) -> PredictionInput:
    """Load prediction from L3_prediction.json or L4_tradeplan.json

    Args:
        file_path: Path to prediction file
        mode: "ai" (L3) or "hitl" (L4)

    Returns:
        PredictionInput object
    """
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if mode == "ai":
        # L3_prediction.json structure
        pred = data.get("prediction", {})
        return PredictionInput(
            direction=pred.get("direction", "WAIT").upper(),
            pair=pred.get("pair", "UNKNOWN"),
            entry_price=pred.get("entry_price"),
            stop_loss=pred.get("stop_loss"),
            take_profit=pred.get("target_price") or pred.get("take_profit"),
            confidence_score=pred.get("confidence_score"),
            reasoning=pred.get("reasoning")
        )
    else:  # mode == "hitl"
        # L4_tradeplan.json structure
        base = data.get("base_prediction", {})
        final = data.get("final_plan", {})
        mods = data.get("hitl_modifications", [])

        return PredictionInput(
            direction=final.get("direction", "WAIT").upper(),
            pair=base.get("pair", "UNKNOWN"),
            entry_price=final.get("entry_price"),
            stop_loss=final.get("stop_loss"),
            take_profit=final.get("take_profit"),
            confidence_score=final.get("confidence_score"),
            reasoning=final.get("reasoning"),
            position_size=final.get("position_size"),
            risk_percent=final.get("risk_percent"),
            modifications=mods
        )


def load_actual_outcome(file_path: Path, pair: str) -> ActualOutcome:
    """Load actual market outcome from OHLC summary

    Args:
        file_path: Path to ohlc_summary.json or similar
        pair: Currency pair to extract

    Returns:
        ActualOutcome object
    """
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Assume ohlc_summary.json has timeframe-specific data
    # Use 1d timeframe for daily evaluation
    timeframes = data.get("timeframes", {})
    daily_data = timeframes.get("1d", {})

    # Extract OHLC from the last bar
    # This is a simplified example - adjust based on actual data structure
    if not daily_data:
        raise ValueError(f"No 1d timeframe data found for {pair}")

    # Placeholder: extract from your actual ohlc_summary structure
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
        volatility=atr
    )


def evaluate_direction_accuracy(
    prediction: PredictionInput,
    actual: ActualOutcome
) -> bool:
    """Check if predicted direction matches actual market movement

    Args:
        prediction: Predicted direction
        actual: Actual market outcome

    Returns:
        True if direction was correct
    """
    if prediction.direction == "WAIT":
        # WAIT is considered correct if price movement was small
        # (within 0.5% of open)
        return abs(actual.period_return) < 0.005

    if prediction.direction == "LONG":
        return actual.close_price > actual.open_price

    if prediction.direction == "SHORT":
        return actual.close_price < actual.open_price

    return False


def calculate_entry_timing_score(
    prediction: PredictionInput,
    actual: ActualOutcome
) -> Optional[float]:
    """Evaluate entry timing quality

    Args:
        prediction: Predicted entry price
        actual: Actual price movement

    Returns:
        Score from -1 (too early) to 1 (too late), 0 is ideal
        None if not applicable (WAIT decision or no entry price)
    """
    if prediction.direction == "WAIT" or prediction.entry_price is None:
        return None

    entry = prediction.entry_price

    if prediction.direction == "LONG":
        # Best entry would be at the low
        ideal_entry = actual.low_price
        worst_entry = actual.high_price
    else:  # SHORT
        # Best entry would be at the high
        ideal_entry = actual.high_price
        worst_entry = actual.low_price

    # Normalize to -1 to 1
    if worst_entry == ideal_entry:
        return 0.0

    score = (entry - ideal_entry) / (worst_entry - ideal_entry)
    # Clamp to -1 to 1
    score = max(-1.0, min(1.0, score * 2 - 1))

    return round(score, 3)


def calculate_pips_outcome(
    prediction: PredictionInput,
    actual: ActualOutcome,
    pip_value: float = 0.01  # For JPY pairs
) -> Optional[float]:
    """Calculate pips outcome if trade was executed

    Args:
        prediction: Trade plan
        actual: Actual price movement
        pip_value: Pip value for the pair (0.01 for JPY, 0.0001 for others)

    Returns:
        Pips gained/lost, None if WAIT
    """
    if prediction.direction == "WAIT" or prediction.entry_price is None:
        return None

    entry = prediction.entry_price

    # Determine exit price (simplified: use close or stop/target)
    if prediction.direction == "LONG":
        # Check if stop loss was hit
        if prediction.stop_loss and actual.low_price <= prediction.stop_loss:
            exit_price = prediction.stop_loss
        # Check if take profit was hit
        elif prediction.take_profit and actual.high_price >= prediction.take_profit:
            exit_price = prediction.take_profit
        else:
            exit_price = actual.close_price

        pips = (exit_price - entry) / pip_value

    else:  # SHORT
        if prediction.stop_loss and actual.high_price >= prediction.stop_loss:
            exit_price = prediction.stop_loss
        elif prediction.take_profit and actual.low_price <= prediction.take_profit:
            exit_price = prediction.take_profit
        else:
            exit_price = actual.close_price

        pips = (entry - exit_price) / pip_value

    return round(pips, 1)


def evaluate_single_trade(
    prediction: PredictionInput,
    actual: ActualOutcome,
    market_regime: Optional[str] = None,
    event_proximity: bool = False
) -> EvaluationResult:
    """Evaluate a single prediction against actual outcome

    Args:
        prediction: L3 or L4 prediction
        actual: Actual market outcome
        market_regime: Market regime during trade
        event_proximity: Whether high-impact event was near

    Returns:
        EvaluationResult with comprehensive metrics
    """
    # Direction accuracy
    direction_correct = evaluate_direction_accuracy(prediction, actual)

    # Timing scores
    entry_timing = calculate_entry_timing_score(prediction, actual)

    # Pips outcome
    pips = calculate_pips_outcome(prediction, actual)

    # Risk-reward realized
    rr_realized = None
    if pips is not None and prediction.stop_loss and prediction.entry_price:
        risk_pips = abs(prediction.entry_price - prediction.stop_loss) / 0.01
        if risk_pips > 0:
            rr_realized = pips / risk_pips

    # Confidence calibration
    conf_calibration = None
    if prediction.confidence_score is not None:
        actual_accuracy = 1.0 if direction_correct else 0.0
        conf_calibration = abs(prediction.confidence_score - actual_accuracy)

    metrics = TradeMetrics(
        direction_correct=direction_correct,
        entry_timing_score=entry_timing,
        pips_outcome=pips,
        risk_reward_realized=rr_realized,
        confidence_calibration=conf_calibration
    )

    # HITL intervention analysis
    intervention_type = None
    intervention_success = None
    if prediction.modifications:
        # Classify intervention type based on modifications
        for mod in prediction.modifications:
            mod_type = mod.get("modification_type", "")
            if "risk" in mod_type.lower():
                intervention_type = "risk_reduction"
            elif "aggressive" in mod_type.lower():
                intervention_type = "aggressive_adjustment"
            elif "cancellation" in mod_type.lower() or "wait" in mod_type.lower():
                intervention_type = "trade_cancellation"

        # Determine intervention success
        # (Simplified: if direction correct after intervention, it's success)
        intervention_success = direction_correct

    mode = "hitl" if prediction.modifications else "ai"

    return EvaluationResult(
        date=datetime.now().strftime("%Y-%m-%d"),
        pair=prediction.pair,
        mode=mode,
        prediction=prediction,
        actual=actual,
        metrics=metrics,
        market_regime=market_regime,
        event_proximity=event_proximity,
        intervention_type=intervention_type,
        intervention_success=intervention_success
    )


def aggregate_evaluations(
    evaluations: List[EvaluationResult],
    mode: str
) -> AggregatedMetrics:
    """Aggregate multiple evaluation results

    Args:
        evaluations: List of EvaluationResult
        mode: "ai" or "hitl"

    Returns:
        AggregatedMetrics with summary statistics
    """
    if not evaluations:
        return AggregatedMetrics(
            total_trades=0,
            direction_accuracy=0.0,
            avg_confidence=0.0,
            avg_confidence_calibration=0.0
        )

    total = len(evaluations)
    correct = sum(1 for e in evaluations if e.metrics.direction_correct)
    direction_accuracy = correct / total if total > 0 else 0.0

    # Average confidence
    confidences = [e.prediction.confidence_score for e in evaluations
                   if e.prediction.confidence_score is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    # Average confidence calibration
    calibrations = [e.metrics.confidence_calibration for e in evaluations
                    if e.metrics.confidence_calibration is not None]
    avg_calibration = sum(calibrations) / len(calibrations) if calibrations else 0.0

    # By market regime
    accuracy_by_regime = {}
    regimes = set(e.market_regime for e in evaluations if e.market_regime)
    for regime in regimes:
        regime_evals = [e for e in evaluations if e.market_regime == regime]
        regime_correct = sum(1 for e in regime_evals if e.metrics.direction_correct)
        accuracy_by_regime[regime] = regime_correct / len(regime_evals)

    # HITL-specific metrics
    total_interventions = None
    intervention_success_rate = None
    intervention_impact = None

    if mode == "hitl":
        interventions = [e for e in evaluations if e.intervention_type is not None]
        total_interventions = len(interventions)

        if total_interventions > 0:
            successes = sum(1 for e in interventions if e.intervention_success)
            intervention_success_rate = successes / total_interventions

            # Break down by intervention type
            intervention_impact = {}
            types = set(e.intervention_type for e in interventions if e.intervention_type)
            for itype in types:
                type_evals = [e for e in interventions if e.intervention_type == itype]
                type_successes = sum(1 for e in type_evals if e.intervention_success)
                intervention_impact[itype] = {
                    "count": len(type_evals),
                    "success_rate": type_successes / len(type_evals)
                }

    return AggregatedMetrics(
        total_trades=total,
        direction_accuracy=direction_accuracy,
        avg_confidence=avg_confidence,
        avg_confidence_calibration=avg_calibration,
        accuracy_by_regime=accuracy_by_regime,
        total_interventions=total_interventions,
        intervention_success_rate=intervention_success_rate,
        intervention_impact=intervention_impact
    )


def write_evaluation(result: EvaluationResult, output_path: Path) -> None:
    """Write evaluation result to JSON

    Args:
        result: EvaluationResult to write
        output_path: Destination path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

    logger.info(f"Wrote evaluation to {output_path}")


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point

    Returns:
        0 on success, 1 on failure
    """
    parser = argparse.ArgumentParser(
        description="Evaluate L3/L4 predictions against actual market outcomes"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["ai", "hitl"],
        help="Evaluation mode: 'ai' for L3, 'hitl' for L4"
    )
    parser.add_argument(
        "--prediction",
        type=Path,
        required=True,
        help="Path to prediction file (L3_prediction.json or L4_tradeplan.json)"
    )
    parser.add_argument(
        "--actual",
        type=Path,
        required=True,
        help="Path to actual outcome file (e.g., next day's ohlc_summary.json)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to output evaluation file"
    )
    parser.add_argument(
        "--market-regime",
        choices=["TRENDING", "RANGING", "CHOPPY"],
        help="Market regime during the trade (optional)"
    )
    parser.add_argument(
        "--event-proximity",
        action="store_true",
        help="Flag if high-impact event was within 24 hours"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    try:
        # Load prediction
        prediction = load_prediction(args.prediction, args.mode)
        logger.info(f"Loaded {args.mode} prediction: {prediction.direction} @ {prediction.entry_price}")

        # Load actual outcome
        actual = load_actual_outcome(args.actual, prediction.pair)
        logger.info(f"Loaded actual outcome: {actual.open_price} → {actual.close_price}")

        # Evaluate
        result = evaluate_single_trade(
            prediction,
            actual,
            market_regime=args.market_regime,
            event_proximity=args.event_proximity
        )

        # Write output
        write_evaluation(result, args.output)

        # Print summary
        print(f"\n{'='*60}")
        print(f"Evaluation Result ({args.mode.upper()})")
        print(f"{'='*60}")
        print(f"Pair: {result.pair}")
        print(f"Direction: {prediction.direction}")
        print(f"Correct: {'✅ YES' if result.metrics.direction_correct else '❌ NO'}")
        if result.metrics.pips_outcome is not None:
            print(f"Pips: {result.metrics.pips_outcome:+.1f}")
        if result.metrics.entry_timing_score is not None:
            print(f"Entry Timing: {result.metrics.entry_timing_score:+.2f}")
        if result.intervention_type:
            print(f"Intervention: {result.intervention_type}")
            print(f"Success: {'✅' if result.intervention_success else '❌'}")
        print(f"{'='*60}\n")

        return 0

    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
