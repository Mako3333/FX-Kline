#!/usr/bin/env python3
"""
Run L3 evaluation for a given target date.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Sequence

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_kline.analyst import data_manager  # noqa: E402
from fx_kline.analyst.l3_evaluator import L3Evaluator  # noqa: E402


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _load_prediction(pred_date: date) -> Dict:
    pred_path = data_manager.get_daily_data_dir(pred_date) / "L3_prediction.json"
    if not pred_path.exists():
        raise FileNotFoundError(f"L3_prediction.json not found at {pred_path}")
    return _load_json(pred_path)


def _load_market_data(pred_date: date) -> Dict[str, pd.DataFrame]:
    ohlc_dir = data_manager.get_daily_ohlc_dir(pred_date)
    market_data: Dict[str, pd.DataFrame] = {}
    if not ohlc_dir.exists():
        return market_data

    for csv_path in sorted(ohlc_dir.glob("*_15m.csv")):
        pair = csv_path.stem.split("_")[0]
        df = pd.read_csv(csv_path, parse_dates=["datetime"])
        if df.empty:
            continue
        df = df.rename(columns=str.lower)
        df = df.set_index("datetime")
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize("Asia/Tokyo")
        else:
            df.index = df.index.tz_convert("Asia/Tokyo")
        market_data[pair] = df
    return market_data


def _load_atr_from_summaries(pred_date: date) -> Dict[str, float]:
    summaries_dir = data_manager.get_daily_summaries_dir(pred_date)
    atr_map: Dict[str, float] = {}
    if not summaries_dir.exists():
        return atr_map

    for path in summaries_dir.glob("*_summary.json"):
        data = _load_json(path)
        pair = data.get("pair")
        tf_1d = data.get("timeframes", {}).get("1d", {})
        atr_val = tf_1d.get("atr")
        if pair and isinstance(atr_val, (int, float)):
            atr_map[pair] = float(atr_val)
    return atr_map


def run_for_target_date(target_date: date) -> Dict:
    prediction_date = target_date - timedelta(days=1)
    l3_json = _load_prediction(prediction_date)
    market_data = _load_market_data(prediction_date)
    atr_data = _load_atr_from_summaries(prediction_date)

    evaluator = L3Evaluator(l3_json=l3_json, market_data=market_data, atr_data=atr_data)
    results = evaluator.run()

    out_dir = data_manager.get_daily_data_dir(target_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "L3_evaluation.json"
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(results, fp, ensure_ascii=True, indent=2, default=str)
    return {"output_path": out_path, "results": results}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run L3 evaluation for a target date.")
    parser.add_argument(
        "--target-date",
        required=True,
        help="Target evaluation date (YYYY-MM-DD). Uses previous day data for evaluation.",
    )
    args = parser.parse_args(argv)

    target_date = _parse_date(args.target_date)

    try:
        result = run_for_target_date(target_date)
        print(f"[OK] L3 evaluation written to {result['output_path']}")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERR] L3 evaluation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
