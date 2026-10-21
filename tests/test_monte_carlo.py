import numpy as np

from jpdm import monte_carlo, params


def test_run_is_reproducible_with_local_generator():
    cfg = dict(monte_carlo.settings(), n=20)
    br = params.beef()
    a = monte_carlo.run(br, np.random.default_rng(1), cfg)
    b = monte_carlo.run(br, np.random.default_rng(1), cfg)
    assert a == b


def test_draw_does_not_mutate_input():
    br = params.beef()
    before = [s.elas for s in br.streams]
    monte_carlo.draw_branch(br, np.random.default_rng(1), monte_carlo.settings())
    assert [s.elas for s in br.streams] == before


def test_short_run_supply_never_exceeds_long_run():
    cfg = monte_carlo.settings()
    rng = np.random.default_rng(7)
    for br in params.ALL:
        for _ in range(500):
            _, es_sr, es_lr = monte_carlo.draw_branch(br, rng, cfg)
            assert es_sr <= es_lr
