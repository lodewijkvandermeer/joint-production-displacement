import pytest

from jpdm import data


def test_shipped_files_load():
    assert len(data.carcass_shares()) == 16
    assert {r["series"] for r in data.whey_prices()} == {"Dry whey", "WPC 34%"}
    assert all(1 <= r["reachability"] <= 4 for r in data.reachability())


def test_known_data_quality_findings_are_exactly_these():
    # Broiler live-weight shares add to 89.8%: a data gap to resolve with the author's numbers (not a loader bug).
    # Update this list when the data is fixed.
    assert data.problems() == ["Broiler: live weight shares add to 89.8%, not 100%"]


def _write(tmp_path, monkeypatch, name, text):
    (tmp_path / name).write_text(text)
    monkeypatch.setattr(data, "DATA", tmp_path)


def test_wrong_columns_are_rejected(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, "technical_reachability.csv", "product,level,df\nA,1,0.1\n")
    with pytest.raises(ValueError, match="columns"):
        data.reachability()


def test_non_numeric_and_out_of_range_values_are_rejected(tmp_path, monkeypatch):
    head = "product,reachability_1_to_4,df_3_5_years\n"
    for row, msg in (("A,x,0.1", "not a number"), ("A,5,0.1", "outside"), ("A,2.5,0.1", "whole"), ("A,2,1.5", "outside")):
        _write(tmp_path, monkeypatch, "technical_reachability.csv", head + row + "\n")
        with pytest.raises(ValueError, match=msg):
            data.reachability()


def test_duplicates_and_bad_months_are_rejected(tmp_path, monkeypatch):
    head = "month,series,usd_per_lb\n"
    _write(tmp_path, monkeypatch, "whey_prices_central_us_2022_2026.csv", head + "2022-01,A,1\n2022-01,A,2\n")
    with pytest.raises(ValueError, match="duplicate"):
        data.whey_prices()
    _write(tmp_path, monkeypatch, "whey_prices_central_us_2022_2026.csv", head + "2022-13,A,1\n")
    with pytest.raises(ValueError, match="YYYY-MM"):
        data.whey_prices()


def test_share_sums_are_reported(tmp_path, monkeypatch):
    head = "animal,part,share_of_live_weight_pct,share_of_value_pct\n"
    _write(tmp_path, monkeypatch, "carcass_weight_and_value_shares.csv", head + "X,a,60,50\nX,b,30,50\n")
    assert data.problems() == ["X: live weight shares add to 90.0%, not 100%"]
