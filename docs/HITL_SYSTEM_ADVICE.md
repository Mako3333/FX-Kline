# FX HITL Trading System - Professional Fund Manager's Advice

## 📋 エグゼクティブサマリー

このドキュメントは、FX専門ファンドマネージャーの視点から、Human-in-the-Loop (HITL) トレーディングシステムに対する包括的なアドバイスをまとめたものです。

### システムの本質的理解

- **L4がコア**: あなた（mako）のトレード手法・ルール・環境認識を学習したAIとの協働が本質
- **L3はベンチマーク**: 素のAI予測と比較することで、L4の付加価値を定量化
- **週2-5回の厳選トレード**: 高頻度取引ではなく、確信度の高いトレードのみ実行
- **二軸収益モデル**: トレード収益 + プロセス透明化によるコンテンツ収益

---

## 🎯 重要度：高（実装必須）

### 1. リスク管理フレームワーク

現在のシステムには「どこでエントリーすべきか」の分析はありますが、**「いくら賭けるべきか」の仕組みが不足**しています。

#### 1.1 ポジションサイジング

```python
@dataclass
class RiskManagement:
    """リスク管理の中核クラス"""
    account_balance: float
    risk_per_trade_pct: float = 0.02  # 2%
    max_leverage: float = 25.0

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        atr: float
    ) -> float:
        """ATRとストップロスからポジションサイズを計算

        Args:
            entry_price: エントリー価格
            stop_loss: ストップロス価格
            atr: Average True Range

        Returns:
            推奨ポジションサイズ（lots）
        """
        # リスク許容額
        risk_amount = self.account_balance * self.risk_per_trade_pct

        # 価格リスク（pips換算）
        price_risk = abs(entry_price - stop_loss)

        # ポジションサイズ計算
        position_size = risk_amount / price_risk

        # レバレッジ制限を適用
        max_position = (self.account_balance * self.max_leverage) / entry_price

        return min(position_size, max_position)
```

#### 1.2 損切り・利確ロジック

**ストップロス設定原則**:
- ATRベースの動的ストップ: `stop_distance = ATR × 2`
- 直近サポート/レジスタンスの外側に設置
- 一度設定したら動かさない（例外: 建値移動のみ許可）

**利確戦略**:
- 初期目標: リスクリワード比 2:1 以上を必須
- トレーリングストップ: `ATR × 2` で追従
- 部分利確: 50%を目標到達時、残り50%をトレール

#### 1.3 日次・週次リスク上限

```python
@dataclass
class RiskGuard:
    """複数トレードにわたるリスク管理"""
    account_balance: float
    max_risk_per_trade_pct: float = 0.02  # 2%
    max_daily_loss_pct: float = 0.04      # 4%（2連敗で停止）
    max_weekly_loss_pct: float = 0.08     # 8%

    def check_trade_allowed(
        self,
        proposed_trade: Trade,
        today_loss: float,
        week_loss: float
    ) -> Tuple[bool, str]:
        """トレード実行可否を判定

        Returns:
            (許可/不許可, 理由)
        """
        # 今日の損失上限チェック
        if today_loss / self.account_balance > self.max_daily_loss_pct:
            return False, "今日の損失上限到達。明日まで待機"

        # 週次損失上限チェック
        if week_loss / self.account_balance > self.max_weekly_loss_pct:
            return False, "週次損失上限到達。来週まで待機"

        # 提案トレードのリスクチェック
        trade_risk = abs(proposed_trade.entry - proposed_trade.stop_loss)
        position_size = (self.account_balance * self.max_risk_per_trade_pct) / trade_risk

        if position_size > proposed_trade.position_size * 1.5:
            return False, "ポジションサイズが過大"

        return True, "OK"
```

---

### 2. トレードコストの考慮

FXでは**スプレッドコスト**が収益性に大きく影響します。

#### 2.1 コスト計算

