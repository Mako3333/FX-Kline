# [Target] L3 予測プロンプト (L3 Prediction Prompt)

このプロンプトを Claude (Sonnet 4.5 推奨) で使用して、`L3_prediction.json` を生成します。
**スキーマバージョン: 2.3** (L3_prompt_v1.md と統合)

-----

## [System] システムプロンプト

以下のテキストをコピーして、Claudeのシステムプロンプト（または最初のメッセージ）として使用してください。

```markdown
あなたは、ファンダメンタルズ分析とテクニカル分析を統合してトレード予測を行う「エキスパートFXトレードAI」です。あなたの役割は、提供された L1（ファンダメンタルズ）および L2（テクニカル）レポートのみに基づき、人間の介入なしに**構造化された定量的予測**を生成することです。

**出力フォーマット** (schema_version 2.3):
以下の構造を持つ有効なJSONオブジェクトを出力してください。L3_prompt_v1.md の統合フォーマットに準拠：

```json
{
  "meta": {
    "version": "1.0",
    "schema_version": "2.3",
    "generated_at": "2025-11-27T15:30:00+09:00",
    "model": "claude-sonnet-4.5"
  },
  "market_environment": {
    "USDJPY": {
      "bias": "BULLISH|BEARISH|RANGE|MIXED",
      "vol_expect": "HIGH|MEDIUM|LOW"
    },
    "EURUSD": {
      "bias": "BULLISH|BEARISH|RANGE|MIXED",
      "vol_expect": "HIGH|MEDIUM|LOW"
    },
    "AUDUSD": {
      "bias": "BULLISH|BEARISH|RANGE|MIXED",
      "vol_expect": "HIGH|MEDIUM|LOW"
    },
    "EURJPY": {
      "bias": "BULLISH|BEARISH|RANGE|MIXED",
      "vol_expect": "HIGH|MEDIUM|LOW"
    },
    "AUDJPY": {
      "bias": "BULLISH|BEARISH|RANGE|MIXED",
      "vol_expect": "HIGH|MEDIUM|LOW"
    },
    "XAUUSD": {
      "bias": "BULLISH|BEARISH|RANGE|MIXED",
      "vol_expect": "HIGH|MEDIUM|LOW"
    }
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
      "reasoning": "テクニカルは強い上昇トレンドを示唆。151.50-151.80が主要サポート。ファンダメンタルはドル高支持だが、明日の雇用統計を控えており、短期的には慎重姿勢。",
      "alternative_scenario": {
        "direction": "WAIT",
        "probability": 0.25,
        "reason": "雇用統計での大きなボラティリティの可能性"
      }
    }
  ]
}
```

**主要ガイドライン**:

1. **方向性の決定 (Direction)**:
   - "LONG": 強気セットアップ (確信度 > 0.65)
   - "SHORT": 弱気セットアップ (確信度 > 0.65)
   - "WAIT": 不明確またはシグナルが矛盾 (確信度 < 0.65)

2. **確信度スコア計算 (Confidence Score)** (0.0-1.0):
   - Technical alignment: いくつのテクニカル指標が一致しているか (SMA順列, EMA反応, サポレジ接近度)
   - Trend strength: ADX > 25 → 高, ADX < 20 → 低
   - Support/Resistance proximity: 価格が重要レベルに近い → 高
   - Fundamental alignment: L1のテーマがテクニカルの方向と一致 → 高

   最終確信度 = 加重平均:
   - テクニカル: 40%
   - トレンド強度: 25%
   - サポレジ接近度: 20%
   - ファンダメンタル: 15%
   
   **計算式**: `confidence_score = 0.40 × technical_alignment + 0.25 × trend_strength + 0.20 × support_resistance_proximity + 0.15 × fundamental_alignment`

3. **エントリーゾーン (Entry Zone)**:
   - v2.3スキーマでは `entry.zone_min`, `entry.zone_max`, `entry.strict_limit` を使用
   - LONG: zone_minは直近サポート、zone_maxはその上、strict_limitは推奨エントリー
   - SHORT: zone_minは推奨エントリー、zone_maxは直近レジスタンス
   - L2レポートの 1h または 4h のサポレジを使用すること
   - direction="WAIT" の場合は entry フィールドすべて null に設定

4. **Exit フィールド**:
   - `exit.stop_loss`: LONG の場合は直近サポート - (ATR × 0.5)、SHORT の場合は直近レジスタンス + (ATR × 0.5)
   - `exit.take_profit`: リスクリワード比が 2:1 以上になるように設定。L2の次の主要レジスタンス(LONG)またはサポート(SHORT)を使用
   - `exit.invalidation`: 戦略が無効化されるレベル（アカウントの2%以上のリスクを負わないこと）
   - direction="WAIT" の場合は exit フィールドすべて null に設定

6. **理由 (Reasoning)**:
   - **日本語**で記述すること
   - 簡潔に (2-3文)
   - 決定に至った「主要な理由」を説明すること
   - 重要なサポレジレベルに言及すること

7. **代替シナリオ (Alternative Scenario)**:
   - 常に「次善のシナリオ」を提供すること
   - 確率を見積もること。**必須要件**: `confidence_score + alternative_scenario.probability = 1.0`（許容誤差: ±0.01）
   - リスク管理のために使用される
   - **バリデーション**: JSONスキーマ検証後、確率の合計が1.0であることを確認すること（不一致はセマンティックエラーとして扱う）

**重要事項**:
- 人間の好み、リスク許容度、トレードスタイルは考慮しないこと
- これは L1+L2 データのみに基づく「純粋なAI予測」である
- 確信度スコアは保守的に見積もること (過信を避ける)
- L1 と L2 が矛盾する場合は、確信度を下げて「WAIT」に傾けること
```

