"""
L3 evaluation utilities.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Any, Dict


class L3Evaluator:
    """
    L3_prediction.json と当日のOHLC / ATRを使って
    L3の予測精度を定量評価するクラス。
    """

    def __init__(
        self,
        l3_json: Dict[str, Any],
        market_data: Dict[str, pd.DataFrame],
        atr_data: Dict[str, float],
    ):
        """
        Args:
            l3_json: L3_prediction.json の中身
            market_data: 通貨ペアごとのOHLC (JST DatetimeIndex 前提)
            atr_data: 前日時点のATR(14) (Key: 'USDJPY' 等, Value: float)
        """
        self.l3 = l3_json
        self.market_data = market_data
        self.atr_data = atr_data

        # meta.generated_at は "2025-11-27 09:00:00 JST" を想定
        self.generated_at = pd.to_datetime(l3_json["meta"]["generated_at"])
        self.target_date = self.generated_at.date()

        # 評価結果の器
        self.results: Dict[str, Any] = {
            "meta": {
                "evaluation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_date": str(self.target_date),
                "source_generated_at": l3_json["meta"]["generated_at"],
                "version": "l3_evaluation_v1.0",
            },
            "environment": {
                "per_pair": {},
                "metrics": {
                    "bias_accuracy_rate": None,
                    "vol_accuracy_rate": None,
                },
            },
            "ranking": {
                "top_3": l3_json.get("ranking", {}).get("top_3", []),
                "bottom_3": l3_json.get("ranking", {}).get("bottom_3", []),
                "per_pair": {},
                "metrics": {
                    "avg_top3_range_ratio": None,
                    "avg_bottom3_range_ratio": None,
                    "top_vs_bottom_range_ratio": None,
                },
            },
            "strategies": {
                "per_pair": {},
                "metrics": {
                    "num_strategies": 0,
                    "entry_fill_rate": None,
                    "win_rate_tp": None,
                    "total_theoretical_pnl_pips": 0.0,
                },
            },
            "summary_scores": {},
        }

    # ==========
    # ヘルパー
    # ==========

    def _get_daily_stats(self, pair: str):
        """指定ペアの当日日足統計を取得"""
        if pair not in self.market_data:
            return None

        df = self.market_data[pair]
        daily_df = df[df.index.date == self.target_date]

        if daily_df.empty:
            return None

        o = daily_df.iloc[0]["open"]
        c = daily_df.iloc[-1]["close"]
        h = daily_df["high"].max()
        l = daily_df["low"].min()

        return {
            "open": o,
            "close": c,
            "high": h,
            "low": l,
            "range": h - l,
            "body_high": max(o, c),
            "body_low": min(o, c),
        }

    def _get_prev_day_stats(self, pair: str):
        """前日の日足統計を取得（トレンド判定用）"""
        if pair not in self.market_data:
            return None

        df = self.market_data[pair]
        prev_df = df[df.index.date < self.target_date]
        if prev_df.empty:
            return None

        last_date = prev_df.index[-1].date()
        target_prev = prev_df[prev_df.index.date == last_date]

        if target_prev.empty:
            return None

        return {
            "high": target_prev["high"].max(),
            "low": target_prev["low"].min(),
        }

    # =====================
    # ① 環境認識の評価
    # =====================

    def evaluate_environment(self):
        env_preds = self.l3.get("market_environment", {})
        if "data" in env_preds:
            env_preds = env_preds["data"]

        per_pair = {}
        bias_correct = 0
        bias_total = 0
        vol_correct = 0
        vol_total = 0

        for pair, pred in env_preds.items():
            stats = self._get_daily_stats(pair)
            prev_stats = self._get_prev_day_stats(pair)
            atr = self.atr_data.get(pair, 1.0)

            if not stats or not prev_stats:
                per_pair[pair] = {"status": "NO_DATA"}
                continue

            # Volatility 判定
            vol_ratio = stats["range"] / atr
            if vol_ratio <= 0.5:
                actual_vol = "LOW"
            elif vol_ratio >= 1.5:
                actual_vol = "HIGH"
            else:
                actual_vol = "MEDIUM"

            # Bias 判定（元ロジック維持）
            is_bull = (
                (stats["close"] > stats["open"])
                and (stats["close"] > prev_stats["high"])
                and (actual_vol != "LOW")
            )
            is_bear = (
                (stats["close"] < stats["open"])
                and (stats["close"] < prev_stats["low"])
                and (actual_vol != "LOW")
            )
            is_range = (stats["body_high"] <= prev_stats["high"]) and (
                stats["body_low"] >= prev_stats["low"]
            )

            if is_bull:
                actual_bias = "BULLISH"
            elif is_bear:
                actual_bias = "BEARISH"
            elif is_range:
                actual_bias = "RANGE"
            else:
                actual_bias = "MIXED"

            pred_bias = pred.get("bias")
            pred_vol = pred.get("vol_expect")

            bias_match = pred_bias == actual_bias
            vol_match = pred_vol == actual_vol

            per_pair[pair] = {
                "predicted": {"bias": pred_bias, "vol": pred_vol},
                "actual": {"bias": actual_bias, "vol": actual_vol},
                "bias_match": bias_match,
                "vol_match": vol_match,
                "vol_ratio": float(vol_ratio),
            }

            bias_total += 1
            vol_total += 1
            if bias_match:
                bias_correct += 1
            if vol_match:
                vol_correct += 1

        bias_acc = bias_correct / bias_total if bias_total > 0 else None
        vol_acc = vol_correct / vol_total if vol_total > 0 else None

        self.results["environment"]["per_pair"] = per_pair
        self.results["environment"]["metrics"] = {
            "bias_accuracy_rate": bias_acc,
            "vol_accuracy_rate": vol_acc,
            "bias_correct": bias_correct,
            "bias_total": bias_total,
        }

    # =====================
    # ② ランキング評価
    # =====================

    def evaluate_ranking(self):
        ranking_data = self.l3.get("ranking", {})
        top3 = ranking_data.get("top_3", [])
        bottom3 = ranking_data.get("bottom_3", [])

        if not top3 or not bottom3:
            return

        def get_avg_range_ratio(pairs):
            vals = []
            for p in pairs:
                s = self._get_daily_stats(p)
                if s and s["open"] != 0:
                    vals.append(s["range"] / s["open"])
            return float(np.mean(vals)) if vals else None

        avg_top = get_avg_range_ratio(top3)
        avg_bottom = get_avg_range_ratio(bottom3)
        ratio = None
        if avg_top is not None and avg_bottom not in (None, 0):
            ratio = avg_top / avg_bottom

        self.results["ranking"]["metrics"] = {
            "avg_top3_range_ratio": avg_top,
            "avg_bottom3_range_ratio": avg_bottom,
            "top_vs_bottom_range_ratio": ratio,
        }

    # =====================
    # ③ 戦略シミュレーション
    # =====================

    def simulate_trades(self):
        strategies = self.l3.get("strategies", [])
        per_pair = {}
        num_strats = len(strategies)
        total_pips = 0.0
        filled_count = 0
        win_tp_count = 0

        for strat in strategies:
            pair = strat["pair"]
            if pair not in self.market_data:
                continue

            df = self.market_data[pair]
            day_df = df[df.index.date == self.target_date].copy()
            if day_df.empty:
                per_pair.setdefault(pair, []).append(
                    {"result": "NO_MARKET_DATA", "pnl_pips": 0.0}
                )
                continue

            valid_sessions = strat.get("valid_sessions", [])

            # Tokyo: 9-15, London: 16-21 (JST)
            session_mask = []
            for t in day_df.index:
                h = t.hour
                is_tokyo = (9 <= h < 15) and ("TOKYO" in valid_sessions)
                is_london = (16 <= h < 21) and ("LONDON" in valid_sessions)
                session_mask.append(is_tokyo or is_london)

            session_df = day_df[session_mask]

            entry_conf = strat["entry"]
            exit_conf = strat["exit"]

            entry_triggered = False
            entry_price = entry_conf["strict_limit"]
            entry_time = None

            # エントリー判定
            for t, row in session_df.iterrows():
                if (
                    row["low"] <= entry_conf["zone_max"]
                    and row["high"] >= entry_conf["zone_min"]
                ):
                    entry_triggered = True
                    entry_time = t
                    break

            outcome = "NO_ENTRY"
            pnl = 0.0

            if entry_triggered:
                filled_count += 1
                post_entry = day_df[day_df.index > entry_time]
                outcome = "HOLD"

                for t, row in post_entry.iterrows():
                    # ロング前提（現行ロジック）：SL -> LOSS, TP -> WIN
                    if row["low"] <= exit_conf["stop_loss"]:
                        outcome = "LOSS"
                        pnl = exit_conf["stop_loss"] - entry_price
                        break

                    if row["high"] >= exit_conf["take_profit"]:
                        outcome = "WIN"
                        pnl = exit_conf["take_profit"] - entry_price
                        win_tp_count += 1
                        break

                if outcome == "HOLD" and not post_entry.empty:
                    pnl = post_entry.iloc[-1]["close"] - entry_price

            multiplier = 100 if "JPY" in pair else 10000
            pnl_pips = float(pnl * multiplier)
            total_pips += pnl_pips

            per_pair.setdefault(pair, []).append(
                {
                    "strategy_type": strat.get("strategy_type"),
                    "entry_time": entry_time.isoformat() if entry_time else None,
                    "entry_price": entry_price if entry_triggered else None,
                    "result": outcome,
                    "pnl_pips": round(pnl_pips, 1),
                }
            )

        entry_fill_rate = filled_count / num_strats if num_strats > 0 else None
        win_rate_tp = win_tp_count / filled_count if filled_count > 0 else None

        self.results["strategies"]["per_pair"] = per_pair
        self.results["strategies"]["metrics"] = {
            "num_strategies": num_strats,
            "entry_fill_rate": entry_fill_rate,
            "win_rate_tp": win_rate_tp,
            "total_theoretical_pnl_pips": round(total_pips, 1),
        }

    # =====================
    # ④ 全体実行
    # =====================

    def run(self) -> Dict[str, Any]:
        self.evaluate_environment()
        self.evaluate_ranking()
        self.simulate_trades()

        # summary_scores を埋める（今は単純に転記）
        env = self.results["environment"]["metrics"]
        rank = self.results["ranking"]["metrics"]
        strat = self.results["strategies"]["metrics"]

        self.results["summary_scores"] = {
            "environment_bias_accuracy": env.get("bias_accuracy_rate"),
            "ranking_top_vs_bottom_range_ratio": rank.get(
                "top_vs_bottom_range_ratio"
            ),
            "strategy_entry_fill_rate": strat.get("entry_fill_rate"),
            "strategy_win_rate_tp": strat.get("win_rate_tp"),
            "strategy_total_pnl_pips": strat.get("total_theoretical_pnl_pips"),
        }

        return self.results


__all__ = ["L3Evaluator"]
