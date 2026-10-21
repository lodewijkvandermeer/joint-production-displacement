import pytest

from jpdm import params
from jpdm.params import _Names


def ev(expr, **names):
    return _Names(names).value(expr)


def test_expression_arithmetic_and_names():
    assert ev("a*2+1", a=3) == 7
    assert ev("-a**2", a=3) == -9
    assert ev("b", a=2, b="a*5") == 10          # names resolve lazily, in any order


@pytest.mark.parametrize("bad", ["__import__('os')", "a.real", "[1]", "'x'", "a if 1 else 2", "abs(1)", "True", "1 < 2"])
def test_unsafe_expressions_rejected(bad):
    with pytest.raises(ValueError):
        ev(bad, a=1)


def test_unknown_and_circular_names():
    with pytest.raises(ValueError, match="unknown"):
        ev("nope")
    with pytest.raises(ValueError, match="circular"):
        ev("a", a="b", b="a")


def test_total_value_only_when_available():
    with pytest.raises(ValueError, match="total_value"):
        ev("total_value()")


def test_scenarios_differ_and_default():
    assert params.dairy().key == params.dairy("2026").key
    assert params.dairy("2019").key != params.dairy("2026").key
    assert params.dairy("2019").subs != params.dairy("2026").subs
    assert params.eggs().key == params.eggs("2019-21").key


def test_unknown_scenario_rejected():
    with pytest.raises(ValueError):
        params.dairy("1999")
    with pytest.raises(ValueError):
        params.load("beef", "2026")


def test_every_parameter_file_is_loaded():
    from jpdm.paths import PARAMS
    used = {"dairy", "eggs", "beef", "broiler", "pork", "pollock", "salmon"}
    assert {p.stem for p in PARAMS.glob("*.toml")} == used
    assert len(params.ALL) == 9


def test_every_stream_has_explicit_basis():
    for br in params.ALL:
        assert all(st.basis in ("S", "A") and st.elas_src.startswith(f"[{st.basis}]") for st in br.streams)


def test_malformed_elas_tag_is_an_error():
    with pytest.raises(ValueError, match=r"\[S\] or \[A\]"):
        params._basis("x", {"name": "s", "elas_src": "Source: Andreyeva"})


def test_every_animal_has_supply_spread():
    for br in params.ALL:
        assert "supply_sigma_lr" in br.monte_carlo or "supply_lr_uniform" in br.monte_carlo
