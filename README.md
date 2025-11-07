# FX-Kline

FX OHLC(4本足)データ取得ツール。複数の通貨ペア・時間足を並列で取得し、CSV/JSONでダウンロードまたはクリップボードにコピーできるアプリケーション。

## 特徴

- 並列データ取得: 複数の通貨ペア・時間足を同時に取得(asyncio対応)
- 営業日フィルタリング: 土日を自動除外、過去N営業日分のデータを取得
- JST自動変換: UTC→JST(日本時間)に自動変換、米国夏時間・冬時間対応
- 複数フォーマット対応: CSV、JSON、クリップボードコピー(カンマ区切り)
- 使いやすいUI: Streamlitによる直感的なWebインターフェース
- MCPサーバー対応: Claude Desktop/Cline統合に向けた設計
- 実時間取得: yfinanceを使用した最新データ取得

## 対応通貨ペア

| 通貨ペア | コード |
|---------|--------|
| ドル円 | USDJPY |
| ユーロドル | EURUSD |
| ポンドドル | GBPUSD |
| オーストラリアドル | AUDUSD |
| ユーロ円 | EURJPY |
| ポンド円 | GBPJPY |
| オーストラリアドル円 | AUDJPY |
| 金(ゴールド) | XAUUSD |

## 対応時間足

- 5分足(5m)
- 15分足(15m)
- 1時間足(1h)
- 日足(1d)

※ 今後拡張可能

## クイックスタート

### 前提条件

- Python 3.10以上
- uv(パッケージマネージャー)

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd FX-Kline

# 依存関係をインストール
uv sync
```

### Streamlit UIの起動

```bash
# 方法1: streamlit コマンド直接実行
uv run streamlit run src/fx_kline/ui/streamlit_app.py

# 方法2: main.py経由で実行
python main.py
```

ブラウザで自動的に http://localhost:8501 が開きます。

### 使用方法

#### UI経由での使用

1. サイドバーで設定
   - 通貨ペアを選択(マルチセレクト対応)
   - 時間足を選択(複数選択可)
   - 各通貨ペアの取得期間を日数で指定

2. データ取得
   - 「Fetch Data」ボタンをクリック
   - 複数リクエストが並列で実行される

3. データのエクスポート
   - CSVダウンロード: ローカルPC保存
   - JSONダウンロード: JSON形式で保存
   - クリップボードコピー: カンマ区切り形式で表示(コピー可)

#### Pythonコードからの直接使用

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fx_kline.core import OHLCRequest, fetch_batch_ohlc_sync

# 複数リクエストを準備
requests = [
    OHLCRequest(pair="USDJPY", interval="1d", period="30d"),
    OHLCRequest(pair="EURUSD", interval="1h", period="5d"),
    OHLCRequest(pair="XAUUSD", interval="15m", period="1d"),
]

# 並列で取得
response = fetch_batch_ohlc_sync(requests)

# 成功したデータを処理
print(f"成功: {response.total_succeeded} / {response.total_requested}")

for ohlc in response.successful:
    print(f"\n{ohlc.pair} ({ohlc.interval} / {ohlc.period})")
    print(f"データ数: {ohlc.data_count}")
    print(f"期間: {ohlc.rows[0]['Datetime']} ~ {ohlc.rows[-1]['Datetime']}")

    # 最初の3行を表示
    for row in ohlc.rows[:3]:
        print(f"  {row['Datetime']}: O={row['Open']:.4f} H={row['High']:.4f} L={row['Low']:.4f} C={row['Close']:.4f}")

# エラーハンドリング
for err in response.failed:
    print(f"\n[Error] {err.pair} ({err.interval} / {err.period})")
    print(f"  エラー: {err.error_type}")
    print(f"  詳細: {err.error_message}")
```

## プロジェクト構成

```
fx-kline/
├── src/fx_kline/
│   ├── core/                      # コアビジネスロジック
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic データモデル
│   │   ├── validators.py          # 入力検証・定数定義
│   │   ├── timezone_utils.py      # UTC~JST変換(DST対応)
│   │   ├── business_days.py       # 営業日フィルタリング
│   │   └── data_fetcher.py        # yfinance並列取得・エクスポート
│   ├── mcp/                       # MCPサーバー実装
│   │   ├── __init__.py
│   │   ├── server.py              # MCPサーバーメイン
│   │   └── tools.py               # MCPツール定義
│   └── ui/
│       ├── __init__.py
│       └── streamlit_app.py       # Streamlit Webアプリ
├── pyproject.toml                 # プロジェクト設定・依存関係
├── main.py                        # Streamlit起動スクリプト
├── run_mcp_server.py              # MCPサーバー起動スクリプト
├── claude_desktop_config.example.json  # Claude Desktop設定例
├── test_fetch.py                  # テストスクリプト
├── debug_fetch.py                 # デバッグスクリプト
├── README.md                      # このファイル
└── MCP_SETUP.md                   # MCPセットアップガイド
```

