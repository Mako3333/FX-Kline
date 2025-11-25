# Daily OHLC Analysis Workflow

自動化された日次OHLC分析ワークフローの完全なドキュメント。

## 概要

このワークフローは、主要通貨ペアのOHLCデータを毎営業日（月曜〜金曜）に自動取得し、テクニカル分析を実行して統合レポートを生成します。

**ワークフローファイル**: `daily_ohlc_analysis.yml`

## 実行スケジュール

### 自動実行（スケジュール）

```yaml
cron: "15 23 * * 0-4"
```

| UTC曜日 | UTC時刻 | JST曜日 | JST時刻 | 実行 |
|---------|---------|---------|---------|------|
| 日曜 23:15 | 23:15 | 月曜 | 08:15 | ✅ |
| 月曜 23:15 | 23:15 | 火曜 | 08:15 | ✅ |
| 火曜 23:15 | 23:15 | 水曜 | 08:15 | ✅ |
| 水曜 23:15 | 23:15 | 木曜 | 08:15 | ✅ |
| 木曜 23:15 | 23:15 | 金曜 | 08:15 | ✅ |
| 金曜 23:15 | 23:15 | 土曜 | 08:15 | ❌ |
| 土曜 23:15 | 23:15 | 日曜 | 08:15 | ❌ |

**重要**: GitHub ActionsはUTC時刻で実行されるため、JST時刻の1日前の曜日を指定する必要があります。

### 手動実行

GitHubのActionsタブから `workflow_dispatch` で任意のタイミングで実行可能です。

---

## 処理フロー詳細

### 全体フロー

```
1. CSVファイル取得（18個）
   ↓
2. 個別分析JSON生成（18個）
   ↓
3. 通貨ペア別統合サマリー生成（6個）
   ↓
4. アーティファクトアップロード（7日間保存）
```

---

### ステップ1: CSVファイル取得

**実行コマンド**: Python inline script via `uv run`

**処理内容**:
- yfinance APIを使用して市場データ取得
- 6通貨ペア × 3時間足 = **18個のCSVファイル**生成

**対象通貨ペア**:
```
USDJPY, EURUSD, AUDJPY, AUDUSD, GBPJPY, XAUUSD
```

**時間足と期間**:
| 時間足 | 期間 | データ量目安 |
|--------|------|-------------|
| 1h | 10日 | 240本（10日×24時間） |
| 4h | 35日 | 210本（35日×6本/日） |
| 1d | 200日 | 200本（200営業日） |

**出力先**: `./csv_data/`

**ファイル命名規則**: `{PAIR}_{INTERVAL}_{PERIOD}.csv`

**例**:
```
csv_data/
├── USDJPY_1h_10d.csv
├── USDJPY_4h_35d.csv
├── USDJPY_1d_200d.csv
├── EURUSD_1h_10d.csv
├── ... (18ファイル)
```

**タイムゾーン処理**:
- **入力**: yfinance APIからUTC時刻で取得
- **変換**: `convert_dataframe_to_jst()` でJSTに変換
- **出力**: CSVのDatetimeカラムは `YYYY-MM-DD HH:MM:SS JST` 形式

---

### ステップ2: 個別分析JSON生成

**実行コマンド**:
```bash
uv run python ohlc_aggregator.py --input-dir ./csv_data --output-dir ./reports --verbose
```

**処理内容**:
- 各CSVファイルに対してテクニカル分析を実行
- 18個のCSV → 18個の個別分析JSON（**schema_version=1**）

**計算される指標**:

| 指標 | 説明 | 実装詳細 |
|------|------|----------|
| **trend** | UP/DOWN/SIDEWAYS | 0.2%閾値、価格変化率60% + 平滑化スロープ40%の加重平均 |
| **support_levels** | サポートライン（2本） | 期間内の最安値2つ |
| **resistance_levels** | レジスタンスライン（2本） | 期間内の最高値2つ |
| **RSI14** | 相対力指数 | Wilderの平滑化（EWM alpha=1/14） |
| **ATR14** | 平均真の範囲 | 14期間のローリング平均 |
| **average_volatility** | 平均ボラティリティ | 高値-安値の平均、フォールバックは標準偏差 |