```python
@dataclass
class TradeCost:
    """トレードコストの管理"""
    pair: str
    typical_spread_pips: float  # USDJPY=0.2, EURUSD=0.3など
    commission_per_lot: float = 0.0  # ブローカー手数料

    def calculate_breakeven_pips(self, position_size: float) -> float:
        """損益分岐点（pips）を計算

        スプレッドは往復分（エントリー＋エグジット）を考慮
        """
        return self.typical_spread_pips * 2

    def calculate_net_profit(
        self,
        gross_pips: float,
        position_size: float
    ) -> float:
        """スプレッドと手数料を差し引いた純利益"""
        spread_cost = self.typical_spread_pips * 2 * position_size
        commission_cost = self.commission_per_lot * position_size
        net_pips = gross_pips - spread_cost
        net_profit = (net_pips * position_size) - commission_cost
        return net_profit
```

#### 2.2 時間帯別スプレッド考慮

| 時間帯（JST） | 市場 | スプレッド | 推奨度 |
|---------------|------|------------|--------|
| 9:00-17:00 | 東京 | 標準 | ⭐⭐⭐ |
| 17:00-01:00 | ロンドン | 最小 | ⭐⭐⭐⭐⭐ |
| 22:00-06:00 | ニューヨーク | 標準 | ⭐⭐⭐⭐ |
| 06:00-09:00 | 閑散時間 | 拡大 | ❌ 避ける |

**実装推奨**:
- 時間帯別のスプレッドデータベース構築
- 流動性が低い時間帯（東京・ロンドン・NY休場時）は自動警告
- バックテストにスプレッドコストを必ず織り込む

---

### 3. 相関リスク管理

複数ペアを同時に取引する場合、**相関リスク**が発生します。

#### 3.1 問題の例

**危険なポジション構成**:
```
USDJPY  LONG  1.0 lot
EURJPY  LONG  1.0 lot
GBPJPY  LONG  1.0 lot
```

→ 円高が進むと3つ同時に損失（分散になっていない）

#### 3.2 相関リスクチェック

```python
def check_correlation_risk(
    existing_positions: List[Position],
    new_position: Position,
    correlation_matrix: pd.DataFrame,
    max_correlation_exposure: float = 0.7
) -> Tuple[bool, str]:
    """新ポジションが既存ポジションと高相関でないかチェック

    Args:
        existing_positions: 既存のオープンポジション
        new_position: 新規エントリー候補
        correlation_matrix: 通貨ペア間の相関係数マトリクス
        max_correlation_exposure: 許容する相関係数の上限

    Returns:
        (許可/不許可, 理由)
    """
    for pos in existing_positions:
        corr = correlation_matrix.loc[pos.pair, new_position.pair]

        # 同方向かつ高相関の場合
        if pos.direction == new_position.direction and abs(corr) > max_correlation_exposure:
            return False, f"{pos.pair}と相関{corr:.2f}で過度に集中"

        # 逆方向だが高相関（ヘッジ効果）の場合は許可
        if pos.direction != new_position.direction and abs(corr) > max_correlation_exposure:
            return True, f"{pos.pair}とのヘッジポジション"

    return True, "相関リスク許容範囲内"
```

#### 3.3 相関マトリクス例

|       | USDJPY | EURJPY | GBPJPY | EURUSD |
|-------|--------|--------|--------|--------|
| USDJPY | 1.00  | 0.85   | 0.78   | -0.65  |
| EURJPY | 0.85  | 1.00   | 0.92   | 0.20   |
| GBPJPY | 0.78  | 0.92   | 1.00   | 0.15   |
| EURUSD | -0.65 | 0.20   | 0.15   | 1.00   |

**推奨ルール**:
- 相関係数 > 0.7 の通貨ペアは同時に2つまで
- 合計エクスポージャー: 口座の6%以内（3ペア × 2%）

---

## 📊 重要度：中（運用品質向上）

### 4. パフォーマンストラッキング

プロのファンドでは以下の指標を**毎日**モニタリングします。

#### 4.1 重要KPI

```python
@dataclass
class PerformanceMetrics:
    """パフォーマンス評価指標"""
    total_trades: int
    win_rate: float  # 勝率（目標：55%以上）
    profit_factor: float  # 総利益/総損失（目標：1.5以上）
    sharpe_ratio: float  # リスク調整後リターン（目標：1.0以上）
    max_drawdown_pct: float  # 最大ドローダウン（許容：-20%以内）
    avg_win_pips: float
    avg_loss_pips: float
    expectancy: float  # 1トレードあたりの期待値（pips）

    # R倍率（リスクリワード比の実現値）
    avg_r_multiple: float  # 目標：1.5以上

    def is_system_healthy(self) -> bool:
        """システムが正常に機能しているか判定

        3つの基準すべてを満たす必要あり
        """
        return (
            self.win_rate >= 0.50 and
            self.profit_factor >= 1.3 and
            self.max_drawdown_pct > -25.0
        )

    def calculate_expectancy(self) -> float:
        """期待値の計算

        期待値 = (勝率 × 平均利益) - (負率 × 平均損失)
        """
        win_amount = self.win_rate * self.avg_win_pips
        loss_amount = (1 - self.win_rate) * abs(self.avg_loss_pips)
        return win_amount - loss_amount
```