## コア API リファレンス

### OHLCRequest

単一のデータ取得リクエストを定義

```python
from fx_kline.core import OHLCRequest

request = OHLCRequest(
    pair="USDJPY",      # 通貨ペアコード
    interval="1h",      # 時間足
    period="30d"        # 取得期間
)
```

### 並列データ取得

```python
from fx_kline.core import fetch_batch_ohlc_sync, OHLCRequest

requests = [
    OHLCRequest(pair="USDJPY", interval="1d", period="30d"),
    OHLCRequest(pair="EURUSD", interval="1h", period="5d"),
]

response = fetch_batch_ohlc_sync(requests, exclude_weekends=True)

# レスポンス構造
response.successful    # OHLCDataのリスト
response.failed        # FetchErrorのリスト
response.total_requested
response.total_succeeded
response.total_failed
response.summary       # 成功率などのサマリー
```

### データエクスポート

```python
from fx_kline.core import export_to_csv, export_to_json, export_to_csv_string

# CSV形式(ファイル保存用)
csv_data = export_to_csv(ohlc_data)
with open("data.csv", "w") as f:
    f.write(csv_data)

# JSON形式(ファイル保存用)
json_data = export_to_json(ohlc_data)
with open("data.json", "w") as f:
    f.write(json_data)

# クリップボード用(カンマ区切り)
clipboard_data = export_to_csv_string(ohlc_data, include_header=True)
print(clipboard_data)  # コピーして使用
```

### タイムゾーン処理

```python
from fx_kline.core import (
    utc_to_jst,
    get_jst_now,
    is_us_dst_active,
    get_us_market_hours_in_jst
)

# 現在時刻をJSTで取得
now_jst = get_jst_now()

# 米国市場の営業時間をJSTで確認
market_hours = get_us_market_hours_in_jst()
print(f"NY市場(JST): {market_hours['open']} ~ {market_hours['close']}")

# DST判定
if is_us_dst_active():
    print("現在は米国夏時間(EDT)です")
else:
    print("現在は米国冬時間(EST)です")
```

### 営業日フィルタリング

```python
from fx_kline.core import (
    filter_business_days,
    get_business_days_back,
    count_business_days
)

# 過去N営業日を取得
target_date = get_business_days_back(30)  # 過去30営業日前

# DataFrameから土日を除外
df_weekdays = filter_business_days(df)

# 日付範囲の営業日数をカウント
business_day_count = count_business_days(start_date, end_date)
```

## データフォーマット

### 返却されるOHLCデータの構造

```python
{
    "pair": "USDJPY",
    "interval": "1h",
    "period": "30d",
    "data_count": 150,
    "rows": [
        {
            "Datetime": "2025-10-30 09:00:00 JST",
            "Open": 152.72,
            "High": 152.78,
            "Low": 152.32,
            "Close": 152.54,
            "Volume": 1000
        },
        # ... 以下、data_count分のデータ
    ]
}
```

## 並列実行の例

複数の通貨ペア・時間足を一度に取得：

```python
requests = [
    # ドル円
    OHLCRequest(pair="USDJPY", interval="1d", period="30d"),
    OHLCRequest(pair="USDJPY", interval="1h", period="5d"),
    OHLCRequest(pair="USDJPY", interval="15m", period="1d"),

    # ユーロドル
    OHLCRequest(pair="EURUSD", interval="1d", period="30d"),
    OHLCRequest(pair="EURUSD", interval="1h", period="5d"),

    # 金
    OHLCRequest(pair="XAUUSD", interval="1h", period="5d"),
]

# 6つのリクエストが同時に実行される
response = fetch_batch_ohlc_sync(requests)

print(f"取得完了: {response.total_succeeded}/{response.total_requested}")
```

## エラーハンドリング

データ取得失敗時の情報：

