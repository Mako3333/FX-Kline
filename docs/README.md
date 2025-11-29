# FX HITL Trading System - Documentation Index（v2.4）

このプロジェクトは、**AI予測（L3）と人間判断（L4）を統合し、実トレード（L5）まで一貫して評価・改善可能な「裁量×AIトレードシステム」** を構築するためのドキュメント群です。

本ドキュメント（README）は、全体構造・ワークフロー・関連ドキュメントの入口として機能します。



---

# 📚 Overview

本システムのアーキテクチャは以下の 5 層構造で設計されています。

```
L1（ファンダ） → L2（テクニカル） → L3（AI予測） → L4（HITLプラン） → L5（レビュー & カルテ化）
                                                        ↓
                                           L3/L4 評価エンジン（学習ループ）
```

各レイヤーは独立しており、
**AI単体（L3）と HITL（L4）の価値比較** を行えるのが最大の特徴です。

2025年11月以降、本READMEは **L5レイヤー刷新（v2.4）** に伴い大幅にアップデートされています。

---

# 📖 Documentation Structure

docs フォルダに格納された各ドキュメントは役割別に整理されています。

## Core Documents（核となる文書）

### 1. **HITL_SYSTEM_ADVICE.md**

プロファンドマネージャー視点の体系的アドバイス。
リスク管理・コスト・市場環境・時間帯特性・バックテスト運用まで網羅。

### 2. **IMPLEMENTATION_GUIDE.md**

HITLトレーディングシステムの実装ガイド。
12週ロードマップ、日次ワークフロー、プロンプトセットアップ。

### 3. **L3_prompt_v1.md / v2.md**

AIによるL3_prediction.json 作成テンプレート。

### 4. **ACADEMIC_VALUE.md**

研究用途向け。学術性、キャリブレーション分析、データ公開方針。

### 5. **CONTENT_STRATEGY.md**

X / note を活用した情報発信・収益化モデル。

---

# 🚀 Quick Start Guide

### Trading（実装開始したい人向け）

1. HITL_SYSTEM_ADVICE.md を読む
2. IMPLEMENTATION_GUIDE.md Phase 1
3. makoトレードルール作成
4. L3/L4生成テスト
5. 日次ワークフロー構築

### Research（研究者向け）

* ACADEMIC_VALUE.md を参照
* 評価指標（Calibration / skill metrics）
* データ収集 → backtest_simulator（実装予定）

### Content（情報発信）

* CONTENT_STRATEGY.md
* 毎日のL3/L4比較結果を投稿
* 月次はnote有料記事化

---

# 🎯 Key Concepts（レイヤー別解説）

## L1: Fundamental

AIによる市場テーマ選定。
AIに与える「地ならし情報」。

## L2: Technical

自動生成された6通貨ペアのサマリー。
サポレジ・トレンド・RSI等の構造化JSON。

## L3: AI Prediction

純AIによる Top3 通貨ペア戦略（ベースライン）。
出力：**L3_prediction.json**

## L4: HITL Plan

人間の意図＋AI補正による実行プラン。
出力：**L4_tradeplan.json**

## L5: Review & Karte（v2.4）

HITL開発の中核。
**AI評価・実トレード・感情ログ・画像を1トレード単位に集約し、改善ループを形成するレイヤー。**

* 日次レビュー：**L5_review.yaml**
* 個別カルテ：**trade.yaml（1トレード単位）**
* ダッシュボード：Streamlit または Next.js
* 画像：Supabase Storage（容量問題を回避）

（詳細は「L5: 更新内容」章にて記載）

---

# 📊 System Components

## Implemented（実装済み）

* **L2 OHLC集計**
  `src/fx_kline/core/ohlc_aggregator.py`

* **L3/L4評価エンジン（v2.3）**
  `src/fx_kline/core/l3_evaluator.py`

* **6通貨ペア summary generator**
  summary_consolidator.py

* **L3 prediction prompt**
  docs/L3_prompt_v1.md, v2.md

* **GitHub Actions による日次実行**

---

## To Be Implemented（これから実装）