-----

## [Ex] 使用例 (Example Usage)

### 入力: L1 + L2 レポート

**L1 ファンダメンタルズ (要約)**:

```text
市場テーマ: ドル高継続
- FRBハト派姿勢後退（インフレ再燃懸念）
- 日銀は追加利上げに慎重姿勢
- 米雇用統計は明日22:30発表（高リスク）
```

**L2 テクニカル (USDJPY 要約)**:

```text
1d: Trend=UP, SMA ordering=bullish, EMA25 support bounce
    Support: [151.50, 150.80], Resistance: [153.20, 154.50]
    RSI=58, ATR=1.20

4h: Trend=UP, SMA ordering=bullish
    Support: [151.80, 151.50], Resistance: [152.90, 153.20]
    RSI=62, ATR=0.45

1h: Trend=UP, SMA ordering=bullish
    Support: [152.10, 151.90], Resistance: [152.70, 153.00]
    RSI=65, ATR=0.25
```

### ユーザーから Claude へのプロンプト入力

```text
以下のL1とL2レポートに基づいて、L3_prediction.jsonを生成してください。

# L1 Fundamental Analysis
[L1ファイルの内容を貼り付け]

# L2 Technical Analysis
[L2ファイルの内容を貼り付け]

上記のシステムプロンプトに従い、JSON形式で予測を出力してください。
現在価格: USDJPY 152.30
```

### 期待される出力 (L3\_prediction.json v2.3)

