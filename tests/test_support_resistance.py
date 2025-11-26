import pandas as pd
import pytest

from fx_kline.core import ohlc_aggregator as agg


def test_merge_candidates_prefers_extreme_then_recent():
    candidates = [
        (100.2, pd.Timestamp("2024-01-02")),
        (100.1, pd.Timestamp("2024-01-03")),  # more extreme support
        (101.5, pd.Timestamp("2024-01-01")),
        (101.4, pd.Timestamp("2024-01-04")),  # newer but less extreme resistance
    ]

    merged_supports = agg._merge_candidates_by_atr(candidates, tolerance=1.0, is_support=True)
    merged_resistances = agg._merge_candidates_by_atr(candidates, tolerance=1.0, is_support=False)

    assert [round(p, 3) for p, _ in merged_supports] == [100.1, 101.5]
    # Resistance keeps the higher price even if an older timestamp exists
    assert [round(p, 3) for p, _ in merged_resistances] == [101.5, 100.2]


def test_daily_atr_guardrail_filters_far_levels():
    timestamps = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    rows = []

    for idx, ts in enumerate(timestamps):
        open_price = 100.0
        high_price = 102.0
        low_price = 98.0
        close_price = 100.0

        if idx == 0:
            # Far support candidate (will be filtered by ATR guard)
            low_price = 80.0
            close_price = 81.0
        elif idx in (1, 2, 3):
            open_price = 90.0
            close_price = 91.0  # bullish follow-through for idx=0
        elif idx == 4:
            # Near support candidate (should survive guardrail)
            low_price = 98.0
            close_price = 98.5
        elif idx in (5, 6, 7):
            open_price = 99.0
            close_price = 100.2  # bullish follow-through for idx=4

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
    supports, resistances = agg.compute_support_resistance(df, "1d", atr_value=1.0)

    assert supports and supports[0] == pytest.approx(98.0, rel=1e-3)
    assert resistances  # fallback should populate if none survive


def test_ema_reaction_support_bounce_detected():
    timestamps = pd.date_range("2024-01-01", periods=220, freq="h", tz="UTC")
    rows = []
    last_idx = len(timestamps) - 1

    for idx, ts in enumerate(timestamps):
        open_price = 100.0
        high_price = 100.3
        low_price = 99.7
        close_price = 100.0

        if idx == last_idx:
            low_price = 99.0  # dip under EMA
            close_price = 100.6  # close back above EMA
            high_price = 100.9

        rows.append(
            {
                "datetime": ts,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 800,
            }
        )

    df = pd.DataFrame(rows)
    ema_features = agg.compute_ema_features(df, "1h")

    assert ema_features["25"]["reaction"] == "support_bounce"
    assert ema_features["25"]["reaction_bars_ago"] == 0
