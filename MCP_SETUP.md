# FX-Kline MCP サーバーセットアップガイド

FX-KlineをModel Context Protocol (MCP)サーバーとして使用することで、Claude DesktopやClineなどのAIツールから直接FXデータを取得できます。

## MCPサーバー化の利点

### 🎯 主な利点

1. **AI駆動の市場分析**
   - データ取得とAI分析を一つのワークフローで実現
   - 自然言語でデータリクエスト
   - トレンド分析、相関分析などを即座に実行

2. **自動化ワークフロー**
   - 複数ツールとの連携が容易
   - スクリプトからのプログラマティックアクセス
   - データ取得→分析→レポート生成を自動化

3. **効率的な開発**
   - コマンド入力不要
   - GUIの起動不要
   - 対話的なデータ探索

## 前提条件

- Python 3.10以上
- uv（パッケージマネージャー）
- Claude Desktop または MCP対応クライアント

## インストール手順

### 1. 依存関係のインストール

MCPサーバーには追加の依存関係が必要です：

```bash
# MCPサーバー用の依存関係を含めてインストール
uv sync --extra mcp
```

### 2. Claude Desktop設定

Claude Desktopの設定ファイルに以下を追加します。

**macOS/Linux**:
```bash
# 設定ファイルの場所
~/.config/claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

**設定内容**:

```json
{
  "mcpServers": {
    "fx-kline": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/path/to/FX-Kline/run_mcp_server.py"
      ],
      "description": "FX OHLC data fetching tool"
    }
  }
}
```

**重要**: `/path/to/FX-Kline/` を実際のプロジェクトパスに置き換えてください。

### 3. サーバーの起動確認

Claude Desktopを再起動すると、FX-Klineサーバーが自動的に起動します。

Claude Desktopのツール一覧で以下が表示されることを確認：
- `fetch_ohlc` - 単一データ取得
- `fetch_ohlc_batch` - バッチ取得
- `list_available_pairs` - 通貨ペア一覧
- `list_available_timeframes` - 時間足一覧

## 使用方法

### 基本的な使い方

Claude Desktopで自然言語でリクエストできます：

```
「ドル円の過去30日の日足データを取得して」
```

```
「ユーロドルとポンド円の1時間足を過去5日分取得して、相関を分析して」
```

```
「金（XAUUSD）の過去3ヶ月の日足データを取得して、トレンドを教えて」
```

### 利用可能なツール

#### 1. fetch_ohlc

単一の通貨ペアのOHLCデータを取得。

**パラメータ**:
- `pair` (必須): 通貨ペアコード (例: "USDJPY", "EURUSD", "XAUUSD")
- `interval` (オプション): 時間足 (デフォルト: "1d")
  - 利用可能: "1m", "5m", "15m", "1h", "4h", "1d"
- `period` (オプション): 取得期間 (デフォルト: "30d")
  - 形式: "1d", "5d", "30d", "3mo", "1y"
- `exclude_weekends` (オプション): 週末除外 (デフォルト: true)

**使用例**:
```
「fetch_ohlcツールを使って、USDJPYの1時間足を過去5日分取得して」
```

#### 2. fetch_ohlc_batch

複数の通貨ペア・時間足を並列取得。効率的なバッチ処理。

**パラメータ**:
- `requests` (必須): リクエストの配列
  - 各リクエスト: `{"pair": "USDJPY", "interval": "1h", "period": "5d"}`
- `exclude_weekends` (オプション): 週末除外 (デフォルト: true)

**使用例**:
```
「fetch_ohlc_batchで以下のデータを取得して：
- USDJPY 日足 30日分
- EURUSD 1時間足 5日分
- XAUUSD 15分足 1日分」
```

#### 3. list_available_pairs

利用可能な通貨ペア一覧を取得。

**パラメータ**:
- `preset_only` (オプション): プリセットのみ返す (デフォルト: false)

**使用例**:
```
「利用可能な通貨ペアを全て教えて」
```

#### 4. list_available_timeframes

利用可能な時間足一覧を取得。

**パラメータ**:
- `preset_only` (オプション): プリセットのみ返す (デフォルト: false)

**使用例**:
```
「対応している時間足を教えて」
```

## 実践的なユースケース

### 1. トレンド分析

```
「ドル円の過去30日の日足データを取得して、移動平均線でトレンドを分析して」
```

Claudeが以下を自動実行：
1. fetch_ohlcでデータ取得
2. 移動平均線を計算
3. トレンドを分析・解釈
4. レポート生成

### 2. 相関分析

```
「USDJPY、EURJPY、GBPJPYの過去30日の日足を取得して、相関を分析して」
```

Claude が並列取得して相関係数を計算。

### 3. 複数時間足分析

```
「ドル円の日足・4時間足・1時間足を過去7日分取得して、マルチタイムフレーム分析して」
```

異なる時間足での動きを総合的に分析。

### 4. ボラティリティ分析

```
「主要通貨ペア（USDJPY, EURUSD, GBPUSD）の過去30日のボラティリティを比較して」
```

複数ペアのデータを取得して統計分析。

## データフォーマット

### 成功レスポンス

```json
{
  "success": true,
  "data": {
    "pair": "USDJPY",
    "interval": "1h",
    "period": "5d",
    "data_count": 120,
    "timestamp_jst": "2025-11-07 10:30:00 JST",
    "columns": ["Datetime", "Open", "High", "Low", "Close", "Volume"],
    "rows": [
      {
        "Datetime": "2025-11-02 09:00:00 JST",
        "Open": 152.72,
        "High": 152.78,
        "Low": 152.32,
        "Close": 152.54,
        "Volume": 1000
      },
      ...
    ]
  }
}
```

### エラーレスポンス

```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid currency pair: INVALID",
    "pair": "INVALID",
    "interval": "1h",
    "period": "5d"
  }
}
```

## トラブルシューティング

### サーバーが起動しない

**確認事項**:
1. 依存関係がインストールされているか
   ```bash
   uv sync --extra mcp
   ```

2. 設定ファイルのパスが正しいか
   ```bash
   # 絶対パスを使用
   pwd  # 現在のディレクトリを確認
   ```

3. Claude Desktopを再起動

### ツールが表示されない

**解決方法**:
1. Claude Desktopを完全に終了
2. 設定ファイルを再確認
3. Claude Desktopを再起動
4. 数秒待機してツールリストを確認

### データ取得エラー

**一般的な原因**:
- インターネット接続の問題
- 不正な通貨ペアコード（大文字で指定）
- サポートされていない時間足
- yfinanceのサービス問題

**確認方法**:
```bash
# 手動でテスト
cd /path/to/FX-Kline
uv run python test_fetch.py
```

## Streamlit UIとの併用

MCPサーバーとStreamlit UIは**完全に独立**しており、両方を同時に使用できます：

- **Streamlit UI**: 視覚的なデータ確認、手動エクスポート
- **MCPサーバー**: AI分析、自動化ワークフロー

### Streamlit UIの起動

```bash
uv run streamlit run src/fx_kline/ui/streamlit_app.py
```

ブラウザで http://localhost:8501 が開きます。

## 開発者向け情報

### スタンドアロンテスト

MCPサーバーを直接テストする場合：

```bash
uv run python run_mcp_server.py
```

標準入出力でMCPプロトコルと通信します。

### カスタムMCPクライアント

Python/Node.jsから直接利用する場合は、MCP SDKを使用してクライアントを実装できます。

## 次のステップ

1. Claude Desktopでツールを試す
2. 自然言語でデータ取得
3. AIと組み合わせた分析ワークフローを構築
4. 他のMCPツールと連携

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください：
- 設定の問題
- データ取得エラー
- 機能リクエスト

## 関連リンク

- [MCP公式ドキュメント](https://modelcontextprotocol.io/)
- [Claude Desktop](https://claude.ai/desktop)
- [FX-Kline README](./README.md)
