"""Accounting identities of the closed form that must hold for every animal and every parameter set."""
import math

import pytest

from jpdm import edm_model as M, params

BRANCHES = params.ALL


@pytest.mark.parametrize("br", BRANCHES, ids=[b.key for b in BRANCHES])
def test_stream_factors_sum_to_bundle(br):
    for eps_s in (br.eps_s_sr, br.eps_s_lr, 3.0):
        if eps_s <= 0:
            continue
        total = sum(br.DF_stream(k.name, eps_s) for k in br.streams)
        assert math.isclose(total, br.DF_bundle(eps_s), rel_tol=1e-12)


@pytest.mark.parametrize("br", BRANCHES, ids=[b.key for b in BRANCHES])
def test_constant_cost_limit_sums_to_one(br):
    total = sum(br.DF_stream_limit(k.name) for k in br.streams)
    assert math.isclose(total, 1.0, rel_tol=1e-12)


@pytest.mark.parametrize("br", BRANCHES, ids=[b.key for b in BRANCHES])
def test_product_factors_sum_to_stream_factor(br):
    rows = br.results(br.eps_s_lr)
    for st in br.streams:
        subs = [r for r in rows if r["stream"] == st.name]
        assert math.isclose(sum(r["DF"] for r in subs), br.DF_stream(st.name, br.eps_s_lr), rel_tol=1e-12)


@pytest.mark.parametrize("br", BRANCHES, ids=[b.key for b in BRANCHES])
def test_value_shares_sum_to_one(br):
    assert math.isclose(sum(r["share_total"] for r in br.results(br.eps_s_lr)), 1.0, rel_tol=1e-12)


@pytest.mark.parametrize("br", BRANCHES, ids=[b.key for b in BRANCHES])
def test_factors_rise_with_the_horizon(br):
    for k in br.streams:
        lr = br.DF_stream(k.name, br.eps_s_lr)
        assert 0.0 <= lr <= br.DF_stream_limit(k.name) + 1e-15
        if br.eps_s_sr > 0:
            assert br.DF_stream(k.name, br.eps_s_sr) <= lr + 1e-15


def test_single_product_formula():
    # one product, no joint production: DF = eps_s / (eps_s + |eps_d|)
    assert math.isclose(M.single_df(0.9, -0.55), 0.9 / 1.45)


def test_closed_form_matches_exact_toy_models():
    # the log-differential closed form is a first-order approximation: within 2.6% at a 10% shift
    for kind, idx, shift, exact, closed in M.numeric_check():
        if abs(shift) <= 0.10:
            assert abs(exact - closed) <= 0.026 * abs(exact), (kind, idx, shift)
