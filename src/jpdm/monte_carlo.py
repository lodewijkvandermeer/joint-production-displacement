"""Monte Carlo ranges for displacement factors: sample stream demand elasticities and supply elasticities over
literature ranges ([S] streams: lognormal sigma 0.25 on |eps|; [A] streams: sigma 0.45; supply: branch-specific).
Value shares (prices) are held at the scenario snapshot; the 2019/2025 scenarios show that sensitivity separately."""
import copy, json, math
import numpy as np
from . import params
from .paths import RESULTS, MC_SETTINGS


def settings():
    with open(MC_SETTINGS, "rb") as f:
        return params.tomllib.load(f)


def draw_branch(br, rng, cfg):
    b = copy.deepcopy(br)
    for st in b.streams:
        sigma = cfg["sigma_demand_sourced"] if st.basis == "S" else cfg["sigma_demand_assumed"]
        st.elas = -abs(st.elas) * math.exp(rng.normal(0.0, sigma))
    mc = br.monte_carlo
    if "supply_lr_uniform" in mc:   # e.g. pollock: quota-managed capture
        es_lr = rng.uniform(*mc["supply_lr_uniform"]); es_sr = 0.0
    else:
        # long-run supply cannot be less elastic than short-run: redraw the pair until it is ordered
        while True:
            es_lr = br.eps_s_lr * math.exp(rng.normal(0.0, mc["supply_sigma_lr"]))
            es_sr = br.eps_s_sr * math.exp(rng.normal(0.0, cfg["sigma_supply_sr"]))
            if es_sr <= es_lr:
                break
    return b, es_sr, es_lr


def run(br, rng, cfg=None):
    cfg = cfg or settings()
    n = cfg["n"]
    subs = [s.name for s in br.subs]
    out = {s: {"sr": [], "lr": [], "lim": []} for s in subs}
    bundle = {"sr": [], "lr": []}
    for _ in range(n):
        b, es_sr, es_lr = draw_branch(br, rng, cfg)
        rs = b.results(es_sr) if es_sr > 0 else None
        rl = b.results(es_lr) if es_lr > 0 else None
        for i, s in enumerate(subs):
            out[s]["sr"].append(rs[i]["DF"] if rs else 0.0)
            out[s]["lr"].append(rl[i]["DF"] if rl else 0.0)
            out[s]["lim"].append(rl[i]["DF_limit"] if rl else b.results(1.0)[i]["DF_limit"])
        bundle["sr"].append(b.DF_bundle(es_sr) if es_sr > 0 else 0.0)
        bundle["lr"].append(b.DF_bundle(es_lr) if es_lr > 0 else 0.0)
    def pct(x):
        a = np.array(x); return dict(p10=float(np.percentile(a, 10)), p50=float(np.percentile(a, 50)), p90=float(np.percentile(a, 90)))
    res = {s: {h: pct(v) for h, v in d.items()} for s, d in out.items()}
    res["__bundle__"] = {h: pct(v) for h, v in bundle.items()}
    return res


def main(out_dir=RESULTS, verbose=False):
    cfg = settings()
    # One generator shared by all animals, in params.ALL order, so a given seed gives the same draws on every run.
    rng = np.random.default_rng(cfg["seed"])
    allres = {}
    for br in params.ALL:
        r = run(br, rng, cfg)
        allres[br.key] = r
        if not verbose:
            continue
        print("==", br.name, "bundle LR p10/p50/p90", {k: round(v, 3) for k, v in r["__bundle__"]["lr"].items()})
        base = {x["sub"]: x for x in br.results(br.eps_s_lr)}
        for s, d in r.items():
            if s == "__bundle__": continue
            print(f"  {s[:40]:40s} point {base[s]['DF']:.4f}  LR p10 {d['lr']['p10']:.4f} p50 {d['lr']['p50']:.4f} p90 {d['lr']['p90']:.4f} | limit p10 {d['lim']['p10']:.3f} p90 {d['lim']['p90']:.3f} | SR p10 {d['sr']['p10']:.4f} p90 {d['sr']['p90']:.4f}")
    with open(out_dir / "mc_results.json", "w") as f:
        json.dump(allres, f, indent=0)
    return allres