### Phase A：HITLトレード管理（最優先）

* [ ] `trades.csv` マルチ口座対応
* [ ] `trade.yaml` 生成（1トレード1カルテ）
* [ ] Supabase Storage 画像アップロード
* [ ] カレンダーUI（損益ビュー）
* [ ] トレード一覧 → カルテ遷移

### Phase B：L5レイヤー（レビュー/学習）

* [ ] L5_review.yaml v2.4スキーマ
* [ ] L3/L4評価との紐づけ自動化
* [ ] AI定性レビュー（LLM補助）
* [ ] 「keep / stop / try」改善指標の自動提案

### Phase C：ダッシュボード

* [ ] Streamlitダッシュボード
* [ ] 戦略別期待値
* [ ] regime × strategy ヒートマップ
* [ ] AI vs HITL の差分可視化

---

# 🔍 L5: Review, Karte & Knowledge Assets（v2.4）

**この章は今回最大のアップデートポイント。**

L5は「結果を見る」場所ではなく、
**AI × 人間の協働をチューニングする“改善エンジン”** として再定義。

---

## L5-1：日次レビュー（L5_review.yaml）

AI評価（L3/L4）、実トレード、感情ログを統合。

項目例：

```yaml
date: 2025-11-29
day_pnl: 27300
win_rate: 66.6

ai_vs_hitl:
  ai_pips: -12.3
  hitl_pips: +38.1
  delta: +50.4
  comment: "HITLは押し目のみ採用したのが勝因"

regime_eval:
  type: UPTREND
  ai_strength: "トレンド方向の認識は良好"
  hitl_strength: "タイミング最適化で優位性"
  human_harm: "指標前の逆張りは逆効果"

rule_adherence:
  violations: ["POG2条件未達のエントリー"]
  good: ["SL浅め案を採用した"]

emotions:
  triggers: ["眠気"]
  impact: "利確を早めすぎた"

improvements:
  keep_doing: ["H4ネックライン重視"]
  stop_doing: ["東京時間の逆張り"]
  try_next: ["AIからSL候補を3案出させる"]
```

---

## L5-2：個別トレードカルテ（trade.yaml）

1トレード = 1フォルダ方式。

```yaml
trade_id: "20251129_01"
pair: "USDJPY"
account_id: "XM_01"
direction: LONG

entry:
  price: 152.30
  reason: "1H押し目 + POG2一致"
  chart: "https://supabase.../entry.png"

exit:
  price: 152.95
  reason: "東京終盤のボラ低下"
  chart: "https://supabase.../exit.png"

context:
  regime: UPTREND
  higher_tf: "https://supabase.../h4.png"
  strategy: POG2

ai_ref:
  l3_ref: rank_1_long
  l4_ref: hitl_plan_id

evaluation:
  pnl_pips: 65
  rr: 2.1

notes:
  - "ヒゲは迷ったが正しい判断"
```

これを`\docs\template.html`で SSR するだけで、
「MyFXBookを超えるジャーナル」が完成する。

---

## L5-3：ダッシュボード

* 月次損益カレンダー（クリックで遷移）
* AI vs HITL 比較ライン
* 戦略期待値
* レジーム × 手法 のヒートマップ
* 口座別分析（国内/海外）

---

# 📁 Directory Structure（現状）
L1〜L4のデータ生成パイプラインは確立済み。
L5はこの構造の上に “histories” を追加する形で成立する。

```
data/
  YYYY/MM/DD/
    summaries/
    L1_fundamental.md
    L2_technical.md
    L3_report.md
    L3_prediction.json
    L4_tradeplan.json
    L3_evaluation.json
    L4_evaluation.json
    L5_review.yaml
    trades/
      trade_id/
        trade.yaml
        # 画像はSupabase（URLのみ）
```

---

# 🤝 Contributing

バグ修正、評価基準追加、分析ツール追加など歓迎。

---

---

# 🕒 Last Updated

**2025-11-29（v2.4 / L5刷新版）**
Maintainer: mako
License: MIT（code） / CC BY 4.0（docs）