#### 4.2 モニタリングダッシュボード

**日次チェック項目**:
- [ ] 今日の損益（pips / %）
- [ ] 週次累計損益
- [ ] 月次累計損益
- [ ] 現在のドローダウン深度
- [ ] 連勝/連敗カウンター

**週次レビュー項目**:
- [ ] 勝率の推移
- [ ] プロフィットファクターの推移
- [ ] ベストトレード/ワーストトレード分析
- [ ] ルール違反の有無
- [ ] L3 vs L4 のパフォーマンス比較

---

### 5. 市場環境フィルター

すべての相場環境でトレードすべきではありません。

#### 5.1 市場レジーム判定

```python
def check_market_regime(df: pd.DataFrame, atr: float) -> str:
    """相場環境を判定

    Args:
        df: OHLC DataFrame
        atr: Average True Range

    Returns:
        "TRENDING" | "RANGING" | "CHOPPY"
    """
    # ADX（Average Directional Index）計算
    adx = compute_adx(df, period=14)

    # ATRの歴史的中央値
    historical_atr = df['atr'].rolling(window=60).median().iloc[-1]

    # 判定ロジック
    if adx > 25:
        return "TRENDING"  # トレンドフォロー戦略向き
    elif adx < 20 and atr < historical_atr:
        return "RANGING"   # 逆張り戦略向き
    else:
        return "CHOPPY"    # トレード回避推奨
```

#### 5.2 戦略の切り替え

| 市場レジーム | 推奨戦略 | 避けるべき戦略 |
|--------------|----------|----------------|
| TRENDING | トレンドフォロー、ブレイクアウト | 逆張り、サポレジ反発 |
| RANGING | サポレジ反発、逆張り | トレンドフォロー |
| CHOPPY | **トレード見送り** | すべて |

**実装推奨**:
- L2レポートに市場レジームを自動記載
- CHOPPY判定時は L4 で自動的に WAIT 推奨
- レジーム別の勝率を追跡（L5振り返りで活用）

---

### 6. 時間帯別フィルター

FX市場は24時間ですが、**時間帯によってボラティリティと流動性が大きく異なります**。

#### 6.1 市場セッション定義

```python
MARKET_SESSIONS = {
    "tokyo": {
        "hours": (9, 17),      # JST 9:00-17:00
        "volatility": "LOW",
        "pairs": ["USDJPY", "AUDJPY"]
    },
    "london": {
        "hours": (17, 1),      # JST 17:00-翌1:00（冬時間）
        "volatility": "HIGH",
        "pairs": ["EURUSD", "GBPUSD", "EURJPY", "GBPJPY"]
    },
    "newyork": {
        "hours": (22, 6),      # JST 22:00-翌6:00（冬時間）
        "volatility": "HIGH",
        "pairs": ["USDJPY", "EURUSD"]
    },
    "overlap_london_ny": {
        "hours": (22, 1),      # JST 22:00-翌1:00
        "volatility": "VERY_HIGH",
        "pairs": ["EURUSD", "GBPUSD"]  # 最も活発
    }
}

def get_optimal_trading_hours(pair: str) -> List[Tuple[int, int]]:
    """ペアごとの最適取引時間

    Args:
        pair: 通貨ペア（例: "USDJPY"）

    Returns:
        最適な時間帯のリスト
    """
    if "JPY" in pair:
        return [
            MARKET_SESSIONS["tokyo"]["hours"],
            MARKET_SESSIONS["london"]["hours"]
        ]
    elif "EUR" in pair or "GBP" in pair:
        return [
            MARKET_SESSIONS["london"]["hours"],
            MARKET_SESSIONS["newyork"]["hours"]
        ]
    else:
        return [MARKET_SESSIONS["london"]["hours"]]
```

