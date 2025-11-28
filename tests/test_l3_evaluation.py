from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
SCRIPTS_PATH = PROJECT_ROOT / "scripts"

for p in (SRC_PATH, SCRIPTS_PATH):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fx_kline.analyst import data_manager  # noqa: E402
from fx_kline.analyst.l3_evaluator import L3Evaluator  # noqa: E402
import run_l3_evaluation  # noqa: E402


def _write_prediction(tmp_path: Path, pred_date: date):
    pred_dir = data_manager.get_daily_data_dir(pred_date)
    pred_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {"version": "1.0", "generated_at": f"{pred_date} 09:00:00 JST"},
        "market_environment": {"USDJPY": {"bias": "BULLISH", "vol_expect": "MEDIUM"}},
        "ranking": {"top_3": ["USDJPY"], "bottom_3": ["USDJPY"]},
        "strategies": [
            {
                "pair": "USDJPY",
                "rank": 1,
                "strategy_type": "DIP_BUY",
                "valid_sessions": ["TOKYO"],
                "entry": {"zone_min": 100.0, "zone_max": 101.0, "strict_limit": 100.5},
                "exit": {"take_profit": 102.0, "stop_loss": 99.5, "invalidation": 99.0},
            }
        ],
    }
    (pred_dir / "L3_prediction.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_summary(tmp_path: Path, pred_date: date):
    summaries_dir = data_manager.get_daily_summaries_dir(pred_date)
    payload = {
        "pair": "USDJPY",
        "timeframes": {"1d": {"atr": 2.0}},
    }
    summaries_dir.mkdir(parents=True, exist_ok=True)
    (summaries_dir / "USDJPY_summary.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_ohlc(tmp_path: Path, pred_date: date):
    ohlc_dir = data_manager.get_daily_ohlc_dir(pred_date)
    idx = pd.date_range(f"{pred_date} 09:00", periods=3, freq="15min", tz="Asia/Tokyo")
    df = pd.DataFrame(
        {
            "datetime": idx,
            "open": [100.0, 100.6, 101.0],
            "high": [100.8, 101.2, 101.5],
            "low": [99.8, 100.4, 100.9],
            "close": [100.7, 101.0, 101.4],
            "volume": [1000, 900, 800],
        }
    )
    ohlc_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(ohlc_dir / "USDJPY_15m.csv", index=False)


def test_run_l3_evaluation_produces_output(monkeypatch, tmp_path):
    monkeypatch.setattr(data_manager, "get_data_root", lambda: tmp_path / "data")

    target_date = date(2025, 11, 29)
    pred_date = target_date - timedelta(days=1)

    _write_prediction(tmp_path, pred_date)
    _write_summary(tmp_path, pred_date)
    _write_ohlc(tmp_path, pred_date)

    exit_code = run_l3_evaluation.main(["--target-date", target_date.strftime("%Y-%m-%d")])
    assert exit_code == 0

    out_path = data_manager.get_daily_data_dir(target_date) / "L3_evaluation.json"
    assert out_path.exists()


def test_evaluator_runs_with_minimal_inputs():
    pred_date = date(2025, 11, 28)
    l3_json = {
        "meta": {"version": "1.0", "generated_at": f"{pred_date} 09:00:00 JST"},
        "market_environment": {"USDJPY": {"bias": "BULLISH", "vol_expect": "MEDIUM"}},
        "ranking": {"top_3": ["USDJPY"], "bottom_3": ["USDJPY"]},
        "strategies": [],
    }
    idx = pd.date_range(f"{pred_date} 09:00", periods=2, freq="15min", tz="Asia/Tokyo")
    df = pd.DataFrame(
        {
            "open": [100.0, 100.5],
            "high": [100.4, 100.8],
            "low": [99.8, 100.2],
            "close": [100.3, 100.7],
            "volume": [10, 11],
        },
        index=idx,
    )
    evaluator = L3Evaluator(l3_json, {"USDJPY": df}, {"USDJPY": 1.0})
    results = evaluator.run()
    assert "environment" in results
    assert "strategies" in results
