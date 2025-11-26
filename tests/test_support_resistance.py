import pandas as pd
import pytest

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


def test_1h_resistance_above_support():
    """
    Verify that 1H resistance levels are always above support levels.

    This test creates a scenario where a low reversal candidate (154.0)
    is below the current price but would otherwise qualify as both
    support and resistance. The resistance should NOT include levels
    below the current price or below the support levels.
    """
    timestamps = pd.date_range("2024-01-01", periods=60, freq="h", tz="UTC")
    rows = []
    for idx, ts in enumerate(timestamps):
        # Default: price around 156.0
        open_price = 155.8
        high_price = 156.2
        low_price = 155.5
        close_price = 156.0

        # Day 1: Low at 154.0 (below current price) - should be support only
        if idx == 5:
            open_price, high_price, low_price, close_price = 154.5, 155.0, 154.0, 154.3

        # Day 2: High at 157.5 (above current price) - valid resistance
        if idx == 18:
            open_price, high_price, low_price, close_price = 156.5, 157.5, 156.0, 157.2

        # Day 3: High at 158.0 (above current price) - valid resistance
        if idx == 30:
            open_price, high_price, low_price, close_price = 157.0, 158.0, 156.5, 157.8

        # Last price at 155.87
        if idx == 59:
            open_price, high_price, low_price, close_price = 155.5, 156.0, 155.3, 155.87

        rows.append({
            "timestamp": ts,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": 1000,
        })

    df = pd.DataFrame(rows)
    supports, resistances = agg.compute_support_resistance(df, "1h")

    # All resistance levels should be above all support levels
    if supports and resistances:
        assert min(resistances) > max(supports), (
            f"Resistance {min(resistances)} should be above support {max(supports)}"
        )

    # All resistance levels should be at or above the current price
    last_close = 155.87
    for r in resistances:
        assert r >= last_close, f"Resistance {r} should be >= current price {last_close}"


def test_4h_fallback_merges_nearby_levels():
    """
    Verify that 4H fallback merges nearly identical support/resistance levels.

    When the two lowest lows are very close (e.g., 152.814 and 152.826),
    they should be merged into one, and an alternative level should be found
    (or only one level returned if no suitable alternative exists).
    """
    # Create data where weekly structure doesn't trigger (no HH or LL breakout)
    # This forces the fallback path
    timestamps = pd.date_range("2024-01-01", periods=84, freq="4h", tz="UTC")
    rows = []

    for idx, ts in enumerate(timestamps):
        # Base price around 155.0, no weekly HH/LL breakout
        open_price = 155.0
        high_price = 155.5
        low_price = 154.5
        close_price = 155.2

        # Create two nearly identical lows (within 0.05 tolerance)
        if idx == 10:
            low_price = 152.814
        if idx == 20:
            low_price = 152.826  # Only 0.012 apart from 152.814

        # Create a distant alternative low
        if idx == 40:
            low_price = 153.50  # Sufficiently distant

        # Create two nearly identical highs
        if idx == 15:
            high_price = 157.892
        if idx == 25:
            high_price = 157.903  # Only 0.011 apart

        # Create a distant alternative high
        if idx == 45:
            high_price = 157.10  # Sufficiently distant

        rows.append({
            "timestamp": ts,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": 800,
        })

    df = pd.DataFrame(rows)
    supports, resistances = agg.compute_support_resistance(df, "4h")

    # Check that nearly identical levels are not both present
    if len(supports) >= 2:
        for i, s1 in enumerate(supports):
            for s2 in supports[i + 1:]:
                assert abs(s1 - s2) >= agg.FOUR_HOUR_MERGE_TOLERANCE, (
                    f"Supports {s1} and {s2} are too close (< {agg.FOUR_HOUR_MERGE_TOLERANCE})"
                )

    if len(resistances) >= 2:
        for i, r1 in enumerate(resistances):
            for r2 in resistances[i + 1:]:
                assert abs(r1 - r2) >= agg.FOUR_HOUR_MERGE_TOLERANCE, (
                    f"Resistances {r1} and {r2} are too close (< {agg.FOUR_HOUR_MERGE_TOLERANCE})"
                )


def test_1d_fallback_uses_lookback_window():
    """
    Verify that daily fallback only considers the 60-bar lookback window,
    not the full 200+ bar DataFrame.

    This ensures L2 daily support/resistance are within the recent 60 days,
    not from 200 days ago.
    """
    # Create 200 bars of data
    timestamps = pd.date_range("2024-01-01", periods=200, freq="D", tz="UTC")
    rows = []

    for idx, ts in enumerate(timestamps):
        # Old data (first 140 bars): extreme values that should NOT appear
        if idx < 140:
            open_price = 145.0
            high_price = 165.0 if idx == 50 else 146.0  # Extreme high at bar 50
            low_price = 135.0 if idx == 60 else 144.0   # Extreme low at bar 60
            close_price = 145.0
        else:
            # Recent data (last 60 bars): moderate values
            open_price = 150.0
            high_price = 152.0
            low_price = 148.0
            close_price = 150.5

        rows.append({
            "timestamp": ts,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": 500,
        })

    df = pd.DataFrame(rows)
    supports, resistances = agg.compute_support_resistance(df, "1d")

    # The extreme values from old data should NOT appear
    # (135.0 for support, 165.0 for resistance)
    for s in supports:
        assert s >= 145.0, f"Support {s} is from old data (should be >= 145.0)"

    for r in resistances:
        assert r <= 155.0, f"Resistance {r} is from old data (should be <= 155.0)"
