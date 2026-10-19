"""Price-cap (perfect substitute) and full-loss scenarios on the exact model: the three regimes.

Regime 1: marginal displacement (DF, from edm_model). Regime 2: a perfect substitute for ONE stream at price pi x today's.
Regime 3: a perfect substitute for EVERY product of the animal at pi x today's (A = pi^eps_s; -100% in the constant-cost limit).

Outputs (written by main()):
  exit_results.json  price caps at 90/75/50/25/10% of today's price (and at the floor), 3-5 years and constant-cost limit
  full_loss.json     each product's market lost (cap at its floor price, or at ~0 where there is none), three horizons
  exit_curves.json   cap curves in 5-point steps for the figure, and the route exit prices (fluid milk, shell eggs, whole egg)
"""
import json

from . import params, exact_model as X
from .paths import RESULTS

CAPS = [0.9, 0.75, 0.5, 0.25, 0.10]
BRANCHES = [params.dairy("2026"), params.dairy("2019"), params.beef(), params.eggs("2019-21"), params.eggs("2025"),
            params.broiler(), params.pork(), params.pollock(), params.salmon()]


def run_branch(br):
    ex = X.exact_for(br)
    rows = []
    for k in ex.streams:
        phi = ex.phi[k]
        caps = [c for c in CAPS if c > phi + 1e-9] + ([phi] if phi > 0 else [])
        for horizon, kw in (("LR", dict(eps_s=br.eps_s_lr)), ("limit", dict(constant_cost=True))):
            if horizon == "LR" and br.eps_s_lr == 0:
                kw = dict(eps_s=1e-9)
            for c in caps:
                res = ex.solve(cap={k: c}, **kw)
                Qk = res["Q"][k]
                others = {j: res["P"][j] for j in ex.streams if j != k}
                rows.append(dict(branch=br.key, stream=k, horizon=horizon, cap=c, A=res["A"] - 1.0, Q_k=Qk - 1.0,
                                 price_k=res["P"][k], sub_volume=res["sub"][k], sub_share=res["sub_share"][k],
                                 outlet=res["outlet"][k], PA=res["PA"] - 1.0,
                                 route_q={r: q for r, q in res["q"].items()},
                                 max_other_price=max(others.values()) if others else None,
                                 others=others))
    # regime 3: whole bundle capped
    for horizon in ("LR", "limit"):
        for c in CAPS:
            A = c ** br.eps_s_lr - 1.0 if horizon == "LR" else -1.0
            rows.append(dict(branch=br.key, stream="ALL PRODUCTS", horizon=horizon, cap=c, A=A, Q_k=A, price_k=c, sub_volume=None, sub_share=None,
                             outlet=None, PA=c - 1.0, route_q={}, max_other_price=None, others={}))
    return rows


def full_loss():
    """Each product's whole market lost: a perfect substitute at the stream's floor price (or ~0 where it has none)."""
    out = {}
    for br in BRANCHES:
        ex = X.exact_for(br)
        d = {}
        for k in ex.streams:
            cap = max(ex.phi[k], 1e-6)
            e = {"cap": cap}
            horizons = (("SR", dict(eps_s=br.eps_s_sr if br.eps_s_sr > 0 else 1e-9)),
                        ("LR", dict(eps_s=br.eps_s_lr if br.eps_s_lr > 0 else 1e-9)),
                        ("limit", dict(constant_cost=True)))
            for h, kw in horizons:
                r = ex.solve(cap={k: cap}, **kw)
                others = {j: r["P"][j] for j in ex.streams if j != k}
                am = max(others, key=others.get) if others else None
                e[h] = dict(A=r["A"] - 1, P_k=r["P"][k], Q_k=r["Q"][k] - 1, sub_share=r["sub_share"][k],
                            max_other=others[am] if am else None, argmax_other=am, routes=dict(r["q"]))
            d[k] = e
        out[br.key] = d
    return out


CURVE_STREAMS = {
    "dairy_2026": ["Cheese", "Fluid milk", "Whey protein", "Butter (fat)", "Milk powder (nonfat solids)"],
    "beef": ["Middle meats (whole cut)", "Minced beef (grinding material)"],
    "eggs_2019-21": ["Shell eggs", "Whole egg products", "Egg white"],
    "broiler": ["Breast meat", "Dark meat", "Backs & necks (MSC)"],
    "pork": ["Fresh pork cuts", "Ham", "Belly", "Sausage & trim"],
    "salmon": ["Salmon flesh"],
    "pollock": ["Flesh (fillets, surimi, mince)"],
}


def curves():
    out = []
    for br in BRANCHES:
        if br.key not in CURVE_STREAMS:
            continue
        ex = X.exact_for(br)
        for k in CURVE_STREAMS[br.key]:
            phi = ex.phi[k]
            for c in [x / 100 for x in range(100, 4, -5)] + ([phi] if phi > 0 else []):
                if c < phi - 1e-9:
                    continue
                for horizon, kw in (("LR", dict(eps_s=br.eps_s_lr if br.eps_s_lr > 0 else 1e-9)), ("limit", dict(constant_cost=True))):
                    res = ex.solve(cap={k: c}, **kw)
                    out.append(dict(branch=br.key, stream=k, horizon=horizon, cap=c, A=res["A"] - 1, Q_k=res["Q"][k] - 1, sub_share=res["sub_share"][k]))
    return out


def route_exit_prices(verbose=False):
    """Cap at which a single-stream fungible route receives no raw commodity (3-5 years and constant-cost limit)."""
    out = []
    for br in BRANCHES:
        ex = X.exact_for(br)
        for r in ex.fung:
            ks = [k for k in ex.streams if ex.route_of[k] == r]
            if len(ks) != 1:
                continue
            k = ks[0]
            for horizon, kw in (("LR", dict(eps_s=br.eps_s_lr)), ("limit", dict(constant_cost=True))):
                lo, hi = 0.01, 1.0
                for _ in range(40):
                    m = 0.5 * (lo + hi)
                    res = ex.solve(cap={k: m}, **kw)
                    if res["Q"][k] < 1e-6:
                        lo = m
                    else:
                        hi = m
                out.append(dict(branch=br.key, stream=k, horizon=horizon, exit_cap=0.5 * (lo + hi)))
                if verbose:
                    print(f"route exit {br.key} {k} {horizon}: cap {0.5*(lo+hi):.3f}")
    return out


def main(out_dir=RESULTS, verbose=False):
    out_dir.mkdir(parents=True, exist_ok=True)
    allrows = []
    for br in BRANCHES:
        rs = run_branch(br)
        allrows += rs
        if verbose:
            print("==", br.name)
            for r in rs:
                if r["horizon"] == "LR" or r["cap"] in (0.5, 0.10) or r["stream"] == "ALL PRODUCTS":
                    print(f"  {r['stream'][:26]:26s} {r['horizon']:5s} cap {r['cap']:.2f}: A {r['A']:+.3f}  Q_k {r['Q_k']:+.3f}")
    json.dump(allrows, open(out_dir / "exit_results.json", "w"), indent=0, default=float)
    json.dump(full_loss(), open(out_dir / "full_loss.json", "w"), indent=0, default=float)
    cv = curves()
    rx = route_exit_prices(verbose)
    json.dump(dict(curves=cv, route_exit=rx), open(out_dir / "exit_curves.json", "w"), indent=0, default=float)


if __name__ == "__main__":
    main(verbose=True)