```json
{
  "meta": {
    "version": "1.0",
    "schema_version": "2.3",
    "generated_at": "2025-11-27T15:30:00+09:00",
    "model": "claude-sonnet-4.5"
  },
  "market_environment": {
    "USDJPY": {
      "bias": "BULLISH",
      "vol_expect": "HIGH"
    },
    "EURUSD": {
      "bias": "RANGE",
      "vol_expect": "MEDIUM"
    },
    "AUDUSD": {
      "bias": "BEARISH",
      "vol_expect": "MEDIUM"
    },
    "EURJPY": {
      "bias": "BEARISH",
      "vol_expect": "MEDIUM"
    },
    "AUDJPY": {
      "bias": "BEARISH",
      "vol_expect": "MEDIUM"
    },
    "XAUUSD": {
      "bias": "RANGE",
      "vol_expect": "HIGH"
    }
  },
  "ranking": {
    "top_3": ["USDJPY"],
    "bottom_3": ["EURJPY", "AUDJPY", "AUDUSD"],
    "selection_rationale": "高インパクトイベント控えのため、確信度が高い通貨ペアは限定される"
  },
  "strategies": [
    {
      "pair": "USDJPY",
      "rank": 1,
      "strategy_type": "BREAKOUT",
      "direction": "WAIT",
      "valid_sessions": ["TOKYO", "LONDON"],
      "entry": {
        "zone_min": null,
        "zone_max": null,
        "strict_limit": null
      },
      "exit": {
        "take_profit": null,
        "stop_loss": null,
        "invalidation": null
      },
      "confidence_score": 0.45,
      "confidence_breakdown": {
        "technical_alignment": 0.85,
        "trend_strength": 0.75,
        "support_resistance_proximity": 0.60,
        "fundamental_alignment": 0.70
      },
      "risk_reward_ratio": null,
      "reasoning": "テクニカルは強い上昇トレンド（SMA配列完全ブル、RSI好況水準）を示唆。151.50が主要サポート。しかし明日の米雇用統計（高インパクト）を24時間以内に控えており、エントリーリスクが高い。統計発表後の反応を見てから判断すべき。",
      "alternative_scenario": {
        "direction": "LONG",
        "probability": 0.55,
        "reason": "雇用統計が予想通りならドル買い継続。151.50サポートからのロング有効。目標は152.90〜153.20"
      }
    }
  ]
}
```

**この例の分析**:

  * ✔ テクニカル指標は強気 (technical_alignment=0.85, trend_strength=0.75)
  * ✔ ファンダメンタルズもドル高支持 (fundamental_alignment=0.70)
  * × **しかし**: 24時間以内に高インパクトイベント（雇用統計）がある
  * **結果**: 確信度0.45で **direction="WAIT"** を出力
    - entry/exit/risk_reward_ratio は null に設定（戦略無効）
  * **代替案**: イベント通過後の LONG（確率 0.55）
    - 151.50サポートからのロング、目標152.90-153.20

**この例が示すもの**: リスクが存在する場合の**「保守的なAI判断」**
- 高パフォーマンステクニカルでも、イベントリスクが高確信度を阻害する
- confidence_score < 0.65 のとき WAIT を出力する判定基準を遵守
- 代替シナリオで「イベント通過後の戻り」を記録

-----

## [\!] 確信度スコアの調整ガイドライン

AIの「確信度」と実際の「予測精度」を一致させるための基準です。

### 高確信度 (0.75 - 0.90)

**条件**:

  * ✔ 全ての時間足 (1h, 4h, 1d) が同じトレンドを示している
  * ✔ 価格が強力なサポレジ付近にある
  * ✔ ファンダメンタルズのテーマがテクニカルと一致している
  * ✔ 48時間以内に高インパクトイベントがない
  * ✔ 市場レジームが TRENDING (ADX \> 25) である

**例**: 明確な上昇トレンド + ドル高ファンダ + サポート反発

### 中確信度 (0.55 - 0.75)

**条件**:

  * [\!] 多くの時間足は一致しているが、1つが矛盾している
  * [\!] サポート/レジスタンスがやや不明確
  * [\!] ファンダメンタルズが中立
  * [\!] 市場レジームが混在している

**例**: 日足は上昇だが、1時間足で短期的な弱さが見られる

### 低確信度 (0.35 - 0.55)

**条件**:

  * × 時間足間でシグナルが矛盾している
  * × 価格がレンジの中間にあり、明確なサポレジがない
  * × ファンダメンタルズが不明確または混在
  * × 市場レジームが CHOPPY（方向感なし）

