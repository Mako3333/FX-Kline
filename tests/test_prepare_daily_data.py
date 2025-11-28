from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

SCRIPTS_PATH = PROJECT_ROOT / "scripts"
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))

from fx_kline.analyst import data_manager  # noqa: E402
import prepare_daily_data  # noqa: E402


def test_prepare_daily_data_copies_summary_files(monkeypatch, tmp_path):
    source_dir = tmp_path / "summary_reports"
    source_dir.mkdir(parents=True)
    sample = source_dir / "USDJPY_summary.json"
    sample.write_text('{"pair": "USDJPY"}', encoding="utf-8")

    data_root = tmp_path / "data"
    monkeypatch.setattr(data_manager, "get_data_root", lambda: data_root)

    exit_code = prepare_daily_data.main(["--date", "2025-11-28"])
    assert exit_code == 0

    dest = data_root / "2025" / "11" / "28" / "summaries" / sample.name
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == sample.read_text(encoding="utf-8")
