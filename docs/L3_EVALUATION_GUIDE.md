# L3/L4 評価エントリポイント（統一版）

評価 CLI は `fx_kline.core.l3_evaluator` に一本化しました。旧 `run_l3_evaluation` は使用禁止です。

## 使い方（CLI）
- L3（AI予測）の評価:
  ```bash
  python -m fx_kline.core.l3_evaluator \
    --mode ai \
    --prediction data/YYYY/MM/DD/L3_prediction.json \
    --actual data/YYYY/MM/DD/ohlc_summary.json \
    --output data/YYYY/MM/DD/L3_evaluation.json
  ```
- L4（HITL トレードプラン）の評価:
  ```bash
  python -m fx_kline.core.l3_evaluator \
    --mode hitl \
    --prediction data/YYYY/MM/DD/L4_tradeplan.json \
    --actual data/YYYY/MM/DD/ohlc_summary.json \
    --output data/YYYY/MM/DD/L4_evaluation.json
  ```

### 主な引数
- `--mode`: `ai`（L3）または `hitl`（L4）
- `--prediction`: L3/L4 の JSON（schema v2.3）
- `--actual`: `timeframes.1d` に `open/high/low/close/atr` を含む OHLC summary JSON
- `--output`: 評価結果を書き出すパス
- オプション: `--market-regime` (`TRENDING|RANGING|CHOPPY`), `--event-proximity`, `--verbose`

## 入出力の想定
- 入力（prediction）: `strategies[]` に `pair`, `rank`, `strategy_type`, `direction`, entry/exit, confidence 関連が入っていること
- 入力（actual）: `timeframes.1d` の価格と ATR が入っていること
- 出力: `L3_evaluation.json` / `L4_evaluation.json`  
  - 各ストラテジー: 方向正解、entry_hit、pips、RR などの指標  
  - 集計: 方向正解率、avg_confidence、entry_hit_rate、total_pips、accuracy_by_rank など

## テスト
- ユニットテストは `fx_kline.core.l3_evaluator` を直接叩く:  
  `uv run pytest tests/test_l3_evaluation.py`
- 新規ドキュメント・スクリプトを書くときは、必ず上記コマンド形式を参照すること。

## よくあるミス
- `run_l3_evaluation` や `python run_l3_evaluation.py` を呼ぶのは NG。必ず `python -m fx_kline.core.l3_evaluator` を使う。
- prediction 日付と actual（日次サマリー）の対応をずらさない。
- schema v2.3 前提でフィールドを揃える（特に `strategies[]` の必須項目）。