**例**: 日足上昇、4時間足下降、1時間足横ばい

### 超低確信度 (0.00 - 0.35)

**条件**:

  * × 全ての次元でシグナルが激しく矛盾
  * × 高インパクトイベントが差し迫っている
  * × 極端なボラティリティ (ATRが歴史的平均を大きく上回る)

**推奨**: 確信度が 0.50 未満の場合は、常に **WAIT** を出力させる。

-----

## [Fix] 特定ニーズに合わせたプロンプト調整

### より積極的な予測にする場合

確信度のしきい値を変更します：

```
"LONG" / "SHORT": confidence > 0.55 (通常 0.65)
"WAIT": confidence < 0.55 (通常 0.65)
```

### より保守的な予測にする場合

追加のフィルターを加えます：

```
- リスクリワード比 ≥ 3:1 を必須とする (通常 2:1)
- 高インパクトイベントの48時間前はトレードしない (通常 24時間)
- TRENDING確認のために ADX > 30 を要求する (通常 25)
```

### 特定の通貨ペア向け

ペア固有のルールを追加します：

```
USDJPY:
  - 日銀/FRBの政策乖離に重みを置く
  - 150.00, 152.00, 155.00 などの心理的節目（キリ番）を尊重する

EURUSD:
  - ECB/FRB政策に重みを置く
  - 1.0500, 1.1000 などの主要レベルを尊重する

XAUUSD (Gold):
  - 実質金利、地政学的リスクに重みを置く
  - リスクオフイベントに対して非常に敏感に反応させる
```

-----

## [Test] テストと検証

### 1\. プロンプトのテスト・チェックリスト

本番使用前の確認事項：

  * ☐ 強気L1 + 強気L2 → **LONG** が出力されるか
  * ☐ 弱気L1 + 弱気L2 → **SHORT** が出力されるか
  * ☐ 強気L1 + 弱気L2 → **WAIT** (矛盾) が出力されるか
  * ☐ イベント接近フラグあり → **WAIT** が出力されるか
  * ☐ 確信度スコアの計算 → ガイドラインと一致しているか
  * ☐ JSONスキーマの検証 → 有効なJSONか
  * ☐ **確率の合計チェック**: `confidence_score + alternative_scenario.probability = 1.0` が成立しているか（許容誤差: ±0.01）

### 2\. 確信度のキャリブレーション確認

30件以上の予測データが溜まった後に実行：

```python
import pandas as pd
import matplotlib.pyplot as plt

# 評価結果の読み込み
df = pd.read_json("evaluations/all_l3_results.json")

# キャリブレーションプロット作成
df['confidence_bin'] = pd.cut(df['confidence_score'], bins=[0, 0.5, 0.7, 0.9, 1.0])
calibration = df.groupby('confidence_bin')['direction_correct'].mean()

# 期待値: confidence_bin と実際の精度(accuracy)が一致すべき
# 例: 0.7-0.9 のビンは、約80%の精度があるはず
print(calibration)
```

**期待される結果**:

```
confidence_bin
(0.0, 0.5]     0.45  # 少し自信過小 (良い傾向)
(0.5, 0.7]     0.62  # 適正に調整されている
(0.7, 0.9]     0.78  # 適正に調整されている
(0.9, 1.0]     0.85  # 少し自信過剰気味
```

もしAIが一貫して自信過剰/過小であれば、確信度計算式の重み付けを調整します。

-----

## [Link] l3\_evaluator.py との統合

生成された **L3\_prediction.json** は、評価スクリプトとシームレスに連携するように設計されています：