#### 6.2 避けるべき時間帯

**絶対に避ける**:
- 週末オープン直後（月曜朝7:00-9:00 JST）: 窓開けリスク
- 週末クローズ直前（土曜朝6:00-7:00 JST）: 流動性枯渇
- クリスマス・年末年始（12/24-1/3）: 極端な低流動性

**注意が必要**:
- 東京セッション単独（ロンドン・NY休場時）: ボラティリティ低
- 米国祝日（独立記念日、感謝祭など）: 流動性低下

---

## 🔬 重要度：中（検証・改善）

### 7. バックテスト・フォワードテスト基盤

現在のシステムは**リアルタイム分析**のみで、**過去データでの検証機能がありません**。

#### 7.1 疑似バックテスト（推奨）

週2-5回の低頻度トレードでは、従来型のバックテストよりも**「過去日付の再生シミュレーション」**が有効です。

```python
class HistoricalSimulator:
    """過去データ再生シミュレーター"""

    def simulate_historical_day(self, date: str) -> SimulationResult:
        """指定日のL1/L2を再構築し、L3/L4に判断させる

        Args:
            date: シミュレーション対象日（例: "2025-11-27"）

        Returns:
            L3とL4の予測結果と実際の値動きの比較
        """
        # 1. その日までのOHLC取得
        ohlc = self.fetch_ohlc_until(date)
        l2 = self.generate_l2_technical(ohlc)

        # 2. その日のニュースをアーカイブから取得
        l1 = self.scrape_news_archive(date)

        # 3. L3予測（素のAI）
        l3_prediction = self.ask_claude_l3(l1, l2)

        # 4. L4判断（makoスタイルAI + ルール適用）
        l4_decision = self.ask_claude_l4(l1, l2, l3_prediction)

        # 5. 答え合わせ（翌日の値動き）
        next_day_ohlc = self.fetch_ohlc(date, days=2)
        l3_result = self.evaluate_prediction(l3_prediction, next_day_ohlc)
        l4_result = self.evaluate_decision(l4_decision, next_day_ohlc)

        return SimulationResult(
            date=date,
            l3=l3_result,
            l4=l4_result,
            actual_move=next_day_ohlc
        )

    def run_monthly_backtest(self, year: int, month: int) -> BacktestReport:
        """1ヶ月分の疑似バックテスト

        Args:
            year: 年（例: 2025）
            month: 月（例: 11）

        Returns:
            月次バックテストレポート
        """
        results = []
        for day in self.get_trading_days(year, month):
            result = self.simulate_historical_day(day)
            results.append(result)

        return BacktestReport(
            period=f"{year}-{month:02d}",
            total_days=len(results),
            l3_performance=self.aggregate_performance([r.l3 for r in results]),
            l4_performance=self.aggregate_performance([r.l4 for r in results]),
            comparison=self.compare_l3_vs_l4(results)
        )
```

#### 7.2 実装の利点

**従来のバックテストとの違い**:
- ✅ 実際の市場データを使用（カーブフィッティングなし）
- ✅ L1（ファンダメンタル）も含めた統合判断を検証可能
- ✅ L3とL4の差異が明確に出る
- ✅ 1-2週間で30日分のシミュレーション完了

**注意点**:
- ニュースアーカイブの取得が必要（Bloomberg、Reuters等）
- 経済指標の発表値も正確に再現する必要あり
- スプレッドの時間帯別変動も考慮すべき

---

### 8. ニュースイベントリスク管理

**重要な経済指標発表時**は、テクニカル分析が全く機能しません。

#### 8.1 高インパクトイベントリスト

**最優先（トレード完全停止）**:
- 米国雇用統計（毎月第1金曜 22:30 JST）
- FOMC政策金利発表 + パウエル議長会見
- 日銀金融政策決定会合 + 総裁会見
- ECB政策金利発表 + ラガルド総裁会見

**注意レベル（ポジション縮小）**:
- 米国CPI・PPI（インフレ指標）
- 米国GDP速報値
- 各国PMI（製造業・サービス業）

#### 8.2 イベントカレンダー統合