**出力先**: `./reports/`

**ファイル命名規則**: `{PAIR}_{INTERVAL}_{PERIOD}_analysis.json`

**JSONスキーマ (schema_version=1)**:
```json
{
  "pair": "USDJPY",
  "interval": "1h",
  "period": "10d",
  "trend": "UP",
  "support_levels": [149.85, 149.92],
  "resistance_levels": [151.20, 151.05],
  "rsi": 62.45,
  "atr": 0.3245,
  "average_volatility": 0.2812,
  "generated_at": "2025-11-25T08:00:00+09:00",
  "schema_version": 1
}
```

**タイムゾーン処理**:
- **入力**: CSVファイル（JST）
- **読み込み**: `pd.to_datetime(..., utc=True)` でUTC awareとして解析
- **出力**: `generated_at`フィールドはJST（`get_jst_now().isoformat()`）

---

### ステップ3: 通貨ペア別統合サマリー生成

**実行コマンド**:
```bash
uv run python consolidate_summaries.py --reports-dir ./reports --output-dir ./summary_reports --verbose
```

**処理内容**:
- 同じ通貨ペアの複数時間足分析を1ファイルに統合
- 18個の個別JSON → 6個の統合サマリーJSON（**schema_version=2**）

**統合ロジック**:
1. `reports/` ディレクトリから `*_analysis.json` を検出
2. ファイル名から通貨ペアを抽出してグループ化
3. 各通貨ペアについて、時間足別にデータを整理
4. 時間足順序: `1d` → `4h` → `1h`（マクロからミクロへ）
5. メタデータ（ソースファイル、欠損時間足）を追加

**出力先**: `./summary_reports/`

**ファイル命名規則**: `{PAIR}_summary.json`

**JSONスキーマ (schema_version=2)**:
```json
{
  "pair": "USDJPY",
  "schema_version": 2,
  "generated_at": "2025-11-25T08:15:00+09:00",
  "timeframes": {
    "1d": {
      "interval": "1d",
      "period": "200d",
      "trend": "SIDEWAYS",
      "support_levels": [140.25, 142.80],
      "resistance_levels": [152.00, 151.50],
      "rsi": 54.12,
      "atr": 1.2456,
      "average_volatility": 1.1234,
      "data_timestamp": "2025-11-24T23:59:00+09:00"
    },
    "4h": {
      "interval": "4h",
      "period": "35d",
      "trend": "UP",
      "support_levels": [148.50, 149.10],
      "resistance_levels": [151.80, 151.45],
      "rsi": 58.22,
      "atr": 0.6834,
      "average_volatility": 0.5923,
      "data_timestamp": "2025-11-25T04:00:00+09:00"
    },
    "1h": {
      "interval": "1h",
      "period": "10d",
      "trend": "UP",
      "support_levels": [149.85, 149.92],
      "resistance_levels": [151.20, 151.05],
      "rsi": 62.45,
      "atr": 0.3245,
      "average_volatility": 0.2812,
      "data_timestamp": "2025-11-25T08:00:00+09:00"
    }
  },
  "metadata": {
    "source_files": [
      "USDJPY_1h_10d_analysis.json",
      "USDJPY_4h_35d_analysis.json",
      "USDJPY_1d_200d_analysis.json"
    ],
    "consolidation_version": "1.0.0",
    "total_timeframes": 3,
    "missing_timeframes": []
  }
}
```

**スキーマの特徴**:
- **schema_version=2**: 個別分析（v1）と明確に区別
- **timeframes辞書**: 時間足別にネストされた構造
- **data_timestamp**: 元の `generated_at` をリネーム（各時間足のデータ生成時刻）
- **generated_at**: 統合処理実行時刻（トップレベル）
- **metadata**: ソースファイル追跡、欠損検出

**タイムゾーン処理**:
- **入力**: 個別分析JSON（JST）
- **処理**: タイムスタンプをそのまま保持（`data_timestamp`としてリネーム）
- **出力**: `generated_at`フィールドはJST（`get_jst_now().isoformat()`）

