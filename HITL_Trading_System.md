# 📊 FX HITL Trading System Architecture（v2.3）

## 全体コンセプト

* **目的:**
  人間（mako）とAIが協働する「人間承認型AIトレード (HITL Trading)」の、
  日次ワークフローとデータ構造を体系化する。

* **特徴:**
  * L1〜L3で「AIだけのベースライン」を作る
  * L4で「人間＋AIのHITLプラン」を作る
  * `l3_evaluator.py` で **AI単体 vs HITL** を共通の物差しで評価
  * L5で「定量 + 定性」の両側面から振り返る

* **スキーマバージョン:** 2.3
  * 複数戦略（Top3通貨ペア）の配列形式
  * confidence_score / confidence_breakdown による信頼度定量化
  * risk_reward_ratio / reasoning / alternative_scenario の必須化

---

## システム構成図

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        FX HITL Trading System                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │
│  │   L1    │───▶│   L2    │───▶│   L3    │───▶│   L4    │──┐       │
│  │ Funda-  │    │ Techni- │    │ Integra-│    │ Action &│  │       │
│  │ mental  │    │ cal     │    │ tion    │    │ Eval    │  │       │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │       │
│       │              │              │              │        │       │
│       ▼              ▼              ▼              ▼        ▼       │
│  L1_funda-      L2_techni-     L3_report.md   L4_tradeplan  L5     │
│  mental.md      cal.md         L3_prediction  L3_ai_evaluation review │
│                                .json          .json                 │
│                                             L3_hitl_evaluation.json │
└─────────────────────────────────────────────────────────────────────┘
```

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
    * 今日のメインテーマ（例: 日銀タカ派観測、米雇用統計後のドル買い継続など）
    * センチメント（リスクオン / リスクオフ）
    * 重要イベントと時刻
    * 想定される主要シナリオ

---

## L2: テクニカル分析 (Technical Analysis)

チャートの状態とインジケーターを、LLMが扱いやすい形で言語化・構造化するフェーズ。

* **主体:**
  * GitHub Actions（OHLC集計・`*_summary.json`生成）
  * mako（MT5チャートのスクショ選定）
  * Claude App（テキストへの落とし込み）

* **入力 (Input):**
  * `summaries/*_summary.json`
    * 6通貨ペアのトレンド/サポレジ/ボラティリティ指標など
  * `chart_*.png`
    * MT5の1時間足スクショ × 最大6枚

* **出力 (Output):**
  * `L2_technical.md`
  * **内容例:**
    * 日足・4H・1Hのマルチタイムフレーム分析
    * 明確なサポート/レジスタンス
    * トレンド状態（上昇/下降/レンジ）
    * SMA/EMA/RSIなどの位置・傾き
    * 代表的なチャートパターン（ダブルトップ、押し目、戻りなど）

* **データ構造:**
  ```text
  data/YYYY/MM/DD/
  ├── summaries/
  │   ├── USDJPY_summary.json
  │   ├── EURJPY_summary.json
  │   ├── AUDJPY_summary.json
  │   ├── EURUSD_summary.json
  │   ├── AUDUSD_summary.json
  │   └── XAUUSD_summary.json
  └── ohlc/
      ├── USDJPY_15m.csv
      ├── EURJPY_15m.csv
      └── ... (評価用15分足データ)
  ```

---

## L3: 統合レポート & 予測 (Integration & Prediction)

L1 × L2 を統合して、**「AIだけで考えたトレードプラン（ベースライン）」**を作るフェーズ。
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
     * **スキーマバージョン: 2.3**
     * 各通貨ペアの環境認識（Bias, Volatility）
     * Top3 / Bottom3 ランキング
     * **strategies[] 配列（Top3通貨のみ）:**
       * `pair`, `rank`, `strategy_type`, `direction`
       * `valid_sessions`: ["TOKYO", "LONDON"]
       * `entry`: zone_min, zone_max, strict_limit
       * `exit`: take_profit, stop_loss, invalidation
       * `confidence_score` (0.0-1.0)
       * `confidence_breakdown` (4つの信頼度指標)
       * `risk_reward_ratio`
       * `reasoning` (日本語)
       * `alternative_scenario` (direction, probability, reason)

* **プロンプトテンプレート:**
  * `docs/L3_prompt_v1.md` - 統合レポート生成用
  * `docs/L3_prompt_v2.md` - 詳細予測生成用

---

## L4: 実行 & 評価 (Action & Evaluation)

**「今日どう動くか」と「昨日の予測はどうだったか」を扱うフェーズ。**

L4は、
* A: HITLトレードプランの策定（人間＋AI）
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
     * 過去のデータから○○の方が期待値高いです。等のデータドリブンアドバイスで最適なIFO注文にブラッシュアップ
  3. OKが出たプランだけを「HITLトレードプラン」として記録

* **出力 (Output):**
  * **`L4_tradeplan.json`**
    * L3_prediction.json と同じスキーマ v2.3 形式
    * HITL固有の追加フィールド:
      * `modifications`: 人間による修正履歴
      * `position_size`, `risk_percent`
    * **役割:** 「人間＋AIが共同で作った実際のトレードプラン」として、後でAI単体と比較される

---

### L4-B: 予実判定・比較評価 (Evaluation & Comparison)

`src/fx_kline/core/l3_evaluator.py` が担う領域。
**評価専用エンジン**として、AI単体の L3_prediction と人間＋AIの L4_tradeplan を **同じロジックで評価** し、比較を可能にする。

* **主体:**
  `l3_evaluator.py`（Python / CLI 手動実行）

* **評価対象データ:**
  * 15分足OHLCデータ (`data/YYYY/MM/DD/ohlc/*_15m.csv`)
  * セッション別フィルタリング（TOKYO: 09:00-15:00, LONDON: 16:00-21:00 JST）

* **実行方法:**

  ```bash
  # AIベースライン評価モード
  uv run python -m fx_kline.core.l3_evaluator \
    --mode ai \
    --prediction data/2025/11/27/L3_prediction.json \
    --actual data/2025/11/28/summaries/USDJPY_summary.json \
    --output data/2025/11/27/L3_evaluation.json

  # HITLプラン評価モード
  uv run python -m fx_kline.core.l3_evaluator \
    --mode hitl \
    --prediction data/2025/11/27/L4_tradeplan.json \
    --actual data/2025/11/28/summaries/USDJPY_summary.json \
    --output data/2025/11/27/L4_evaluation.json
  ```

* **評価メトリクス（v2.3対応）:**

  | メトリクス | 説明 |
  |-----------|------|
  | `direction_correct` | 方向性が正しかったか |
  | `entry_hit` | エントリーゾーンに価格が到達したか |
  | `entry_timing_score` | エントリータイミングの質 (-1 to 1) |
  | `stop_loss_hit` | ストップロスがヒットしたか |
  | `take_profit_hit` | テイクプロフィットがヒットしたか |
  | `pips_outcome` | 獲得/損失pips |
  | `risk_reward_realized` | 実現リスク・リワード比 |
  | `confidence_calibration` | 信頼度と実際の精度の誤差 |

* **集計メトリクス:**

  | メトリクス | 説明 |
  |-----------|------|
  | `direction_accuracy` | 方向性正解率 |
  | `avg_confidence` | 平均信頼度 |
  | `avg_confidence_calibration` | 平均キャリブレーション誤差 |
  | `entry_hit_rate` | エントリーゾーン到達率 |
  | `total_pips` | 合計pips |
  | `accuracy_by_rank` | ランク別精度 |
  | `accuracy_by_regime` | 市場レジーム別精度 |

* **出力 (Output):**
  * `L3_evaluation.json` - AI単体の評価結果
  * `L4_evaluation.json` - HITLプランの評価結果

---

## L5: 振り返り・カルテ化・資産化（Review, Journal & Knowledge Assets）

L5は、
**AI評価（L3/L4）＋実トレード履歴＋人間の判断・感情＋画像（チャート）**
を一元化し、
**1トレード単位のカルテ** として資産化するフェーズ。

ここで蓄積されたデータは、
AI単体 vs HITL介入の優位性比較、
戦略別の期待値分析、
note/Xへのアウトプット、
さらには将来の「自分専用HITLトレーダー」の教師データ
として活用される。

---

### 主体

* **mako**
  実トレードの判断ログ、感情ログ、まとめレビューを入力。

* **LLM（Claude / ChatGPT）**
  Evaluatorの定性評価補助、レビューの圧縮、改善案生成。

* **GitHub Actions / スクリプト**
  日次集計、ダッシュボード更新、カルテ生成補助。

---

### 入力（Input）

L5で扱うデータは3階建て。

## 1. 評価データ（AI側）

* `L3_evaluation.json`（AI単体のベースライン評価）
* `L4_evaluation.json`（HITLプラン評価）

## 2. 実トレード（人間側）

* `trades.csv`（口座横断の実トレード履歴）

  * account_id
  * broker
  * pair
  * entry_price / exit_price
  * pnl_pips / pnl_jpy
  * size
  * direction
  * strategy（手法：POG2、MTF押し目、Wトップ etc.）
  * regime（UPTREND、RANGE、NEWS etc.）
  * l3_ref / l4_ref

## 3. 人間ログ（メンタル・判断）

* エントリー前の意図
* そのときの感情（FOMO、疲れ、迷いなど）
* その日に守れたルール・破ったルール
* 反省点と改善案

## 4. 画像（チャート文脈）

Supabase Storage に保存された URL（ローカル保存しない）

* entry_chart.png
* h4_context.png
* exit_chart.png
* 必要に応じてレイヤー画像（水平線・POG2ライン等）

---

### 出力（Output）

L5では「日次レビュー」と「1トレードカルテ」を分離して管理する。

---

## 1. 📝 `L5_review.yaml`（日次レビュー／資産化）

### 定量分析（AI vs HITL vs 実トレード）

* day_pnl
* win_rate
* ai_vs_hitl:

  * ai_pips
  * hitl_pips
  * delta
  * 評価コメント
* 戦略別の期待値
* regime別の得意/不得意

### 定性分析（人間ログ）

* good_decisions（良い修正）
* bad_decisions（逆効果だった修正）
* rule_violations（破ったルール）
* emotions:

  * FOMO
  * revenge
  * 疲れ
  * 迷い
* 今日の相場環境（トレンド/レンジ/ニュース相場）

### 明日への改善（Next Actions）

* keep_doing
* stop_doing
* try_next
* L4プロンプトに反映するTODO
* システム改善TODO（評価エンジン・ダッシュボードなど）

---

## 2. 📄 `trade.yaml`（1トレード単位のカルテ）

各トレードを「独立したカルテページ」として管理する。

```yaml
trade_id: "20251129_01"
date: "2025-11-29"
account_id: "XM_01"
pair: "USDJPY"
direction: "LONG"

entry:
  price: 152.30
  datetime: "2025-11-29T10:32:00+09:00"
  reason: "1H押し目 + POG2条件一致"
  chart: "https://supabase.../entry_chart.png"

exit:
  price: 152.95
  datetime: "2025-11-29T13:59:00+09:00"
  reason: "東京終盤のボラ低下"
  chart: "https://supabase.../exit.png"

context:
  higher_tf: "https://supabase.../h4_context.png"
  regime: UPTREND
  strategy: POG2

ai_ref:
  l3_strategy: "rank_1_long"
  l4_plan: "hitl_plan_id"

evaluation:
  pnl_pips: 65
  rr: 2.1
  entry_quality: "Good"
  exit_quality: "OK"

notes:
  - "東京の押し目は素直だがヒゲで迷った"
  - "AI案のSL浅め設定を採用したのが効いた"
```

この `trade.yaml` を Jinja/Next.js でレンダリングすれば、あなたが提示したHTMLカルテがそのまま表示される。

---

## 3. 📊 ダッシュボード（README.md, Streamlit, Next.jsなど）

* 月次損益カレンダー（あなたの画像のUI）
* クリックすると日次ページへ
* さらにクリックで「その日の各トレード一覧」
* そして各トレードカルテへ
* 勝率グラフ
* AI vs HITL比較
* 戦略別期待値
* regime × strategy のヒートマップ
* 口座横断集計（account_idでフィルタ）

---

## L5 の責務と流れ（改定版）

```
L3_prediction      ┐
                   │（AIの事前予測）
L4_tradeplan       ┘
        │
l3_evaluator.py → L3_evaluation.json / L4_evaluation.json
        │
        ├── trades.csv（実トレード）
        ├── trade.yaml（1トレードカルテ）
        └── L5_review.yaml（日次レビュー）
                ↓
             ダッシュボード（可視化）
```

**L5は「評価 + 実トレード + 人間の判断」を統合し、次の改善に繋げるメタレイヤー。**

---

## 実装済み／これから実装するもの（明確化）

## ✔ 実装済み（v2.3）

* L3 / L4 の評価エンジン
* L3_prediction.json / L4_tradeplan.json の標準化
* 評価メトリクス（方向性・RR・pips・confidence_calibration）
* L5_review.yaml（簡易版）

---

## ▶ これから実装する（v2.4〜v2.6）

**優先順に記載**

### [1] trades.csv（マルチ口座対応）

* broker
* account_id
* strategy
* regime
* l3_ref
* l4_ref
* pnl_pips / pnl_jpy

### [2] trade.yaml（1トレードカルテの標準化）

* Entry/Exit理由
* 画像URL
* AI参照（L3/L4）
* 評価

### [3] Supabase Storageに画像保存（容量問題の解決）

* entry・上位足・exit の3〜5枚/トレード
* 自動アップロードスクリプト
* trade.yaml にURL自動埋め込み

### [4] カレンダーUI（あなたのスクショUIを再現）

* 日別損益を trades.csv から自動表示
* 日クリック→その日のトレード一覧
* トレードクリック→カルテHTMLへ

### [5] カルテHTML（あなたの提示テンプレをSSR化）

* Next.js または Flask + Jinja
* trade.yaml を読み込んで生成

### [6] L5_review.yaml（最終スキーマ）

* keep_doing / stop_doing / try_next
* rule_violations
* emotionログ
* AI vs HITL総括

### [7] ダッシュボード（Streamlit）

* 勝率、戦略別期待値
* regime別成績
* カレンダー連動
* AI vs HITL比較

---

## L5 フェーズの最終結論

> **L5 = 評価・実トレード・画像・感情ログを統合し、
> 1日分と1トレード分のカルテとして資産化する「メタ評価レイヤー」**

あなたが提示したHTMLカルテを中心に据え、
AI単体 vs HITL介入の差分を学習し、
日々の改善に直結する構造が完成する。




## 📂 1日のデータセット構成

最終的に、GitHub の `data/YYYY/MM/DD/` は以下のような構成を目指す。

```text
data/2025/11/27/
├── summaries/                    # [L2] 通貨ペア別サマリー
│   ├── USDJPY_summary.json
│   ├── EURJPY_summary.json
│   ├── AUDJPY_summary.json
│   ├── EURUSD_summary.json
│   ├── AUDUSD_summary.json
│   └── XAUUSD_summary.json
├── ohlc/                         # [L2] 15分足OHLCデータ（評価用）
│   ├── USDJPY_15m.csv
│   ├── EURJPY_15m.csv
│   └── ...
├── L1_fundamental.md             # [L1] ファンダメンタル分析
├── L2_technical.md               # [L2] テクニカル分析（人間作成）
├── L3_report.md                  # [L3] AIベースラインの文章レポート
├── L3_prediction.json            # [L3] AIだけの予測モデル (v2.3 schema)
├── L4_tradeplan.json             # [L4] 人間＋AIのHITLトレードプラン
├── L3_evaluation.json            # [L4] L3_prediction の評価結果
├── L4_evaluation.json            # [L4] L4_tradeplan の評価結果
└── L5_review.yaml                # [L5] 人間による振り返り・メモ
```

これが日々蓄積されることで、
* **「AIだけの戦略が強い相場」**
* **「人間＋AIのHITLが圧倒的に強い相場」**
* **「人間の介入が逆効果になっているパターン」**

を、定量・定性の両方から分析できるようになる。
最終的には、このデータセットが **「自分専用HITLトレーダーの教師データ」** になる。

---

## 🔧 コードベース構成

```text
src/fx_kline/
├── core/
│   ├── l3_evaluator.py      # L3/L4 評価エンジン（v2.3対応）
│   ├── ohlc_aggregator.py   # OHLC集計
│   ├── data_fetcher.py      # データ取得
│   ├── models.py            # Pydanticモデル
│   ├── timezone_utils.py    # JST時間ユーティリティ
│   ├── business_days.py     # 営業日計算
│   └── validators.py        # バリデーション
├── analyst/
│   ├── l3_evaluator.py      # 旧評価エンジン（互換性維持）
│   └── data_manager.py      # データディレクトリ管理
├── mcp/
│   ├── server.py            # MCPサーバー
│   └── tools.py             # MCPツール定義
└── ui/
    └── streamlit_app.py     # Streamlit UI

scripts/
├── archive_ohlc_for_day.py  # 日次OHLCアーカイブ
└── prepare_daily_data.py    # 日次データ準備

docs/
├── L3_prompt_v1.md          # L3統合レポートプロンプト（v2.3）
├── L3_prompt_v2.md          # L3詳細予測プロンプト（v2.3）
├── HITL_SYSTEM_ADVICE.md    # システム設計アドバイス
├── IMPLEMENTATION_GUIDE.md  # 実装ガイド
└── MCP_SETUP.md             # MCPセットアップガイド
```

---

## 📊 L3_prediction.json スキーマ v2.3

```json
{
  "meta": {
    "version": "1.0",
    "schema_version": "2.3",
    "generated_at": "2025-11-27T09:00:00+09:00",
    "model": "claude-sonnet-4.5"
  },
  "market_environment": {
    "USDJPY": { "bias": "BULLISH", "vol_expect": "MEDIUM" },
    "EURJPY": { "bias": "BEARISH", "vol_expect": "HIGH" },
    ...
  },
  "ranking": {
    "top_3": ["USDJPY", "AUDJPY", "XAUUSD"],
    "bottom_3": ["EURUSD", "AUDUSD", "EURJPY"],
    "selection_rationale": "ドル高継続、ファンダとMTFが完全一致"
  },
  "strategies": [
    {
      "pair": "USDJPY",
      "rank": 1,
      "strategy_type": "DIP_BUY",
      "direction": "LONG",
      "valid_sessions": ["TOKYO", "LONDON"],
      "entry": {
        "zone_min": 151.50,
        "zone_max": 151.80,
        "strict_limit": 151.50
      },
      "exit": {
        "take_profit": 152.90,
        "stop_loss": 150.80,
        "invalidation": 150.50
      },
      "confidence_score": 0.75,
      "confidence_breakdown": {
        "technical_alignment": 0.80,
        "trend_strength": 0.70,
        "support_resistance_proximity": 0.90,
        "fundamental_alignment": 0.60
      },
      "risk_reward_ratio": 2.00,
      "reasoning": "テクニカルは強い上昇トレンドを示唆。151.50が主要サポート。",
      "alternative_scenario": {
        "direction": "WAIT",
        "probability": 0.25,
        "reason": "雇用統計での大きなボラティリティの可能性"
      }
    },
    ...
  ]
}
```

---

## Note / TODO

* [ ] `src/fx_kline/analyst/l3_evaluator.py` を `core/l3_evaluator.py` に統合し、重複を解消
* [ ] GitHub Actions で日次評価を自動実行するワークフローを追加
* [ ] L5_review.yaml のスキーマを定義し、自動集計スクリプトを作成
* [ ] ダッシュボード（README.md）の自動生成スクリプトを実装
* [ ] 週次/月次のパフォーマンスレポート生成機能を追加

---

**最終更新日:** 2025-11-29
**スキーマバージョン:** 2.3
**メンテナー:** mako