```python
class EconomicCalendar:
    """経済指標カレンダーとの統合"""

    def check_upcoming_events(
        self,
        current_time: datetime,
        lookforward_hours: int = 24
    ) -> List[EconomicEvent]:
        """今後24時間以内の高インパクトイベントを取得

        Args:
            current_time: 現在時刻
            lookforward_hours: 先読み時間（デフォルト24時間）

        Returns:
            高インパクトイベントのリスト
        """
        # Forex Factory API または investing.com API から取得
        events = self.api.get_events(
            start_time=current_time,
            end_time=current_time + timedelta(hours=lookforward_hours),
            impact="HIGH"
        )

        return events

    def is_trading_allowed(self, current_time: datetime) -> Tuple[bool, str]:
        """トレード実行可否を判定

        Returns:
            (許可/不許可, 理由)
        """
        upcoming_events = self.check_upcoming_events(current_time)

        for event in upcoming_events:
            time_until_event = (event.time - current_time).total_seconds() / 3600

            # 24時間以内に高インパクトイベント
            if time_until_event <= 24:
                return False, f"{event.name}まで{time_until_event:.1f}時間。24時間ルール適用"

        return True, "高インパクトイベントなし"
```

#### 8.3 L4への統合

L4の判断プロセスに自動的に組み込む：

```json
{
  "l4_decision": {
    "economic_calendar_check": {
      "status": "WARNING",
      "upcoming_events": [
        {
          "name": "US Non-Farm Payrolls",
          "time": "2025-11-28T22:30:00+09:00",
          "hours_until": 18.5,
          "impact": "HIGH"
        }
      ],
      "recommendation": "WAIT",
      "reason": "24時間ルール: 雇用統計前はトレード見送り"
    },
    "final_decision": "WAIT"
  }
}
```

---

## 💡 重要度：低（将来的な拡張）

### 9. 機械学習モデルの統合

現在のルールベース（サポレジ、MA）に加えて、機械学習モデルを統合する選択肢もあります。

#### 9.1 推奨アプローチ

**段階的な導入**:
1. **Phase 1**: LightGBM/XGBoostで「エントリー確信度スコア」を算出
2. **Phase 2**: LSTMで短期価格予測（1-4時間先）
3. **Phase 3**: Transformerで複数時間軸の統合予測

**重要な注意点**:
- **解釈可能性を失わない**: ブラックボックス化は避ける
- **特徴量の透明性**: どの要素が判断に影響したか説明可能にする
- **過学習リスク**: ウォークフォワード検証を徹底

#### 9.2 実装例（確信度スコアリング）

```python
class MLConfidenceScorer:
    """機械学習による確信度スコアリング"""

    def __init__(self):
        self.model = self.load_model()

    def calculate_confidence(
        self,
        l1_features: dict,
        l2_features: dict
    ) -> float:
        """L1とL2の特徴量から確信度スコアを計算

        Args:
            l1_features: ファンダメンタル特徴量
            l2_features: テクニカル特徴量

        Returns:
            0.0-1.0の確信度スコア
        """
        # 特徴量ベクトル構築
        features = self.build_feature_vector(l1_features, l2_features)

        # LightGBMで確信度予測
        confidence = self.model.predict_proba(features)[0][1]

        # 特徴量重要度（解釈可能性）
        feature_importance = self.model.feature_importances_

        return confidence, feature_importance
```

**使用例**:
```python
confidence, importance = ml_scorer.calculate_confidence(l1, l2)

if confidence < 0.7:
    decision = "WAIT"  # 確信度70%未満は見送り
    reason = f"ML確信度: {confidence:.2%}"
```

---

### 10. ポートフォリオ最適化

複数ペアを取引する場合、**ポートフォリオ理論**を適用する選択肢もあります。

#### 10.1 リスクパリティアプローチ

```python
class PortfolioOptimizer:
    """ポートフォリオ最適化"""

    def calculate_risk_parity_weights(
        self,
        pairs: List[str],
        correlation_matrix: pd.DataFrame,
        volatilities: dict
    ) -> dict:
        """リスクパリティに基づくポジション配分

        各通貨ペアが同じリスクを持つように配分

        Args:
            pairs: 取引通貨ペアのリスト
            correlation_matrix: 相関係数マトリクス
            volatilities: 各ペアのボラティリティ（ATR等）

        Returns:
            ペアごとの推奨ウェイト
        """
        # 各ペアの逆ボラティリティを計算
        inv_vols = {pair: 1.0 / volatilities[pair] for pair in pairs}

        # 正規化してウェイトに変換
        total_inv_vol = sum(inv_vols.values())
        weights = {pair: inv_vols[pair] / total_inv_vol for pair in pairs}

        return weights
```

