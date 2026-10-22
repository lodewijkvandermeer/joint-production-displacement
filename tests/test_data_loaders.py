import pytest

from jpdm import data


def test_shipped_files_load():
    assert len(data.carcass_shares()) == 17
    assert {r["series"] for r in data.whey_prices()} == {"Dry whey", "WPC 34%"}
    assert all(1 <= r["reachability"] <= 4 for r in data.reachability())


def test_known_data_quality_findings_are_exactly_these():
    # The broiler parts in the Cobb 500 yield chart add to 89.8% of live weight; the remaining 10.2% is carried as a
    # labelled residual row (processing shrink, skin and fat trim) with no value. Update this list if the data changes.
    assert data.problems() == []


def _write(tmp_path, monkeypatch, name, text):
    (tmp_path / name).write_text(text)
    monkeypatch.setattr(data, "DATA", tmp_path)


def test_wrong_columns_are_rejected(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, "technical_reachability.csv", "product,level,branch\nA,1,beef\n")
    with pytest.raises(ValueError, match="columns"):
        data.reachability()


def test_non_numeric_and_out_of_range_values_are_rejected(tmp_path, monkeypatch):
    head = "product,reachability_1_to_4,branch,item\n"
    for row, msg in (("A,x,beef,Hide", "not a number"), ("A,5,beef,Hide", "outside"), ("A,2.5,beef,Hide", "whole"), ("A,2,beef,", "required")):
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