```python
for error in response.failed:
    print(f"通貨ペア: {error.pair}")
    print(f"時間足: {error.interval}")
    print(f"期間: {error.period}")
    print(f"エラータイプ: {error.error_type}")
    print(f"詳細メッセージ: {error.error_message}")
    print(f"タイムスタンプ: {error.timestamp}")
```

### よくあるエラー

| エラータイプ | 原因 | 対策 |
|-----------|------|------|
| NoDataAvailable | 取得期間にデータなし | 取得期間を延長 |
| AllWeekendData | 取得期間が全て土日 | 取得期間を延長 |
| ValidationError | 不正な通貨ペア/時間足 | サポートされているペアを確認 |
| TypeError | データ型変換エラー | yfinanceのバージョン確認 |

## MCPサーバー（実装済み）✨

FX-KlineはModel Context Protocol (MCP)サーバーとして利用可能です。Claude DesktopやClineなどのAIツールから直接FXデータを取得できます。

### 実装済み機能

- ✅ `fetch_ohlc`: 単一通貨ペアのデータ取得
- ✅ `fetch_ohlc_batch`: 複数リクエストの並列バッチ取得
- ✅ `list_available_pairs`: 利用可能な通貨ペア一覧
- ✅ `list_available_timeframes`: 利用可能な時間足一覧
- ✅ Claude Desktop統合設定例

### MCPサーバーの利点

- 🤖 **AI駆動の分析**: Claude がデータ取得→分析→レポート生成を自動実行
- 💬 **自然言語インターフェース**: 「ドル円の過去30日のデータを分析して」で完結
- 🔗 **ツール連携**: 他のMCPツールと組み合わせた高度なワークフロー
- ⚡ **効率化**: GUIやコード不要、対話的なデータ探索

### クイックスタート

```bash
# MCP用依存関係をインストール
uv sync --extra mcp

# Claude Desktopの設定ファイルに追加
# ~/.config/claude/claude_desktop_config.json (macOS/Linux)
# %APPDATA%\Claude\claude_desktop_config.json (Windows)
```

**詳細なセットアップ手順は [MCP_SETUP.md](./MCP_SETUP.md) を参照してください。**

### 使用例

Claude Desktopで以下のように自然言語でリクエスト：

```
「ドル円の過去30日の日足データを取得して、トレンドを分析して」
```

```
「USDJPY、EURUSD、GBPUSDの1時間足を過去5日分取得して、相関を分析して」
```

### StreamlitとMCPの併用

両方のインターフェースが利用可能です：

| インターフェース | 用途 |
|--------------|------|
| **Streamlit UI** | 手動データ確認、視覚化、エクスポート |
| **MCPサーバー** | AI分析、自動化ワークフロー、ツール連携 |

## 開発・テスト

### テストスクリプトの実行

```bash
# シンプルなデータ取得テスト
uv run python test_fetch.py

# yfinanceのデータ構造デバッグ
uv run python debug_fetch.py
```

### 依存関係の更新

```bash
# 依存関係をリセット
uv sync --upgrade
```

## 依存関係

### メイン依存関係
- yfinance >= 0.2.66: 市場データ取得
- pandas >= 2.0.0: データ操作
- pydantic >= 2.0.0: データ検証
- python-dateutil >= 2.8.0: 日付計算
- streamlit >= 1.28.0: Web UI
- pytz >= 2023.3: タイムゾーン処理

### オプション依存関係
- mcp >= 0.9.0: MCPサーバー実装用

### 開発用依存関係
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0
- black >= 23.0.0
- ruff >= 0.1.0

## 環境設定

### Streamlit設定ファイル(~/.streamlit/config.toml)

```toml
[browser]
gatherUsageStats = false

[logger]
level = "error"
```

## トラブルシューティング

### Streamlitが起動しない

```bash
# Streamlitを完全にリセット
rm -rf ~/.streamlit
uv sync --upgrade
uv run streamlit run src/fx_kline/ui/streamlit_app.py
```

### データが取得できない

1. インターネット接続を確認
2. yfinanceのバージョンを確認: uv pip list | grep yfinance
3. 通貨ペアが正しいか確認(大文字で指定)
4. debug_fetch.py を実行してデータ構造を確認

### タイムゾーンが正しくない

- システムのタイムゾーン設定を確認
- UTC~JST変換は自動的に行われます
- get_jst_now() で現在のJST時刻を確認可能

## ライセンス

MIT License

## 貢献

プルリクエストやイシュー報告をお待ちしています。

## サポート

問題が発生した場合は、GitHubのIssuesセクションで報告してください。
