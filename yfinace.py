import yfinance as yf

# USD/JPY の1時間足を過去30日分取得
df = yf.download("USDJPY=X", interval="1h", period="30d", auto_adjust=False)

# データの基本情報を確認
print("=" * 60)
print("取得データの概要")
print("=" * 60)
print(f"取得データ総数: {len(df)} 件")
print(f"データ期間: {df.index[0]} ～ {df.index[-1]}")
print(f"カラム: {list(df.columns)}")
print("\n" + "=" * 60)
print("最初の5行（OHLCデータ）")
print("=" * 60)
print(df[['Open', 'High', 'Low', 'Close']].head())
print("\n" + "=" * 60)
print("最後の5行（OHLCデータ）")
print("=" * 60)
print(df[['Open', 'High', 'Low', 'Close']].tail())
