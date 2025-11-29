from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_kline.core import l3_evaluator  # noqa: E402


def _write_prediction(base_dir: Path, pred_date: date) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "schema_version": "2.3",
            "generated_at": f"{pred_date} 09:00:00 JST",
        },
        "market_environment": {"USDJPY": {"bias": "BULLISH", "vol_expect": "MEDIUM"}},
        "ranking": {"top_3": ["USDJPY"], "bottom_3": ["USDJPY"]},
        "strategies": [
            {
                "pair": "USDJPY",
                "rank": 1,
                "strategy_type": "DIP_BUY",
                "direction": "LONG",
                "valid_sessions": ["TOKYO"],
                "entry": {"zone_min": 149.0, "zone_max": 150.0, "strict_limit": 149.5},
                "exit": {"take_profit": 151.0, "stop_loss": 148.0, "invalidation": 147.5},
                "confidence_score": 0.7,
            }
        ],
    }
    out_path = base_dir / "L3_prediction.json"
    out_path.write_text(json.dumps(payload), encoding="utf-8")
    return out_path


def _write_summary(base_dir: Path, market_date: date) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "pair": "USDJPY",
        "timeframes": {
            "1d": {
                "open": 150.0,
                "high": 151.2,
                "low": 148.9,
                "close": 150.8,
                "atr": 0.9,
                "data_timestamp": f"{market_date}T23:59:00+09:00",
            }
        },
    }
    out_path = base_dir / "ohlc_summary.json"
    out_path.write_text(json.dumps(payload), encoding="utf-8")
    return out_path


def test_cli_main_writes_evaluation_json(tmp_path):
    pred_date = date(2025, 11, 29) - timedelta(days=1)
    prediction_path = _write_prediction(tmp_path / "prediction", pred_date)
    actual_path = _write_summary(tmp_path / "actual", pred_date + timedelta(days=1))
    output_path = tmp_path / "output" / "L3_evaluation.json"

    exit_code = l3_evaluator.main(
        [
            "--mode",
            "ai",
            "--prediction",
            str(prediction_path),
            "--actual",
            str(actual_path),
            "--output",
            str(output_path),
        ]
    )
    assert exit_code == 0
    assert output_path.exists()

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["aggregated_metrics"]["total_strategies"] == 1
    assert result["strategy_evaluations"][0]["metrics"]["direction_correct"] is True


def test_l3_evaluator_runs_with_market_data():
    pred_date = date(2025, 11, 28)
    l3_json = {
        "meta": {"schema_version": "2.3", "generated_at": f"{pred_date} 09:00:00 JST"},
        "market_environment": {},
        "ranking": {},
        "strategies": [
            {
                "pair": "USDJPY",
                "rank": 1,
                "strategy_type": "DIP_BUY",
                "direction": "LONG",
                "valid_sessions": ["TOKYO"],
                "entry": {"zone_min": 149.0, "zone_max": 150.0, "strict_limit": 149.5},
                "exit": {"take_profit": 151.0, "stop_loss": 148.0},
                "confidence_score": 0.6,
            }
        ],
    }
    idx = pd.date_range(f"{pred_date} 09:00", periods=3, freq="15min", tz="Asia/Tokyo")
    df = pd.DataFrame(
        {
            "open": [149.5, 149.8, 150.6],
            "high": [149.9, 150.7, 151.1],
            "low": [149.2, 149.6, 150.1],
            "close": [149.8, 150.6, 151.0],
            "volume": [1000, 900, 800],
        },
        index=idx,
    )

    evaluator = l3_evaluator.L3Evaluator(l3_json, {"USDJPY": df}, {"USDJPY": 0.9})
    results = evaluator.run()

    assert results["aggregated_metrics"]["total_strategies"] == 1
    assert results["strategy_evaluations"][0]["actual"]["close_price"] == 151.0
    assert results["strategy_evaluations"][0]["metrics"]["entry_hit"] is True


def test_evaluate_direction_accuracy_handles_wait_and_moves():
    up_actual = l3_evaluator.ActualOutcome(
        pair="USDJPY",
        open_price=150.0,
        high_price=151.0,
        low_price=149.5,
        close_price=150.8,
        period_return=(150.8 - 150.0) / 150.0,
        volatility=0.9,
    )
    down_actual = l3_evaluator.ActualOutcome(
        pair="USDJPY",
        open_price=150.0,
        high_price=150.2,
        low_price=149.0,
        close_price=149.2,
        period_return=(149.2 - 150.0) / 150.0,
        volatility=0.9,
    )
    flat_actual = l3_evaluator.ActualOutcome(
        pair="USDJPY",
        open_price=150.0,
        high_price=150.1,
        low_price=149.9,
        close_price=150.1,
        period_return=(150.1 - 150.0) / 150.0,
        volatility=0.9,
    )

    long_pred = l3_evaluator.StrategyPrediction(
        pair="USDJPY", rank=1, strategy_type="DIP_BUY", direction="LONG"
    )
    short_pred = l3_evaluator.StrategyPrediction(
        pair="USDJPY", rank=1, strategy_type="RALLY_SELL", direction="SHORT"
    )
    wait_pred = l3_evaluator.StrategyPrediction(
        pair="USDJPY", rank=1, strategy_type="BREAKOUT", direction="WAIT"
    )

    assert l3_evaluator.evaluate_direction_accuracy(long_pred, up_actual) is True
    assert l3_evaluator.evaluate_direction_accuracy(short_pred, down_actual) is True
    assert l3_evaluator.evaluate_direction_accuracy(wait_pred, flat_actual) is True
    assert l3_evaluator.evaluate_direction_accuracy(long_pred, down_actual) is False
