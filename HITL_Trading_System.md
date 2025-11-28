# 📊 FX HITL Trading System Architecture（完全版）

## 全体コンセプト

* **目的:**
  人間（mako）とAIが協働する「人間承認型AIトレード (HITL Trading)」の、
  日次ワークフローとデータ構造を体系化する。
* **特徴:**

  * L1〜L3で「AIだけのベースライン」を作る
  * L4で「人間＋AIのHITLプラン」を作る
  * `l3_evaluator.py` で **AI単体 vs HITL** を共通の物差しで評価
  * L5で「定量 + 定性」の両側面から振り返る

---

## L1: ファンダメンタル分析 (Fundamental Analysis)

市場テーマとセンチメントを、人間の判断で確定するフェーズ。

* **主体:**
  mako（Claude App / Opus 4.5）

* **入力 (Input):**

  * 信頼できるニュースソース（Note記事など）
  * 市場解説PDF（X経由）
  * 必要に応じた Web 検索

* **出力 (Output):**

  * `L1_fundamental.md`
  * **内容例:**

    * 今日のメインテーマ
      （例: 日銀タカ派観測、米雇用統計後のドル買い継続など）
    * センチメント（リスクオン / リスクオフ）
    * 重要イベントと時刻
    * 想定される主要シナリオ

---

## L2: テクニカル分析 (Technical Analysis)

チャートの状態とインジケーターを、LLMが扱いやすい形で言語化・構造化するフェーズ。

* **主体:**

  * GitHub Actions（OHLC集計・`ohlc_summary.json`生成）
  * mako（MT5チャートのスクショ選定）
  * Claude App（テキストへの落とし込み）

* **入力 (Input):**

  * `ohlc_summary.json`

    * 6通貨ペアのトレンド/サポレジ/ボラティリティ指標など
  * `chart_*.png`

    * MT5の1時間足スクショ × 最大6枚

* **出力 (Output):**

  * `L2_technical.md`
  * **内容例:**

    * 日足・1H・15mのマルチタイムフレーム分析
    * 明確なサポート/レジスタンス
    * トレンド状態（上昇/下降/レンジ）
    * SMA/EMA/RSIなどの位置・傾き
    * 代表的なチャートパターン（ダブルトップ、押し目、戻りなど）

---

## L3: 統合レポート & 予測 (Integration & Prediction)

L1 × L2 を統合して、
**「AIだけで考えたトレードプラン（ベースライン）」**を作るフェーズ。
ここが日次の基準モデルになる。

* **主体:**
  Claude App（Opus 4.5）

* **入力 (Input):**

  * L1 ファンダメンタルレポート (`L1_fundamental.md`)
  * L2 テクニカルレポート (`L2_technical.md`)

* **出力 (Output):**

  1. **📄 `L3_report.md`（人間用 / 公開用）**

     * Note / X に転用可能な文章レポート
     * Top3通貨ペアの選定理由
     * 東京・ロンドン各セッションの売買シナリオ
     * どの相場を狙い、どこを捨てるかの方針

  2. **💾 `L3_prediction.json`（システム・評価用 / AIベースライン）**

     * 各通貨ペアの環境認識（Bias, Volatility）
     * Top3 / Bottom3 ランキング
     * 各戦略の:

       * `direction`（LONG / SHORT）※必須
       * Entry / SL / TP の数値
       * 有効セッション（Tokyo / Londonなど）
     * **保存先:** `data/YYYY/MM/DD/L3_prediction.json`
     * **役割:**

       * 「AIだけで出した戦略」として、後で機械的に検証される対象

---

## L4: 実行 & 評価 (Action & Evaluation)

**「今日どう動くか」と「昨日の予測はどうだったか」を扱うフェーズ。**

L4は、

* A: HITLトレードプランの策定（人間＋AIの実行側）
* B: 評価エンジンによる自動評価（AI単体 vs HITL比較）
  の2つで構成される。

---

### L4-A: トレードプラン策定 (HITL Plan)

エントリー前に、**人間とAIが一緒にトレードプランを作るフェーズ。**

* **主体:**
  mako + Claude Project（HITL用プロジェクト）

* **タイミング:**
  実際にエントリーを検討する瞬間（1日に複数回ありうる）

* **入力 (Input):**

  * `L3_report.md`（AIベースラインの整理）
  * makoのリアルタイム環境認識・シナリオ
  * makoのトレードルール・手法（POG2など）

* **プロセス:**

  1. mako が「こういう意図でエントリーしたい」と素案を入力
  2. Claude が:

     * ルール整合性をチェック
     * SL/TPの妥当性をチェック
     * シナリオの文章を整形
  3. OKが出たプランだけを「HITLトレードプラン」として記録

* **出力 (Output):**

  * **`L4_tradeplan.json`**

    * 1回のエントリー意図ごとに1ファイル or 1オブジェクト
    * 内容イメージ:

      * pair / direction / timeframe
      * entry条件 / SL / TP
      * 想定シナリオ
      * ルール整合性チェック結果（OK/NG理由）
    * **役割:**

      * 「人間＋AIが共同で作った実際のトレードプラン」として、後でAI単体と比較される

