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
    # central valuation: half of the whey-protein premium over its other-solids value counts as milk value
    assert round(stream_df(cow, "Cheese", "sr"), 3) == 0.081
    assert round(stream_df(cow, "Cheese"), 3) == 0.302
    assert round(stream_df(cow, "Cheese", "limit"), 3) == 0.516
    assert round(stream_df(cow, "Fluid milk"), 3) == 0.103
    assert round(stream_df(cow, "Whey protein"), 3) == 0.018
    assert round(stream_df(cow, "Whey protein", "limit"), 3) == 0.031
    assert round(df(cow, "WPC 80"), 3) == 0.010
    assert round(df(cow, "WPI"), 3) == 0.008
    assert round(cow.DF_bundle(cow.eps_s_lr), 3) == 0.584


def test_dairy_factors_version_1_valuation():
    # theta = 1 (all of the premium is milk value) reproduces version 1.0's factors
    v1 = params.dairy("2026", theta=1.0)
    assert round(stream_df(v1, "Cheese"), 3) == 0.282
    assert round(stream_df(v1, "Whey protein"), 3) == 0.032
    assert round(stream_df(v1, "Whey protein", "limit"), 3) == 0.056
    assert round(v1.DF_bundle(v1.eps_s_lr), 3) == 0.575
    assert round(params.dairy("2019", theta=1.0).DF_stream("Whey protein", 0.9), 3) == 0.008


def test_whey_protein_at_2019_prices():
    old = params.dairy("2019")
    assert round(old.DF_stream("Whey protein", old.eps_s_lr), 3) == 0.004


def test_theta_zero_values_whey_protein_at_other_solids():
    b = params.dairy("2026", theta=0.0)
    p_os = (0.6694 - 0.2668) * 1.03
    assert b.sub("WPC 80 (whey protein concentrate)").price == pytest.approx(0.80 * p_os)
    assert b.sub("WPI (whey protein isolate)").price == pytest.approx(0.90 * p_os)
    assert b.get("Whey protein").floor_ratio == pytest.approx(1.0)


def test_cheese_to_whey_ratio_is_the_same_at_every_horizon(cow):
    ratios = [stream_df(cow, "Cheese", h) / stream_df(cow, "Whey protein", h) for h in ("sr", "lr", "limit")]
    assert max(ratios) - min(ratios) < 1e-9
    assert 16.5 < ratios[0] < 17.0


def test_egg_factors(hen):
    assert round(stream_df(hen, "Shell eggs"), 3) == 0.458
    assert round(stream_df(hen, "Shell eggs", "limit"), 2) == 0.68
    assert round(stream_df(hen, "Whole egg products"), 3) == 0.138
    assert round(stream_df(hen, "Egg white"), 3) == 0.030
    assert round(stream_df(hen, "Egg white", "limit"), 3) == 0.044
    assert round(hen.DF_bundle(hen.eps_s_lr), 3) == 0.673


def test_value_shares(cow, hen):
    share = {r["sub"]: r["share_total"] for r in cow.results(cow.eps_s_lr)}
    assert round(share["Cheese (cheddar-equivalent)"], 3) == 0.432
    assert round(sum(v for k, v in share.items() if k.startswith(("WPC 80", "WPI"))), 3) == 0.070
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
