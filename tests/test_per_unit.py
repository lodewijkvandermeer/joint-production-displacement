"""Per-unit outputs: identities that must hold by construction, and the headline multipliers."""
import json
import math

import pytest

from jpdm import params, per_unit
from jpdm.paths import RESULTS

INF = float("inf")


def _horizons(br):
    hs = [br.eps_s_lr, INF]
    if br.eps_s_sr > 0:
        hs.append(br.eps_s_sr)
    return hs


@pytest.mark.parametrize("br", params.ALL, ids=lambda b: b.key)
def test_animals_removed_add_up_to_the_bundle_factor(br):
    # units removed per unit displaced, times today's quantity, summed over every product = bundle factor (1 in the limit)
    for e in _horizons(br):
        total = sum(br.units_per_qty(s.name, e) * s.qty for s in br.subs)
        assert total == pytest.approx(br.DF_bundle(e), rel=1e-12)
    assert sum(br.units_per_qty(s.name, INF) * s.qty for s in br.subs) == pytest.approx(1.0, rel=1e-12)


@pytest.mark.parametrize("br", params.ALL, ids=lambda b: b.key)
def test_steps_multiply_to_the_discount(br):
    for e in _horizons(br):
        for s in br.subs:
            assert math.prod(br.steps(s.name, e).values()) == pytest.approx(br.discount(s.name, e), rel=1e-12)


@pytest.mark.parametrize("br", params.ALL, ids=lambda b: b.key)
def test_naive_rule_reduces_to_the_simple_cases(br):
    for s in br.subs:
        single = sum(1 for x in br.subs if x.stream == s.stream) == 1
        if br.is_fixed(s.stream):      # fixed to the animal: the discount is the market-share factor itself
            assert br.discount(s.name, br.eps_s_lr) == pytest.approx(br.DF_sub(s.name, br.eps_s_lr), rel=1e-12)
        elif single:                   # its own stream on a route: discount = factor / raw-volume share of the route
            a = br.a(br.get(s.stream).route)
            assert br.discount(s.name, br.eps_s_lr) == pytest.approx(br.DF_sub(s.name, br.eps_s_lr) / a, rel=1e-12)


def test_discounts_are_at_most_one_in_the_limit():
    # no product removes more animals than the naive rule attributes to it
    for br in params.ALL:
        for s in br.subs:
            assert br.discount(s.name, INF) <= 1.0 + 1e-9


def test_substitution_ratio_scales_linearly():
    cow = params.dairy("2026")
    base = per_unit.per_kg_of_new_product(cow, "Cheese (cheddar-equivalent)", cow.eps_s_lr)
    assert per_unit.per_kg_of_new_product(cow, "Cheese (cheddar-equivalent)", cow.eps_s_lr, 0.6) == pytest.approx(0.6 * base)


def test_conversions_are_set_for_every_animal():
    for br in params.ALL:
        assert br.animals_per_unit and br.raw_kg_per_unit and br.animal_label and br.raw_label


def test_headline_multipliers():
    cow, hen, bro, steer = params.dairy("2026"), params.eggs("2019-21"), params.broiler(), params.beef()
    M = lambda b, s, e: b.multiplier(s, e)  # noqa: E731
    assert M(cow, "Cheese (cheddar-equivalent)", cow.eps_s_lr) == pytest.approx(1.99, abs=0.01)
    assert M(cow, "Cheese (cheddar-equivalent)", INF) == pytest.approx(1.16, abs=0.01)
    assert M(cow, "Fluid milk (Class I)", INF) == pytest.approx(1.08, abs=0.01)
    assert M(cow, "WPI (whey protein isolate)", cow.eps_s_lr) == pytest.approx(16.2, abs=0.1)
    assert M(cow, "Cull cows (manufacturing beef)", cow.eps_s_lr) == pytest.approx(45.6, abs=0.3)
    assert M(hen, "Shell eggs (table)", INF) == pytest.approx(1.0, abs=0.01)
    assert M(hen, "Liquid egg white (albumen): liquid, dried albumen, protein fractions", hen.eps_s_lr) == pytest.approx(3.88, abs=0.02)
    assert M(bro, "Backs, necks, frames -> mechanically separated chicken (MSC nuggets, hot dogs)", bro.eps_s_lr) == pytest.approx(353, abs=1)
    assert M(steer, "Grinding material: trim and ground chuck/round (minced beef)", steer.eps_s_lr) == pytest.approx(7.90, abs=0.02)


def test_committed_per_unit_file_matches_the_model():
    P = json.load(open(RESULTS / "per_unit.json"))
    for br in params.ALL:
        for s in br.subs:
            d = P[br.key]["subs"][s.name]["horizons"]["lr"]
            assert d["D"] == pytest.approx(br.discount(s.name, br.eps_s_lr), rel=1e-9)


@pytest.mark.parametrize("br", params.ALL, ids=lambda b: b.key)
def test_grouped_steps_multiply_to_the_discount(br):
    for s in br.subs:
        g = per_unit.grouped_steps(br.steps(s.name, br.eps_s_lr))
        assert math.prod(g.values()) == pytest.approx(br.discount(s.name, br.eps_s_lr), rel=1e-12)


def test_value_share_rule_is_exact_for_fixed_products_with_average_buyers():
    # a carcass part whose buyers respond like the animal's average: the long-run discount is its value share
    hen = params.eggs("2019-21")
    g = per_unit.grouped_steps(hen.steps("Shell eggs (table)", INF))
    assert g["horizon"] == 1.0
    assert hen.multiplier("Shell eggs (table)", INF) == pytest.approx(1 / (g["value_share"] * g["price_response"]))
