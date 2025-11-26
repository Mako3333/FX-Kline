"""Unit tests for summary_consolidator module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from fx_kline.core import summary_consolidator as sc


@pytest.fixture
def temp_reports_dir(tmp_path):
    """Create a temporary reports directory with sample analysis files."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    return reports_dir


@pytest.fixture
def sample_analysis_data():
    """Sample analysis data matching schema_version=1."""
    return {
        "pair": "USDJPY",
        "interval": "1h",
        "period": "10d",
        "trend": "UP",
        "support_levels": [149.85, 149.92],
        "resistance_levels": [151.20, 151.05],
        "rsi": 62.45,
        "atr": 0.3245,
        "average_volatility": 0.2812,
        "generated_at": "2025-11-25T08:00:00+09:00",
        "schema_version": 1,
    }


def create_analysis_file(reports_dir: Path, pair: str, interval: str, period: str, data: dict):
    """Helper to create an analysis JSON file."""
    file_path = reports_dir / f"{pair}_{interval}_{period}_analysis.json"
    with file_path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)
    return file_path


def test_discover_analysis_files_groups_by_pair(temp_reports_dir, sample_analysis_data):
    """Test that analysis files are correctly grouped by currency pair."""
    # Create multiple files for different pairs and intervals
    create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", sample_analysis_data)
    create_analysis_file(temp_reports_dir, "USDJPY", "4h", "35d", {**sample_analysis_data, "interval": "4h"})
    create_analysis_file(temp_reports_dir, "EURUSD", "1h", "10d", {**sample_analysis_data, "pair": "EURUSD"})

    grouped = sc.discover_analysis_files(temp_reports_dir)

    assert len(grouped) == 2
    assert "USDJPY" in grouped
    assert "EURUSD" in grouped
    assert len(grouped["USDJPY"]) == 2
    assert len(grouped["EURUSD"]) == 1


