# TODO: Phase 1–2（プラン評価ライン）

## Phase 1（L3/L4 定量評価・ローカル完結）
- `tests/fixtures/` に L3/L4 prediction + 15m OHLC + summaries の固定サンプルを用意（抽出スクリプトも検討）
- `scripts/run_evaluation_review.py` を作成し、`fx_kline.core.l3_evaluator` CLI で L3/L4 を評価 → 簡易サマリー（方向正解率/RR/total_pips/rank別精度）を出力
- 複数日を一括評価するループ/集計を実装し、OK/NG しきい値をサマリーに表示
- しきい値の暫定合意を決める（例: rank1 方向正解率や RR 下限）→ サマリーに反映
- 新規スクリプトと fixtures をカバーする pytest を追加し、`uv run pytest` を通す
- Docs に “評価の回し方” と “OK/NG の見方” を追記

## Phase 2（LLM 定性レビュー原型）
- プロンプトドラフト（例: `docs/L5_eval_prompt.md`）を作成：入力 = L3/L4 prediction + L3/L4 evaluation、出力 = 3–5 行サマリー + keep/stop/try + 注目ペア/時間帯
- `scripts/generate_qualitative_review.py` を作成し、ローカル CLI で LLM（またはモック）を呼び出し `data/YYYY/MM/DD/L5_plan_review.md` を生成
- 複数パラメータ（温度/フォーマット）を試して比較ログを残す
- “mako 目線で実用か” のチェックリストを用意し、レビュー結果にフィードバックを反映
- LLM 呼び出しを環境変数/API キーに依存させつつ、オフライン時はモック/スキップで動くようにする
