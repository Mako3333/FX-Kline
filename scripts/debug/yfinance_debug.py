import sys

import yfinance as yf


def main() -> int:
    """Simple helper script to inspect raw yfinance data for USDJPY."""
    try:
        df = yf.download("USDJPY=X", interval="1h", period="30d", auto_adjust=False)
    except Exception as e:  # pragma: no cover - manual debug only
        print(f"Error downloading data: {e}")
        return 1

    print("=" * 60)
    print("取得データの概要")
    print("=" * 60)
    print(f"取得データ総数: {len(df)} 件")
    if len(df) == 0:
        print("警告: データが取得できませんでした")
        return 1

    print(f"データ期間: {df.index[0]} ～ {df.index[-1]}")
    print(f"カラム: {list(df.columns)}")
    print("\n" + "=" * 60)
    print("最初の5行（OHLCデータ）")
    print("=" * 60)
    print(df[["Open", "High", "Low", "Close"]].head())
    print("\n" + "=" * 60)
    print("最後の5行（OHLCデータ）")
    print("=" * 60)
    print(df[["Open", "High", "Low", "Close"]].tail())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