**エラーハンドリング**:
| シナリオ | 処理 |
|---------|------|
| 時間足データ欠損 | 利用可能なデータで統合、`metadata.missing_timeframes`に記録 |
| スキーマバージョン不一致 | ファイルをスキップ、処理継続 |
| 破損JSON | エラーログ出力、処理継続 |
| 重複時間足 | 最新データ（タイムスタンプ比較）を使用 |

---

### ステップ4: アーティファクトアップロード

**実行条件**: `if: always()` - 前のステップが失敗しても実行

**アップロード内容**:
```yaml
path: |
  csv_data/**/*.csv          # 18個のCSVファイル
  reports/**/*.json          # 18個の個別分析JSON
  summary_reports/**/*.json  # 6個の統合サマリーJSON
```

**保存期間**: 7日間（`retention-days: 7`）

**アーティファクト名**: `ohlc-daily-{run_id}`

---

## タイムゾーン処理の一貫性

すべてのデータは**日本時間（JST）で統一**されています。

### タイムゾーン変換フロー

```
yfinance API（UTC）
  ↓ convert_dataframe_to_jst()
DataFrame（JST）
  ↓ CSV出力
CSVファイル（JST - "YYYY-MM-DD HH:MM:SS JST"）
  ↓ pd.to_datetime(..., utc=True)
分析処理（UTC aware）
  ↓ get_jst_now()
個別分析JSON（JST - ISO 8601形式）
  ↓ タイムスタンプ保持
統合サマリーJSON（JST - ISO 8601形式）
```

### タイムゾーン処理の検証

| ステップ | データソース | タイムゾーン | 変換処理 | 実装箇所 |
|---------|------------|------------|---------|---------|
| yfinance取得 | 市場データ | UTC | なし | yfinance API |
| DataFrame変換 | yfinance | UTC → **JST** | `convert_dataframe_to_jst()` | data_fetcher.py:77 |
| CSV保存 | DataFrame | **JST** | "YYYY-MM-DD HH:MM:SS JST" | data_fetcher.py:230 |
| CSV読み込み | ファイル | **JST** → UTC aware | `pd.to_datetime(..., utc=True)` | ohlc_aggregator.py:86 |
| 個別分析JSON | 分析結果 | **JST** | `get_jst_now()` | ohlc_aggregator.py:267 |
| 統合サマリーJSON | 統合結果 | **JST** | `get_jst_now()` | summary_consolidator.py:215 |

**保証事項**:
- ✅ すべてのタイムスタンプはJST（日本標準時）
- ✅ タイムゾーン情報は明示的に保持（ISO 8601形式 or "JST"サフィックス）
- ✅ タイムゾーンの混在や変換漏れなし

---

## 出力ファイル構造

### 最終出力（アーティファクト）

```
ohlc-daily-{run_id}/
├── csv_data/
│   ├── USDJPY_1h_10d.csv
│   ├── USDJPY_4h_35d.csv
│   ├── USDJPY_1d_200d.csv
│   ├── EURUSD_1h_10d.csv
│   ├── EURUSD_4h_35d.csv
│   ├── EURUSD_1d_200d.csv
│   ├── AUDJPY_1h_10d.csv
│   ├── AUDJPY_4h_35d.csv
│   ├── AUDJPY_1d_200d.csv
│   ├── AUDUSD_1h_10d.csv
│   ├── AUDUSD_4h_35d.csv
│   ├── AUDUSD_1d_200d.csv
│   ├── GBPJPY_1h_10d.csv
│   ├── GBPJPY_4h_35d.csv
│   ├── GBPJPY_1d_200d.csv
│   ├── XAUUSD_1h_10d.csv
│   ├── XAUUSD_4h_35d.csv
│   └── XAUUSD_1d_200d.csv
│
├── reports/
│   ├── USDJPY_1h_10d_analysis.json
│   ├── USDJPY_4h_35d_analysis.json
│   ├── USDJPY_1d_200d_analysis.json
│   ├── EURUSD_1h_10d_analysis.json
│   ├── EURUSD_4h_35d_analysis.json
│   ├── EURUSD_1d_200d_analysis.json
│   ├── AUDJPY_1h_10d_analysis.json
│   ├── AUDJPY_4h_35d_analysis.json
│   ├── AUDJPY_1d_200d_analysis.json
│   ├── AUDUSD_1h_10d_analysis.json
│   ├── AUDUSD_4h_35d_analysis.json
│   ├── AUDUSD_1d_200d_analysis.json
│   ├── GBPJPY_1h_10d_analysis.json
│   ├── GBPJPY_4h_35d_analysis.json
│   ├── GBPJPY_1d_200d_analysis.json
│   ├── XAUUSD_1h_10d_analysis.json
│   ├── XAUUSD_4h_35d_analysis.json
│   └── XAUUSD_1d_200d_analysis.json
│
└── summary_reports/
    ├── USDJPY_summary.json
    ├── EURUSD_summary.json
    ├── AUDJPY_summary.json
    ├── AUDUSD_summary.json
    ├── GBPJPY_summary.json
    └── XAUUSD_summary.json
```

