"""The exact non-linear model: agreement with the closed form for small shifts, and the full-loss and price-cap results."""
import pytest

from jpdm import exact_model as X, params


@pytest.fixture(scope="module")
def cow():
    br = params.dairy("2026")
    return br, X.exact_for(br)


@pytest.fixture(scope="module")
def hen():
    br = params.eggs("2019-21")
    return br, X.exact_for(br)


def test_baseline_is_an_equilibrium(cow, hen):
    for br, ex in (cow, hen):
        r = ex.solve()
        assert abs(r["A"] - 1.0) < 1e-6
        assert all(abs(p - 1.0) < 1e-6 for p in r["P"].values())


@pytest.mark.parametrize("stream", ["Cheese", "Fluid milk", "Whey protein"])
def test_closed_form_within_1_5_percent_at_a_10_percent_shift(cow, stream):
    br, ex = cow
    exact = ex.solve(kappa={stream: -0.10})["A"] - 1.0
    closed = br.DF_stream(stream, br.eps_s_lr) * -0.10
    assert abs(exact - closed) <= 0.015 * abs(exact)


def test_whey_protein_market_lost(cow):
    br, ex = cow
    lr = ex.solve(cap={"Whey protein": 0.06})["A"] - 1.0
    lim = ex.solve(cap={"Whey protein": 0.06}, constant_cost=True)["A"] - 1.0
    assert round(lr, 3) == -0.044
    assert round(lim, 3) == -0.073


def test_cheese_at_half_price(cow):
    br, ex = cow
    r = ex.solve(cap={"Cheese": 0.5})
    assert round(r["A"] - 1.0, 2) == -0.18
    assert round(r["sub_share"]["Cheese"], 2) == 0.61


def test_egg_white_market_lost(hen):
    br, ex = hen
    assert round(ex.solve(cap={"Egg white": 0.35})["A"] - 1.0, 3) == -0.030
    assert round(ex.solve(cap={"Egg white": 0.35}, constant_cost=True)["A"] - 1.0, 3) == -0.044


def test_shell_egg_route_closes_near_56_percent(hen):
    br, ex = hen
    assert ex.solve(cap={"Shell eggs": 0.55})["Q"]["Shell eggs"] < 1e-6
    assert ex.solve(cap={"Shell eggs": 0.57})["Q"]["Shell eggs"] > 0.1
    assert round(ex.solve(cap={"Shell eggs": 0.5})["A"] - 1.0, 2) == -0.44
