from pathlib import Path

import pandas as pd
import pytest

from fx_kline.core import ohlc_aggregator as agg


def _build_sample_df(rows: int = 20) -> pd.DataFrame:
    base = 100.0
    data = []
    for idx in range(rows):
        open_price = base + idx * 0.5
        data.append(
            {
                "datetime": pd.Timestamp("2024-01-01T00:00:00Z") + pd.Timedelta(hours=idx),
                "open": open_price,
                "high": open_price + 0.8,
                "low": open_price - 0.7,
                "close": open_price + 0.4,
                "volume": 1000 - idx * 5,
            }
        )
    return pd.DataFrame(data)


def test_parse_metadata_from_filename():
    pair, interval, period = agg.parse_metadata_from_filename(Path("USDJPY_1h_10d.csv"))
    assert pair == "USDJPY"
    assert interval == "1h"
    assert period == "10d"


def test_detect_trend_identifies_up_move():
    closes = pd.Series([100, 100.5, 101.0, 102.0])
    assert agg.detect_trend(closes) == "UP"


def test_analyze_dataframe_produces_schema():
    df = _build_sample_df()
    result = agg.analyze_dataframe(df, "USDJPY", "1h", "10d").to_dict()

    assert result["pair"] == "USDJPY"
    assert result["interval"] == "1h"
    assert result["period"] == "10d"
    assert result["trend"] in {"UP", "DOWN", "SIDEWAYS"}
    # 1H reversal detection finds session-level extremes
    # With only 20 hours of data (1 session day), only 1 support/resistance level is detected
    assert len(result["support_levels"]) >= 1
    assert result["support_levels"][0] == pytest.approx(99.3, rel=1e-3)
    assert len(result["resistance_levels"]) >= 1
    assert result["rsi"] is not None
    assert result["atr"] is not None
    assert result["average_volatility"] == pytest.approx(1.5, rel=1e-3)
    assert result["schema_version"] == 1
    assert "T" in result["generated_at"]
