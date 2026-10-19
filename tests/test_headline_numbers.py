"""Headline figures reported in the paper (section 6). A change in parameters that moves them should be deliberate."""
import pytest

from jpdm import params


def df(br, product_prefix, horizon="lr"):
    eps = {"sr": br.eps_s_sr, "lr": br.eps_s_lr}[horizon]
    rows = br.results(eps)
    return sum(r["DF"] if horizon != "limit" else r["DF_limit"] for r in rows if r["sub"].startswith(product_prefix))


def stream_df(br, stream, horizon="lr"):
    if horizon == "limit":
        return br.DF_stream_limit(stream)
    return br.DF_stream(stream, br.eps_s_lr if horizon == "lr" else br.eps_s_sr)


@pytest.fixture(scope="module")
def cow():
    return params.dairy("2026")


@pytest.fixture(scope="module")
def hen():
    return params.eggs("2019-21")


def test_dairy_factors(cow):
    assert round(stream_df(cow, "Cheese", "sr"), 3) == 0.075
    assert round(stream_df(cow, "Cheese"), 3) == 0.282
    assert round(stream_df(cow, "Cheese", "limit"), 3) == 0.490
    assert round(stream_df(cow, "Fluid milk"), 3) == 0.101
    assert round(stream_df(cow, "Whey protein"), 3) == 0.032
    assert round(stream_df(cow, "Whey protein", "limit"), 3) == 0.056
    assert round(df(cow, "WPC 80"), 3) == 0.018
    assert round(df(cow, "WPI"), 3) == 0.015
    assert round(cow.DF_bundle(cow.eps_s_lr), 3) == 0.575


def test_whey_protein_at_2019_prices():
    old = params.dairy("2019")
    assert round(old.DF_stream("Whey protein", old.eps_s_lr), 3) == 0.008


def test_cheese_to_whey_ratio_is_the_same_at_every_horizon(cow):
    ratios = [stream_df(cow, "Cheese", h) / stream_df(cow, "Whey protein", h) for h in ("sr", "lr", "limit")]
    assert max(ratios) - min(ratios) < 1e-9
    assert 8.5 < ratios[0] < 9.0


def test_egg_factors(hen):
    assert round(stream_df(hen, "Shell eggs"), 3) == 0.458
    assert round(stream_df(hen, "Shell eggs", "limit"), 2) == 0.68
    assert round(stream_df(hen, "Whole egg products"), 3) == 0.138
    assert round(stream_df(hen, "Egg white"), 3) == 0.030
    assert round(stream_df(hen, "Egg white", "limit"), 3) == 0.044
    assert round(hen.DF_bundle(hen.eps_s_lr), 3) == 0.673


def test_value_shares(cow, hen):
    share = {r["sub"]: r["share_total"] for r in cow.results(cow.eps_s_lr)}
    assert round(share["Cheese (cheddar-equivalent)"], 3) == 0.404
    assert round(sum(v for k, v in share.items() if k.startswith(("WPC 80", "WPI"))), 3) == 0.126
    eshare = {r["stream"]: 0 for r in hen.results(hen.eps_s_lr)}
    for r in hen.results(hen.eps_s_lr):
        eshare[r["stream"]] += r["share_total"]
    assert round(eshare["Shell eggs"], 3) == 0.828
    assert round(eshare["Egg white"], 3) == 0.029


def test_meat_factors():
    broiler, steer, hog = params.broiler(), params.beef(), params.pork()
    assert round(df(broiler, "Boneless skinless breast"), 2) == 0.23
    assert round(broiler.DF_stream("Breast meat", broiler.eps_s_lr), 2) == 0.28   # breast and tenders together
    assert round(steer.DF_stream("Middle meats (whole cut)", steer.eps_s_lr), 2) == 0.19
    assert round(steer.DF_stream("Minced beef (grinding material)", steer.eps_s_lr), 2) == 0.13
    assert round(broiler.DF_stream("Backs & necks (MSC)", broiler.eps_s_lr), 3) == 0.003
    assert round(broiler.DF_bundle(broiler.eps_s_lr), 2) == 0.42
    assert round(hog.DF_bundle(hog.eps_s_lr), 2) == 0.62