---

### L4-B: 予実判定・比較評価 (Evaluation & Comparison)

`l3_evaluator.py` が担う領域。
**評価専用エンジン**として、

* AI単体の L3_prediction

* 人間＋AIの L4_tradeplan
  を **同じロジックで評価** し、比較を可能にする。

* **主体:**
  `l3_evaluator.py`（Python / CLI 手動実行）

* **実行方法 (現状):**

  * データが揃ったタイミングで、ターミナルからコマンド実行
  * 例（AIベースライン評価モード）:

    ```bash
    uv run python -m fx_kline.analyst.l3_evaluator \
      --mode ai \
      --pred-file data/2025/11/27/L3_prediction.json \
      --ohlc-root data/
    ```
  * 例（HITLプラン評価モード）:

    ```bash
    uv run python -m fx_kline.analyst.l3_evaluator \
      --mode hitl \
      --tradeplan-file data/2025/11/27/L4_tradeplan.json \
      --ohlc-root data/
    ```

* **評価モード:**

  1. **AIベースライン評価モード (`mode=ai`)**

     * **入力:**

       * `L3_prediction.json`
       * 確定済みOHLC（昨日など）
     * **出力:**

       * `L4_ai_evaluation.json`
     * **評価内容:**

       * 戦略ごとの Win / Loss / NoEntry
       * PnL（pips）、MFE / MAE
       * Bias の一致率（環境認識が当たっていたか）
       * Top3 選定の妥当性

  2. **HITLプラン評価モード (`mode=hitl`)**

     * **入力:**

       * `L4_tradeplan.json`（HITLプラン）
       * 確定済みOHLC
     * **出力:**

       * `L4_hitl_evaluation.json`
     * **評価内容:**

       * HITLプランの Win / Loss / NoEntry
       * PnL（pips）、MFE / MAE
       * どの修正・上書きがパフォーマンスにどう効いたか
       * 同一ペア・同一時間帯における **AI基準との差分**

* **役割のポイント:**

  * `l3_evaluator.py` は **「L3を評価するツール」ではなく、
    「AI戦略とHITL戦略の両方を評価する共通エンジン」**。
  * そのため、**入力 JSON に応じてモードを切り替えるだけ**で、
    ロジック（SL/TP判定・PnL計算・方向ロジック）は共通で使い回す。

---

## L5: 振り返り & 資産化 (Review & Journal)

AI評価と人間の主観・感情を統合し、
「次に活かせる形」で資産化するフェーズ。

* **主体:**

  * mako（レビュー記入）
  * GitHub Actions（集計・ダッシュボード更新）

* **入力 (Input):**

  * 実際のトレード履歴（pips / 収支 / ロット）
  * `L4_ai_evaluation.json`（AI単体の結果）
  * `L4_hitl_evaluation.json`（HITLプランの結果）
  * makoの感情・気づき・判断プロセス

* **出力 (Output):**

  1. **📝 `L5_review.yaml`（手動）**

     * 定量面:

       * 日次/週次の収支・勝率
       * AI vs HITL のパフォーマンス比較
       * 相場タイプ別（トレンド/レンジなど）の得意・不得意
     * 定性面:

       * どの修正が良かったか / 逆効果だったか
       * 感情トリガー（FOMO、連敗後のリベンジなど）
       * ルールから外れたトレードの理由と反省

  2. **📊 `README.md`（自動ダッシュボード）**

     * 期間別の勝率推移
     * AI予測精度 vs HITLの優位性
     * トレード履歴の一覧・リンク
     * 今後の改善ポイントのハイライト

---

## 📂 1日のデータセット構成

最終的に、GitHub の `data/YYYY/MM/DD/` は以下のような構成を目指す。

```text
2025/11/27/
├── ohlc_summary.json         # [L2] 客観的相場データ
├── L3_report.md              # [L3] AIベースラインの文章
├── L3_prediction.json        # [L3] AIだけの予測モデル (direction/Entry/SL/TP)
├── L4_tradeplan.json         # [L4] 人間＋AIのHITLトレードプラン（複数も可）
├── L4_ai_evaluation.json     # [L4] L3_prediction の評価結果
├── L4_hitl_evaluation.json   # [L4] L4_tradeplan の評価結果
└── L5_review.yaml            # [L5] 人間による振り返り・メモ
```

これが日々蓄積されることで、

* **「AIだけの戦略が強い相場」**
* **「人間＋AIのHITLが圧倒的に強い相場」**
* **「人間の介入が逆効果になっているパターン」**

を、定量・定性の両方から分析できるようになる。
最終的には、このデータセットが **「自分専用HITLトレーダーの教師データ」** になる。

---

## Note / TODO

* L3 qualitative eval: turn L3_evaluation.json into a brief narrative and store as L4_ai_evaluation.json to capture improvement points.
* L4_tradeplan eval: keep the same JSON route for qualitative/quantitative review so HITL plans are comparable later.
* L5 journal structure: trades.csv should support per-account and aggregated views; if needed, add separate files (e.g., trades_aggregate.csv, journal_L5.md) to keep logs organized.