**ファイル数統計**:
- CSVファイル: 18個（6ペア × 3時間足）
- 個別分析JSON: 18個（schema_version=1）
- 統合サマリーJSON: 6個（schema_version=2）

- 統合サマリーJSONダウンロードコマンド
 # 朝一でこれを実行するだけ
`gh run download --repo owner/FX-Kline --pattern "*summary*"`

より正確なパターン（推奨）
# summary_reportsディレクトリ内のJSONファイルのみ
`gh run download --repo owner/FX-Kline --pattern "summary_reports/*.json"`
# または、より柔軟に
`gh run download --repo owner/FX-Kline --pattern "**/summary*.json"`


---

## ローカル実行方法

### 前提条件

```bash
# 依存関係のインストール
uv sync --frozen
```

### ステップごとの手動実行

#### 1. CSVファイル取得

```bash
# ワークフローと同じ設定で実行
uv run python - <<'EOF'
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))

from fx_kline.core import OHLCRequest, export_to_csv, fetch_batch_ohlc_sync

pairs = "USDJPY EURUSD AUDJPY AUDUSD GBPJPY XAUUSD".split()
intervals = "1h 4h 1d".split()
period_map = {"1h": "10d", "4h": "35d", "1d": "200d"}

requests = [
    OHLCRequest(pair=p, interval=i, period=period_map[i])
    for p in pairs
    for i in intervals
]

response = fetch_batch_ohlc_sync(requests)

csv_dir = Path("csv_data")
csv_dir.mkdir(parents=True, exist_ok=True)

for ohlc in response.successful:
    out_path = csv_dir / f"{ohlc.pair}_{ohlc.interval}_{ohlc.period}.csv"
    out_path.write_text(export_to_csv(ohlc), encoding="utf-8")
    print(f"[OK] {out_path.name}")

for err in response.failed:
    print(f"[ERR] {err.pair}_{err.interval}_{err.period}: {err.error_message}")
EOF
```

#### 2. 個別分析実行

```bash
uv run python ohlc_aggregator.py --input-dir ./csv_data --output-dir ./reports --verbose
```

#### 3. 統合サマリー生成

```bash
uv run python consolidate_summaries.py --reports-dir ./reports --output-dir ./summary_reports --verbose
```

#### 特定通貨ペアのみ処理

```bash
# CSVファイル取得は全ペア実行後、統合時にフィルタ
uv run python consolidate_summaries.py \
  --reports-dir ./reports \
  --output-dir ./summary_reports \
  --pairs USDJPY EURUSD \
  --verbose
```

---

## トラブルシューティング

### よくある問題

#### 1. ワークフローが実行されない

**原因**: mainブランチ以外で実行しようとしている

**確認**:
```yaml
if: github.ref == 'refs/heads/main'
```

**解決策**: mainブランチにマージするか、この条件を削除

#### 2. CSVファイル取得に失敗

**原因**: yfinance APIの一時的なエラーまたはレート制限

