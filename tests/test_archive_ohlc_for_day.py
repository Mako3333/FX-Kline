from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
SCRIPTS_PATH = PROJECT_ROOT / "scripts"

for p in (SRC_PATH, SCRIPTS_PATH):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fx_kline.analyst import data_manager  # noqa: E402
import scripts.archive_ohlc_for_day as archive_ohlc_for_day  # noqa: E402


def test_archive_ohlc_for_day_creates_csv(monkeypatch, tmp_path):
    target_date = date(2025, 11, 27)
    market_date = date(2025, 11, 28)

    # Redirect data root
    monkeypatch.setattr(data_manager, "get_data_root", lambda: tmp_path / "data")

    # Mock fetcher to return predictable data (covering target_date)
    def _fake_fetch(*args, **kwargs):
        idx = pd.DatetimeIndex(
            [
                "2025-11-27 00:00:00+09:00",
                "2025-11-27 00:15:00+09:00",
            ]
        )
        return pd.DataFrame(
            {"Open": [1.0, 1.1], "High": [1.2, 1.2], "Low": [0.9, 1.0], "Close": [1.05, 1.1], "Volume": [10, 12]},
            index=idx,
        )

    monkeypatch.setattr(archive_ohlc_for_day.data_fetcher, "fetch_ohlc_range_dataframe", _fake_fetch)

    exit_code = archive_ohlc_for_day.main(
        [
            "--market-date",
            market_date.strftime("%Y-%m-%d"),
            "--pairs",
            "USDJPY",
        ]
    )

    assert exit_code == 0
    csv_path = data_manager.get_daily_ohlc_filepath(target_date, "USDJPY", "15m")
    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "USDJPY" not in content  # sanity check: only OHLC rows
    lines = content.splitlines()
    assert len(lines) > 0, "CSV file should not be empty"
    assert "datetime" in lines[0]
