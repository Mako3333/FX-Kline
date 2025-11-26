import pandas as pd

from fx_kline.core import ohlc_aggregator as agg


def test_compute_support_resistance_1h_reversals():
    timestamps = pd.date_range("2024-01-01", periods=48, freq="h", tz="UTC")
    rows = []
    for idx, ts in enumerate(timestamps):
        open_price = 100.0
        high_price = 101.0
        low_price = 99.0
        close_price = 100.5

        if idx == 2:
            open_price, high_price, low_price, close_price = 96.0, 96.5, 95.0, 96.2
        elif idx == 10:
            open_price, high_price, low_price, close_price = 104.0, 105.0, 103.5, 104.0
        elif idx == 26:
            open_price, high_price, low_price, close_price = 97.0, 97.5, 96.0, 97.2
        elif idx == 30:
            open_price, high_price, low_price, close_price = 105.0, 106.0, 104.5, 105.3
        elif idx > 30:
            open_price, high_price, low_price, close_price = 100.0, 104.0, 99.5, 100.8

        rows.append(
            {
                "timestamp": ts,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 1000,
            }
        )

    df = pd.DataFrame(rows)
    supports, resistances = agg.compute_support_resistance(df, "1h")

    assert supports == [95.0, 96.0]
    assert resistances == [106.0, 105.0]


def test_compute_support_resistance_4h_weekly_necklines():
    timestamps = pd.date_range("2024-01-01", periods=84, freq="4h", tz="UTC")
    rows = []
    for ts in timestamps:
        open_price = 100.0
        high_price = 101.0
        low_price = 99.0
        close_price = 100.5

        if ts.date() == pd.Timestamp("2024-01-02").date() and ts.hour == 4:
            low_price = 92.0
            high_price = 95.0
            close_price = 93.0
        if ts.date() == pd.Timestamp("2024-01-05").date() and ts.hour == 8:
            high_price = 105.0
            low_price = 99.0
            close_price = 104.0
        if ts.date() == pd.Timestamp("2024-01-09").date() and ts.hour == 12:
            low_price = 95.0
            high_price = 99.0
            close_price = 96.0
        if ts.date() == pd.Timestamp("2024-01-10").date() and ts.hour == 16:
            high_price = 111.0
            low_price = 108.0
            close_price = 110.0
        if ts == timestamps[-1]:
            open_price, high_price, low_price, close_price = 108.0, 109.0, 107.0, 108.0

        rows.append(
            {
                "timestamp": ts,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 800,
            }
        )

    df = pd.DataFrame(rows)
    supports, resistances = agg.compute_support_resistance(df, "4h")

    assert supports == [92.0, 95.0]
    assert resistances == [111.0, 105.0]


def test_compute_support_resistance_1d_three_candle_reversals():
    timestamps = pd.date_range("2024-01-01", periods=40, freq="D", tz="UTC")
    rows = []
    for idx, ts in enumerate(timestamps):
        # Noise data outside ±0.5% tolerance to avoid false reversals
        # Last close = 108.0, tolerance = 0.54 yen, range = [107.46, 108.54]
        # Using 92.0-94.0 range (well below tolerance)
        open_price = 93.0
        high_price = 94.0
        low_price = 92.0
        close_price = 93.0

        if idx == 10:
            # Resistance level: 108.5 (within 0.5% of final close 108.0)
            open_price, high_price, low_price, close_price = 108.2, 108.5, 108.0, 108.3
        elif idx in (11, 12, 13):
            # Three consecutive bearish candles after resistance
            open_price, high_price, low_price, close_price = 108.0, 108.2, 107.5, 107.6
        elif idx == 25:
            # Support level: 107.5 (within 0.5% of final close 108.0)
            open_price, high_price, low_price, close_price = 107.8, 108.0, 107.5, 107.6
        elif idx in (26, 27, 28):
            # Three consecutive bullish candles after support
            open_price, high_price, low_price, close_price = 107.6, 108.0, 107.5, 107.9
        elif idx == 39:  # Last row - set to 108.0 for tolerance range calculation
            open_price, high_price, low_price, close_price = 108.0, 108.2, 107.8, 108.0

        rows.append(
            {
                "timestamp": ts,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 500,
            }
        )

    df = pd.DataFrame(rows)
    supports, resistances = agg.compute_support_resistance(df, "1d")

    assert supports == [107.5]
    assert resistances == [108.5]