**確認**: ワークフローログで `[ERR]` メッセージを確認

**解決策**:
- 手動で再実行（workflow_dispatch）
- 期間を短縮して再試行
- yfinanceのステータスを確認

#### 3. 個別分析でエラー

**原因**: CSVファイルが空、または必須カラムが欠損

**確認**:
```bash
# CSVファイルの内容確認
head csv_data/USDJPY_1h_10d.csv
```

**解決策**:
- CSVファイルに `Datetime,Open,High,Low,Close,Volume` カラムがあるか確認
- CSVを再生成

#### 4. 統合サマリーで一部時間足が欠損

**原因**: 個別分析が失敗した時間足がある

**確認**:
```json
// summary_reports/USDJPY_summary.json
{
  "metadata": {
    "missing_timeframes": ["1h"]  // ← 欠損時間足
  }
}
```

**解決策**:
- 該当時間足の個別分析を再実行
- 統合サマリーは部分データでも生成される（graceful degradation）

#### 5. タイムゾーンがずれている

**確認ポイント**:
```bash
# CSVファイルのタイムゾーン確認
head -n 3 csv_data/USDJPY_1h_10d.csv
# Datetime列に "JST" が含まれているか確認

# JSONファイルのタイムゾーン確認
cat reports/USDJPY_1h_10d_analysis.json | grep generated_at
# "+09:00" (JSTオフセット) が含まれているか確認
```

**期待される出力**:
```
Datetime,Open,High,Low,Close,Volume
2025-11-25 08:00:00 JST,150.12,150.45,149.85,150.32,12345
```

---

## メンテナンス

### 通貨ペアの追加

1. `.github/workflows/daily_ohlc_analysis.yml` の `PAIRS` 環境変数を更新:
```yaml
PAIRS: "USDJPY EURUSD AUDJPY AUDUSD GBPJPY XAUUSD GBPUSD"  # GBPUSD追加
```

2. `src/fx_kline/core/validators.py` で通貨ペアがサポートされているか確認

3. テスト実行して動作確認

### 時間足の変更

1. `.github/workflows/daily_ohlc_analysis.yml` の `INTERVALS` と `PERIOD_MAP` を更新:
```yaml
INTERVALS: "1h 4h 1d 1wk"  # 1wk追加
PERIOD_MAP: "1h:10d 4h:35d 1d:200d 1wk:52w"  # 1wk追加
```

2. `src/fx_kline/core/summary_consolidator.py` の `_EXPECTED_TIMEFRAMES` を更新:
```python
_EXPECTED_TIMEFRAMES = {"1h", "4h", "1d", "1wk"}  # 1wk追加
```

3. `_TIMEFRAME_ORDER` を更新（必要に応じて）:
```python
_TIMEFRAME_ORDER = ["1wk", "1d", "4h", "1h"]  # 1wk追加
```

### スケジュールの変更

実行時刻を変更する場合、**UTC時刻で指定**する必要があります。

**例**: JST 09:00に変更したい場合
- JST 09:00 = UTC 00:00（前日）
- 平日のみ: `cron: "0 0 * * 0-4"` （UTC日曜〜木曜 = JST月曜〜金曜）

---

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `daily_ohlc_analysis.yml` | ワークフロー定義 |
| `ohlc_aggregator.py` | 個別分析スクリプト |
| `consolidate_summaries.py` | 統合サマリースクリプト |
| `src/fx_kline/core/data_fetcher.py` | データ取得・JST変換ロジック |
| `src/fx_kline/core/ohlc_aggregator.py` | 分析ロジック本体 |
| `src/fx_kline/core/summary_consolidator.py` | 統合ロジック本体 |
| `src/fx_kline/core/timezone_utils.py` | タイムゾーン変換ユーティリティ |
| `src/fx_kline/core/validators.py` | 通貨ペア・時間足の設定 |

---

## 履歴

| 日付 | 変更内容 |
|------|---------|
| 2025-11-25 | 初版作成：統合サマリー機能追加、タイムゾーン処理ドキュメント化 |
