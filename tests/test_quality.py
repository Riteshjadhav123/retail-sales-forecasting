import pytest
import pandas as pd
from src.data.loader import load_raw_dataset
from src.data.quality import DataQualityEngine

def test_data_quality_engine():
    df = load_raw_dataset()
    engine = DataQualityEngine(df)
    report = engine.run_assessment()

    assert "summary" in report
    assert report["summary"]["row_count"] == len(df)
    assert "date_coverage" in report["summary"]
    assert report["summary"]["uniques"]["categories"] > 0

def test_data_quality_reports_generation(tmp_path):
    df = load_raw_dataset()
    engine = DataQualityEngine(df)
    json_p = str(tmp_path / "q_report.json")
    md_p = str(tmp_path / "q_report.md")
    report = engine.generate_reports(json_path=json_p, md_path=md_p)

    assert report["summary"]["row_count"] > 0