```bash
# L3予測の生成
# (上記のプロンプトを用いてClaudeで生成)

# 翌日:実際の結果と比較評価
python -m fx_kline.core.l3_evaluator \
  --mode ai \
  --prediction data/2025-11-27/L3_prediction.json \
  --actual data/2025-11-28/ohlc_summary.json \
  --output data/2025-11-27/L4_ai_evaluation.json \
  --market-regime TRENDING

# 結果の確認
cat data/2025-11-27/L4_ai_evaluation.json
```

評価スクリプトは自動的に以下を行います：

  * ✔ 方向性の正解率チェック
  * ✔ エントリータイミングのスコアリング
  * ✔ 実現pipsの計算（もしトレードしていたら）
  * ✔ 確信度の誤差（Calibration Error）測定
  * ✔ 市場レジームごとの分類
  * ✔ **確率の合計バリデーション**: `confidence_score + alternative_scenario.probability` が 1.0 に等しいことを検証（不一致の場合はエラーとして記録）

-----

## [Auto] 自動化ワークフロー

日次自動化のスクリプト例：

```bash
#!/bin/bash
# daily_l3_generation.sh

DATE=$(date +%Y-%m-%d)
DATA_DIR="data/${DATE}"

# 1. OHLCデータ取得 (GitHub Actionsで自動化済み)
# 2. L2 テクニカル分析生成 (ohlc_aggregator.py)
# 3. L1 ファンダメンタルズ分析の手動作成 (makoの担当)

# 4. Claude API経由で L3 予測を生成
claude_api_call.py \
  --l1 "${DATA_DIR}/L1_fundamental.md" \
  --l2 "${DATA_DIR}/L2_technical.md" \
  --output "${DATA_DIR}/L3_prediction.json" \
  --prompt docs/L3_prompt_v2.md

# 5. (翌日) L3 予測の評価
# これはcron経由で翌日に自動実行される
```

-----

## [Grow] 学習と改善

### フィードバックループ

毎週、L3のパフォーマンスをレビューします：

1.  **失敗パターンの特定**:

      * L3の予測はどこで間違ったか？
      * CHOPPY（レンジ）相場で自信過剰になっていなかったか？
      * ファンダメンタルズのリスクを見逃していなかったか？

2.  **プロンプトの洗練**:

      * 失敗パターンに対する特定のルールを追加する
      * 確信度計算の重みを調整する
      * リスクフィルターを更新する

3.  **再テスト**:

      * 更新したプロンプトを過去30日分に適用する
      * 新しい予測と古い予測を比較する
      * キャリブレーションの改善を検証する

### 改善サイクルの例

**1週目の発見**:
L3は TRENDING 相場で65%の精度だが、CHOPPY 相場では40%しかない。
**アクション**:
ルール追加：「L2レポートで `market_regime=CHOPPY` の場合、確信度に 0.7 を掛ける」

**2週目の発見**:
L3が自信過剰である（平均確信度 0.75 に対し、実際の精度 0.60）。
**アクション**:
確信度計算式の重みを再調整。ファンダメンタルズの比重を15%から10%に下げる。

-----

## [Ref] 参考文献

### 関連ドキュメント

  * `HITL_SYSTEM_ADVICE.md`: システム設計全体とリスク管理
  * `ACADEMIC_VALUE.md`: 研究方法論と統計的厳密性
  * `l3_evaluator.py`: 評価スクリプトのソースコード

### バージョン履歴

  * **v2.1** (2025-11-29): スキーマ統合版 - L3_prompt_v1.md v2.3と統合
    - JSONスキーマを v1.md の `meta/market_environment/ranking/strategies` 形式に変更
    - `confidence_breakdown`, `risk_reward_ratio`, `alternative_scenario` を必須化
    - `entry/exit` フィールドを v1.md の形式に統一
    - direction="WAIT" のときの null ハンドリングを明確化
  * **v2.0** (2025-11-28): プロンプトテンプレート初版
  * 将来: 実証データに基づいて更新予定

-----

**最終更新日**: 2025-11-28
**メンテナー**: mako
**ステータス**: 本番運用可能