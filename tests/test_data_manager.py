from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_kline.analyst import data_manager  # noqa: E402


def test_get_daily_data_dir_builds_expected_path(monkeypatch, tmp_path):
    monkeypatch.setattr(data_manager, "get_data_root", lambda: tmp_path / "data")
    target_date = date(2025, 11, 28)
    daily_path = data_manager.get_daily_data_dir(target_date)
    assert daily_path == tmp_path / "data" / "2025" / "11" / "28"


def test_get_daily_summaries_dir_creates_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(data_manager, "get_data_root", lambda: tmp_path / "data")
    target_date = date(2025, 11, 28)
    summaries_dir = data_manager.get_daily_summaries_dir(target_date)
    assert summaries_dir.exists()
    assert summaries_dir.is_dir()
    assert summaries_dir == tmp_path / "data" / "2025" / "11" / "28" / "summaries"