def test_discover_analysis_files_empty_directory(tmp_path):
    """Test behavior with empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    grouped = sc.discover_analysis_files(empty_dir)

    assert grouped == {}


def test_discover_analysis_files_nonexistent_directory(tmp_path):
    """Test behavior with nonexistent directory."""
    nonexistent = tmp_path / "does_not_exist"

    grouped = sc.discover_analysis_files(nonexistent)

    assert grouped == {}


def test_load_analysis_file_valid(temp_reports_dir, sample_analysis_data):
    """Test loading a valid analysis file."""
    file_path = create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", sample_analysis_data)

    tf_analysis = sc.load_analysis_file(file_path)

    assert tf_analysis is not None
    assert tf_analysis.interval == "1h"
    assert tf_analysis.period == "10d"
    assert tf_analysis.trend == "UP"
    assert tf_analysis.support_levels == [149.85, 149.92]
    assert tf_analysis.resistance_levels == [151.20, 151.05]
    assert tf_analysis.rsi == 62.45
    assert tf_analysis.atr == 0.3245
    assert tf_analysis.average_volatility == 0.2812
    assert tf_analysis.data_timestamp == "2025-11-25T08:00:00+09:00"


def test_load_analysis_file_invalid_schema_version(temp_reports_dir, sample_analysis_data):
    """Test that files with wrong schema_version are rejected."""
    invalid_data = {**sample_analysis_data, "schema_version": 2}
    file_path = create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", invalid_data)

    tf_analysis = sc.load_analysis_file(file_path)

    assert tf_analysis is None


def test_load_analysis_file_missing_required_field(temp_reports_dir, sample_analysis_data):
    """Test that files missing required fields are rejected."""
    invalid_data = {k: v for k, v in sample_analysis_data.items() if k != "trend"}
    file_path = create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", invalid_data)

    tf_analysis = sc.load_analysis_file(file_path)

    assert tf_analysis is None


def test_load_analysis_file_corrupt_json(temp_reports_dir):
    """Test that corrupt JSON files are handled gracefully."""
    file_path = temp_reports_dir / "USDJPY_1h_10d_analysis.json"
    file_path.write_text("{invalid json content}", encoding="utf-8")

    tf_analysis = sc.load_analysis_file(file_path)

    assert tf_analysis is None


def test_load_analysis_file_handles_null_indicators(temp_reports_dir, sample_analysis_data):
    """Test that null indicator values are handled correctly."""
    data_with_nulls = {**sample_analysis_data, "rsi": None, "atr": None, "average_volatility": None}
    file_path = create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", data_with_nulls)

    tf_analysis = sc.load_analysis_file(file_path)

    assert tf_analysis is not None
    assert tf_analysis.rsi is None
    assert tf_analysis.atr is None
    assert tf_analysis.average_volatility is None


@patch('fx_kline.core.summary_consolidator.get_jst_now')
def test_consolidate_pair_analyses_complete_data(mock_jst_now, temp_reports_dir, sample_analysis_data):
    """Test consolidation with all three timeframes present."""
    mock_jst_now.return_value.isoformat.return_value = "2025-11-25T10:00:00+09:00"

    # Create all three timeframes
    create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", sample_analysis_data)
    create_analysis_file(temp_reports_dir, "USDJPY", "4h", "35d", {**sample_analysis_data, "interval": "4h", "period": "35d"})
    create_analysis_file(temp_reports_dir, "USDJPY", "1d", "200d", {**sample_analysis_data, "interval": "1d", "period": "200d"})

    analysis_files = list(temp_reports_dir.glob("USDJPY_*_analysis.json"))
    summary = sc.consolidate_pair_analyses("USDJPY", analysis_files)

    assert summary.pair == "USDJPY"
    assert summary.schema_version == 2
    assert summary.generated_at == "2025-11-25T10:00:00+09:00"
    assert len(summary.timeframes) == 3
    assert "1h" in summary.timeframes
    assert "4h" in summary.timeframes
    assert "1d" in summary.timeframes
    assert summary.metadata["total_timeframes"] == 3
    assert summary.metadata["missing_timeframes"] == []
    assert len(summary.metadata["source_files"]) == 3
    assert summary.metadata["consolidation_version"] == "1.0.0"


@patch('fx_kline.core.summary_consolidator.get_jst_now')
def test_consolidate_pair_analyses_partial_data(mock_jst_now, temp_reports_dir, sample_analysis_data):
    """Test consolidation with missing timeframes."""
    mock_jst_now.return_value.isoformat.return_value = "2025-11-25T10:00:00+09:00"

    # Create only 1h and 4h (missing 1d)
    create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", sample_analysis_data)
    create_analysis_file(temp_reports_dir, "USDJPY", "4h", "35d", {**sample_analysis_data, "interval": "4h", "period": "35d"})

    analysis_files = list(temp_reports_dir.glob("USDJPY_*_analysis.json"))
    summary = sc.consolidate_pair_analyses("USDJPY", analysis_files)

    assert summary.pair == "USDJPY"
    assert len(summary.timeframes) == 2
    assert "1h" in summary.timeframes
    assert "4h" in summary.timeframes
    assert "1d" not in summary.timeframes
    assert summary.metadata["total_timeframes"] == 2
    assert summary.metadata["missing_timeframes"] == ["1d"]


@patch('fx_kline.core.summary_consolidator.get_jst_now')
def test_consolidate_pair_analyses_timeframe_ordering(mock_jst_now, temp_reports_dir, sample_analysis_data):
    """Test that timeframes are ordered 1d → 4h → 1h in the output."""
    mock_jst_now.return_value.isoformat.return_value = "2025-11-25T10:00:00+09:00"

    # Create files in random order
    create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", sample_analysis_data)
    create_analysis_file(temp_reports_dir, "USDJPY", "1d", "200d", {**sample_analysis_data, "interval": "1d", "period": "200d"})
    create_analysis_file(temp_reports_dir, "USDJPY", "4h", "35d", {**sample_analysis_data, "interval": "4h", "period": "35d"})

    analysis_files = list(temp_reports_dir.glob("USDJPY_*_analysis.json"))
    summary = sc.consolidate_pair_analyses("USDJPY", analysis_files)

    # Check that keys are in the expected order
    timeframe_keys = list(summary.timeframes.keys())
    assert timeframe_keys == ["1d", "4h", "1h"]


def test_consolidated_summary_to_dict():
    """Test ConsolidatedSummary serialization to dict."""
    tf_1h = sc.TimeframeAnalysis(
        interval="1h",
        period="10d",
        trend="UP",
        support_levels=[149.85, 149.92],
        resistance_levels=[151.20, 151.05],
        rsi=62.45,
        atr=0.3245,
        average_volatility=0.2812,
        data_timestamp="2025-11-25T08:00:00+09:00",
    )

    summary = sc.ConsolidatedSummary(
        pair="USDJPY",
        schema_version=2,
        generated_at="2025-11-25T10:00:00+09:00",
        timeframes={"1h": tf_1h},
        metadata={"source_files": ["USDJPY_1h_10d_analysis.json"], "total_timeframes": 1},
    )

    result_dict = summary.to_dict()

    assert result_dict["pair"] == "USDJPY"
    assert result_dict["schema_version"] == 2
    assert result_dict["generated_at"] == "2025-11-25T10:00:00+09:00"
    assert "1h" in result_dict["timeframes"]
    assert result_dict["timeframes"]["1h"]["interval"] == "1h"
    assert result_dict["timeframes"]["1h"]["rsi"] == 62.45
    assert result_dict["metadata"]["total_timeframes"] == 1


def test_consolidated_summary_to_dict_metadata_immutability():
    """Test that modifying returned dict does not affect original metadata."""
    tf_1h = sc.TimeframeAnalysis(
        interval="1h",
        period="10d",
        trend="UP",
        support_levels=[149.85],
        resistance_levels=[151.20],
        rsi=62.45,
        atr=0.3245,
        average_volatility=0.2812,
        data_timestamp="2025-11-25T08:00:00+09:00",
    )

    original_metadata = {
        "source_files": ["USDJPY_1h_10d_analysis.json"],
        "total_timeframes": 1,
        "missing_timeframes": ["4h"],
        "consolidation_version": "1.0.0",
    }

    summary = sc.ConsolidatedSummary(
        pair="USDJPY",
        schema_version=2,
        generated_at="2025-11-25T10:00:00+09:00",
        timeframes={"1h": tf_1h},
        metadata=original_metadata.copy(),
    )

    # Get original metadata values
    original_total = summary.metadata["total_timeframes"]
    original_files = summary.metadata["source_files"].copy()

    # Call to_dict() and modify the returned dict
    result_dict = summary.to_dict()
    result_dict["metadata"]["total_timeframes"] = 999
    result_dict["metadata"]["new_key"] = "modified"
    result_dict["metadata"]["source_files"].append("modified_file.json")

    # Verify original metadata was not affected
    assert summary.metadata["total_timeframes"] == original_total
    assert summary.metadata["source_files"] == original_files
    assert "new_key" not in summary.metadata
    assert summary.metadata is not result_dict["metadata"]


def test_write_summary(tmp_path):
    """Test writing summary to JSON file."""
    tf_1h = sc.TimeframeAnalysis(
        interval="1h",
        period="10d",
        trend="UP",
        support_levels=[149.85, 149.92],
        resistance_levels=[151.20, 151.05],
        rsi=62.45,
        atr=0.3245,
        average_volatility=0.2812,
        data_timestamp="2025-11-25T08:00:00+09:00",
    )

    summary = sc.ConsolidatedSummary(
        pair="USDJPY",
        schema_version=2,
        generated_at="2025-11-25T10:00:00+09:00",
        timeframes={"1h": tf_1h},
        metadata={"source_files": ["USDJPY_1h_10d_analysis.json"], "total_timeframes": 1},
    )

    output_dir = tmp_path / "summary_reports"
    output_path = output_dir / "USDJPY_summary.json"

    sc.write_summary(summary, output_path)

    assert output_path.exists()

    # Verify content
    with output_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    assert data["pair"] == "USDJPY"
    assert data["schema_version"] == 2
    assert "1h" in data["timeframes"]


@patch('fx_kline.core.summary_consolidator.get_jst_now')
def test_consolidate_reports_batch(mock_jst_now, temp_reports_dir, sample_analysis_data, tmp_path):
    """Test batch consolidation of multiple pairs."""
    mock_jst_now.return_value.isoformat.return_value = "2025-11-25T10:00:00+09:00"

    # Create files for two pairs
    create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", sample_analysis_data)
    create_analysis_file(temp_reports_dir, "USDJPY", "4h", "35d", {**sample_analysis_data, "interval": "4h"})
    create_analysis_file(temp_reports_dir, "EURUSD", "1h", "10d", {**sample_analysis_data, "pair": "EURUSD"})

    output_dir = tmp_path / "summary_reports"

    results = sc.consolidate_reports_batch(temp_reports_dir, output_dir)

    assert len(results) == 2
    assert "USDJPY" in results
    assert "EURUSD" in results
    assert results["USDJPY"].exists()
    assert results["EURUSD"].exists()

    # Verify USDJPY has 2 timeframes
    with results["USDJPY"].open("r", encoding="utf-8") as fp:
        usdjpy_data = json.load(fp)
    assert len(usdjpy_data["timeframes"]) == 2

    # Verify EURUSD has 1 timeframe
    with results["EURUSD"].open("r", encoding="utf-8") as fp:
        eurusd_data = json.load(fp)
    assert len(eurusd_data["timeframes"]) == 1


@patch('fx_kline.core.summary_consolidator.get_jst_now')
def test_consolidate_reports_batch_with_pairs_filter(mock_jst_now, temp_reports_dir, sample_analysis_data, tmp_path):
    """Test batch consolidation with pairs filter."""
    mock_jst_now.return_value.isoformat.return_value = "2025-11-25T10:00:00+09:00"

    # Create files for two pairs
    create_analysis_file(temp_reports_dir, "USDJPY", "1h", "10d", sample_analysis_data)
    create_analysis_file(temp_reports_dir, "EURUSD", "1h", "10d", {**sample_analysis_data, "pair": "EURUSD"})

    output_dir = tmp_path / "summary_reports"

    # Filter to only USDJPY
    results = sc.consolidate_reports_batch(temp_reports_dir, output_dir, pairs_filter=["USDJPY"])

    assert len(results) == 1
    assert "USDJPY" in results
    assert "EURUSD" not in results


def test_consolidate_reports_batch_empty_directory(tmp_path):
    """Test batch consolidation with empty directory."""
    empty_dir = tmp_path / "empty_reports"
    empty_dir.mkdir()
    output_dir = tmp_path / "summary_reports"

    results = sc.consolidate_reports_batch(empty_dir, output_dir)

    assert results == {}
    assert not output_dir.exists()  # Should not create output dir if no results