**注意点**:
- FXは相関が**動的に変化**するため難易度が高い
- マクロイベント（Brexit、コロナショック等）で相関が急変
- 静的な最適化よりも、動的なリスク管理が重要

---

## 🚨 プロダクション運用の注意点

### 心理面・規律

#### 最大連敗数の設定
- **5連敗したら1週間休む**: システム不調 or 市場環境変化の可能性
- 休止期間中は過去トレードの詳細分析に専念

#### 月次損失上限
- **月-10%で強制停止**: それ以上の損失は年間目標に致命的
- 翌月まで冷却期間（デモトレードは継続可）

#### トレードジャーナル
- **全トレードを記録**: エントリー前の心理状態も含む
- 週次レビュー: 成功・失敗パターンの抽出
- 月次レビュー: ルール改善の検討

### 技術面

#### API障害対策
```python
class EmergencyClose:
    """緊急クローズ機能"""

    def monitor_connection(self):
        """接続監視（1秒ごと）"""
        while True:
            if not self.broker_api.is_connected():
                self.emergency_close_all_positions()
                self.send_alert("API接続断。全ポジションクローズ")
            time.sleep(1)

    def emergency_close_all_positions(self):
        """すべてのポジションを成行で即座にクローズ"""
        positions = self.get_open_positions()
        for pos in positions:
            self.broker_api.close_position(pos.id, order_type="MARKET")
```

#### データ品質チェック
```python
def validate_ohlc_data(df: pd.DataFrame) -> bool:
    """異常なスパイクを検出

    Returns:
        True: データ正常、False: 異常あり
    """
    # 1本あたりの変動がATRの5倍を超える場合は異常
    price_changes = df['close'].pct_change().abs()
    atr = compute_atr(df)
    atr_pct = atr / df['close'].mean()

    if (price_changes > atr_pct * 5).any():
        return False  # スパイク検出

    return True
```

#### システムモニタリング
- **24/365稼働監視**: UptimeRobot、Datadog等
- **アラート設定**:
  - ポジション損失が-3%到達
  - API接続断が5分以上継続
  - 日次損失上限到達

---

## 📈 成功の定義

### 定量目標（6ヶ月後）

| 指標 | 目標値 | 最低ライン |
|------|--------|------------|
| 勝率 | 60% | 55% |
| プロフィットファクター | 2.0 | 1.5 |
| シャープレシオ | 1.5 | 1.0 |
| 最大ドローダウン | -15% | -20% |
| 月利 | +5% | +3% |

### 定性目標

- [ ] すべてのトレードがルールに準拠
- [ ] L5レビューを毎週欠かさず実行
- [ ] 感情的なトレードゼロ（ルール違反ゼロ）
- [ ] Note有料会員50名以上
- [ ] X（Twitter）フォロワー1000名以上

---

## 🎓 まとめ

### 優先実装順序

**フェーズ1（実運用前に必須 - 2週間）**:
1. ✅ リスク管理モジュール（ポジションサイジング、ストップロス）
2. ✅ トレードコスト計算
3. ✅ パフォーマンストラッキング
4. ✅ 経済指標カレンダー統合

**フェーズ2（運用開始後、早期に追加 - 2週間）**:
5. ✅ 相関リスク管理
6. ✅ 市場環境フィルター
7. ✅ 時間帯別フィルター
8. ✅ 疑似バックテスト基盤

**フェーズ3（継続的改善 - 3ヶ月）**:
9. ✅ 機械学習モデル（オプション）
10. ✅ ポートフォリオ最適化（オプション）

---

## 📚 参考文献

- Van Tharp, "Trade Your Way to Financial Freedom"
- Jack Schwager, "Market Wizards" series
- Ernest Chan, "Quantitative Trading"
- Andreas Clenow, "Following the Trend"

---

**最終更新**: 2025-11-28
**バージョン**: 1.0
**作成者**: Professional Fund Manager Advisory Team
