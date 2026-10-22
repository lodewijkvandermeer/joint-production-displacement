"""Per-unit outputs: how many animals leave production per kilogram of an animal product displaced.

For product i of an animal (model unit = one cwt of milk, one dozen eggs, one bird, ...):

  animal units removed per unit of i displaced   u_i = DF_i / Q_i            (DF_i: the market-share factor)
  naive rule                                     n_i = 1 / Y_i              (Y_i: yield of i if the whole raw commodity,
                                                                             or for a fixed product the animal, went to i)
  discount                                       D_i = u_i / n_i = DF_i Y_i / Q_i
  multiplier                                     M_i = 1 / D_i  = animals' worth of i displaced per animal removed

  animals per tonne of i                         u_i x animals_per_unit / (kg per unit of i / 1000)
  raw commodity per kg of i                      u_i x raw_kg_per_unit / kg per unit of i
  per tonne of protein                           animals per tonne / protein content

All of these are marginal: they hold for small shares of a market. The whole-market average (a perfect substitute takes
the product's whole market, solved exactly with floors and route exits) is reported per stream from full_loss.json:
  M_avg = (naive animal units for today's whole stream) / |change in animal units|.

The figures are per kilogram of animal product displaced. Per kilogram of a new product, multiply by the substitution
ratio (kg of animal product it displaces per kg sold), which the model does not estimate: see per_kg_of_new_product().

Summing u_i x Q_i over every product of an animal gives the bundle factor (the share of the animals removed if every
product is given up in proportion), and 1 in the constant-cost limit; tests/test_per_unit.py checks this identity.
"""
import json
import math

from . import params
from .paths import RESULTS, TABLES

INF = float("inf")
HORIZONS = (("sr", "eps_s_sr"), ("lr", "eps_s_lr"), ("limit", None))
STEP_LABELS = {
    "within_stream": "value relative to physical share within the stream",
    "route_share": "joint products keep earning (value share in the route)",
    "route_elas": "own buyers' price response relative to the route",
    "animal_share": "the animal's other income keeps earning (value share at the animal)",
    "animal_elas": "price response relative to the animal's average",
    "horizon": "buyers of all the animal's products absorb part (horizon)",
}

# headline rows: (branch key, sub-product, label)
PICKS = [
    ("dairy_2026", "Fluid milk (Class I)", "Fluid milk"),
    ("dairy_2026", "Cheese (cheddar-equivalent)", "Cheese"),
    ("dairy_2026", "Butter / cream (3.5 lb fat per cwt)", "Butter"),
    ("dairy_2026", "Nonfat dry milk / SMP (also the casein route)", "Nonfat dry milk (casein route)"),
    ("dairy_2026", "WPC 80 (whey protein concentrate)", "WPC 80 (2026 prices)"),
    ("dairy_2026", "WPI (whey protein isolate)", "WPI (2026 prices)"),
    ("dairy_2019", "WPI (whey protein isolate)", "WPI (2019-21 prices)"),
    ("dairy_2026", "Cull cows (manufacturing beef)", "Cull-cow beef"),
    ("eggs_2019-21", "Shell eggs (table)", "Shell eggs"),
    ("eggs_2019-21", "Liquid/frozen whole egg", "Whole liquid egg"),
    ("eggs_2019-21", "Liquid egg yolk", "Separated egg yolk"),
    ("eggs_2019-21", "Liquid egg white (albumen): liquid, dried albumen, protein fractions", "Separated egg white (liquid)"),
    ("eggs_2025", "Liquid egg white (albumen): liquid, dried albumen, protein fractions", "Separated egg white (2025 prices)"),
    ("broiler", "Boneless skinless breast (fillets, whole-muscle nuggets)", "Chicken breast"),
    ("broiler", "Leg quarters / dark meat (whole legs)", "Chicken dark meat"),
    ("broiler", "Backs, necks, frames -> mechanically separated chicken (MSC nuggets, hot dogs)", "Mechanically separated chicken"),
    ("beef", "Middle meats: steaks and roasts from rib and loin", "Beef middle meats"),
    ("beef", "Grinding material: trim and ground chuck/round (minced beef)", "Beef grinding material"),
    ("pork", "Loin (chops, roasts)", "Pork loin"),
    ("pork", "Picnic, jowl, neck bones, trim -> sausage, ground pork", "Pork sausage material"),
    ("salmon", "Salmon HOG, fillets and portions", "Farmed salmon"),
    ("pollock", "Fillet blocks and fillets (fish fingers, portions)", "Pollock fillets (quota)"),
]

# products sold as a processed form of a modelled product: (branch key, base sub, label, kg of base per kg, protein)
EQUIVALENTS = [
    ("eggs_2019-21", "Liquid egg white (albumen): liquid, dried albumen, protein fractions", "Dried egg white (albumen powder)", 7.5, 0.81),
]
EQUIV_NOTE = ("Dried egg white: 7.5 kg of liquid white per kg of powder [E] (liquid white about 12.4% solids, powder about "
              "93%; USDA FoodData Central), protein 81% [S]; the liquid-white figures times 7.5, i.e. assuming the powder's "
              "price moves with the liquid white it is made from.")


def _branch(key):
    return next(b for b in params.ALL if b.key == key)


def _eps(br, h):
    attr = dict(HORIZONS)[h]
    return INF if attr is None else getattr(br, attr)


def per_kg_of_new_product(br, sub, eps_s, substitution_ratio=1.0):
    """Animals removed per tonne of a NEW product sold, given kg of `sub` it displaces per kg sold."""
    s = br.sub(sub)
    return substitution_ratio * br.units_per_qty(sub, eps_s) * br.animals_per_unit / (s.kg / 1000.0)


def sub_record(br, name, mc=None, full=None):
    s = br.sub(name)
    rec = dict(sub=name, stream=s.stream, qty=s.qty, kg_per_qty=s.kg, protein=s.protein, naive_yield=br.naive_yield(name),
               animal_label=br.animal_label, raw_label=br.raw_label, horizons={})
    for h, _ in HORIZONS:
        e = _eps(br, h)
        if br.key == "pollock" and h == "limit":
            rec["horizons"][h] = None          # quota-managed: no constant-cost limit
            continue
        if e is not None and e != INF and e <= 0:
            rec["horizons"][h] = dict(DF=0.0, D=0.0, M=None, animals_per_t=0.0, raw_kg_per_kg=0.0, animals_per_t_protein=0.0, steps=None)
            continue
        u = br.units_per_qty(name, e)
        D = br.discount(name, e)
        st = br.steps(name, e)
        d = dict(DF=br.DF_sub(name, e), D=D, M=(1 / D if D > 0 else None), units_per_qty=u, steps=st, grouped=grouped_steps(st))
        if s.kg:
            d["animals_per_t"] = u * br.animals_per_unit / (s.kg / 1000.0)
            d["raw_kg_per_kg"] = u * br.raw_kg_per_unit / s.kg
            d["animals_per_t_protein"] = d["animals_per_t"] / s.protein if s.protein else None
        rec["horizons"][h] = d
    if mc is not None and rec["horizons"]["lr"] and rec["horizons"]["lr"]["DF"] > 0:
        lr = rec["horizons"]["lr"]
        c = lr["D"] / lr["DF"]           # D, M and the per-kg figures are the factor times a constant
        lo, hi = mc["lr"]["p10"], mc["lr"]["p90"]
        rng = dict(D=(c * lo, c * hi), M=(1 / (c * hi), 1 / (c * lo) if lo > 0 else None))
        if s.kg:
            k = lr["animals_per_t"] / lr["DF"]
            rng["animals_per_t"] = (k * lo, k * hi)
        rec["lr_range"] = rng
    return rec


def naive_stream(br, stream):
    """Animal units the naive rule attributes to today's whole stream: 1 for a stream fixed to the animal (all of it
    comes from every animal); for a routed stream, the sum over its products of quantity / naive yield."""
    if br.is_fixed(stream):
        return 1.0
    return sum(s.qty / br.naive_yield(s.name) for s in br.subs if s.stream == stream)


def stream_multiplier(br, stream, eps_s):
    """Multiplier for a whole stream at the margin: naive animal units for the stream / its market-share factor."""
    d = br.DF_stream(stream, eps_s)
    return naive_stream(br, stream) / d if d > 0 else None


def stream_whole_market(br, stream, full):
    """Average multiplier when a perfect substitute takes the stream's whole market (exact model, full_loss.json)."""
    naive = naive_stream(br, stream)
    out = {}
    for h in ("SR", "LR", "limit"):
        if br.key == "pollock" and h == "limit":
            out[h] = None
            continue
        A = full[stream][h]["A"]
        out[h] = dict(A=A, naive=naive, M=(naive / -A if A < 0 else None))
    return out


def build(results=RESULTS):
    mc = json.load(open(results / "mc_results.json"))
    full = json.load(open(results / "full_loss.json"))
    out = {}
    for br in params.ALL:
        out[br.key] = dict(name=br.name, animal_label=br.animal_label, animals_per_unit=br.animals_per_unit,
                           animals_src=br.animals_src, raw_label=br.raw_label, raw_kg_per_unit=br.raw_kg_per_unit,
                           bundle={h: (br.DF_bundle(_eps(br, h)) if _eps(br, h) and _eps(br, h) > 0 else 0.0) for h, _ in HORIZONS},
                           subs={s.name: sub_record(br, s.name, mc[br.key].get(s.name)) for s in br.subs},
                           streams={k.name: stream_whole_market(br, k.name, full[br.key]) for k in br.streams})
    return out


# ---------------------------------------------------------------- formatting
M_ = "−"


def fm(m):
    """Multiplier for display."""
    if m is None:
        return "none"
    if m >= 100:
        return f"{m:,.0f}"
    if m >= 10:
        return f"{m:.0f}"
    return f"{m:.1f}"


def fsig(v, n=2):
    if v is None:
        return "n/a"
    if v == 0:
        return "0"
    d = max(0, n - 1 - int(math.floor(math.log10(abs(v)))))
    return f"{v:,.{d}f}"


def headline_table(P):
    lines = ["| Product | Animals' worth displaced per animal removed: within a year | 3–5 years (80% range) | constant-cost limit | "
             "whole market lost, 3–5 years | Animals per tonne displaced, 3–5 years | Raw commodity per kg, 3–5 years | "
             "Animals per tonne of protein, 3–5 years |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for key, sub, label in PICKS:
        b = P[key]; r = b["subs"][sub]; h = r["horizons"]
        sr, lr, lim = h["sr"], h["lr"], h["limit"]
        rng = r.get("lr_range", {}).get("M")
        lr_txt = fm(lr["M"]) + (f" ({fm(rng[0])}–{fm(rng[1])})" if rng and rng[1] else "")
        wm = b["streams"][r["stream"]]["LR"]
        n_in_stream = sum(1 for x in b["subs"].values() if x["stream"] == r["stream"])
        wm_txt = fm(wm["M"]) + (" (whole stream)" if n_in_stream > 1 else "") if wm else "n/a"
        apt = f"{fsig(lr.get('animals_per_t'), 3)} {b['animal_label']}" if lr.get("animals_per_t") is not None else "n/a"
        raw = f"{fsig(lr.get('raw_kg_per_kg'), 2)} {b['raw_label']}" if lr.get("raw_kg_per_kg") is not None else "n/a"
        prot = fsig(lr.get("animals_per_t_protein"), 3) if lr.get("animals_per_t_protein") else ""
        lines.append(f"| {label} | {fm(sr['M'])} | {lr_txt} | {fm(lim['M']) if lim else 'n/a'} | {wm_txt} | {apt} | {raw} | {prot} |")
    for key, sub, label, f, prot in EQUIVALENTS:
        b = P[key]; lr = b["subs"][sub]["horizons"]["lr"]; sr = b["subs"][sub]["horizons"]["sr"]; lim = b["subs"][sub]["horizons"]["limit"]
        apt = lr["animals_per_t"] * f
        lines.append(f"| {label} | {fm(sr['M'])} | {fm(lr['M'])} | {fm(lim['M'])} | | {fsig(apt, 3)} {b['animal_label']} | "
                     f"{fsig(lr['raw_kg_per_kg'] * f, 2)} {b['raw_label']} | {fsig(apt / prot, 3)} |")
    return "\n".join(lines)


def all_products_table(P):
    lines = []
    for key, b in P.items():
        lines += [f"### {b['name']}", "",
                  f"Animals: {b['animal_label']} ({b['animals_src']}). Raw commodity: {b['raw_label']}.", "",
                  "| Product | Multiplier, within a year | 3–5 years | constant-cost limit | Animals per tonne, 3–5 years | Raw per kg, 3–5 years |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for name, r in b["subs"].items():
            h = r["horizons"]
            apt = fsig(h["lr"].get("animals_per_t"), 3) if h["lr"].get("animals_per_t") is not None else "n/a"
            raw = fsig(h["lr"].get("raw_kg_per_kg"), 2) if h["lr"].get("raw_kg_per_kg") is not None else "n/a"
            lines.append(f"| {name} | {fm(h['sr']['M'])} | {fm(h['lr']['M'])} | {fm(h['limit']['M']) if h['limit'] else 'n/a'} | {apt} | {raw} |")
        lines.append("")
    return "\n".join(lines)


def write_json(results=RESULTS, out_dir=None):
    """results/per_unit.json (needs mc_results.json and full_loss.json in `results`)."""
    P = build(results)
    with open((out_dir or results) / "per_unit.json", "w") as f:
        json.dump(P, f, indent=0)
    return P


def write_tables(results=RESULTS, out_dir=TABLES):
    P = build(results)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "per_kg.md").write_text(headline_table(P) + "\n\n" + EQUIV_NOTE + "\n")
    (out_dir / "per_kg_all.md").write_text(all_products_table(P))
    (out_dir / "theta.md").write_text(theta_table() + "\n")
    (out_dir / "steps.md").write_text("Three to five years:\n\n" + steps_table("lr") + "\n\nConstant-cost limit:\n\n" + steps_table("limit") + "\n")
    return P


# ---------------------------------------------------------------- whey protein valuation sensitivity
THETAS = (0.0, 0.5, 1.0)
THETA_SUBS = [("WPC 80 (whey protein concentrate)", "WPC 80"), ("WPI (whey protein isolate)", "WPI"),
              ("Cheese (cheddar-equivalent)", "Cheese")]


def theta_table():
    """Multipliers and animals per tonne of protein for whey protein and cheese at theta = 0, 0.5, 1 (closed form)."""
    lines = ["| Prices | Product | Share of the premium valued as milk (theta) | Whey protein share of the cow's value | "
             "Multiplier: within a year | 3–5 years | constant-cost limit | Cow-years per tonne of protein, 3–5 years |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for sc, label in (("2026", "2026"), ("2019", "2019–21")):
        for sub, name in THETA_SUBS:
            for th in THETAS:
                b = params.dairy(sc, th)
                share = b.stream_value("Whey protein") / b.total()
                s = b.sub(sub)
                apt = b.units_per_qty(sub, b.eps_s_lr) * b.animals_per_unit / (s.kg / 1000.0) / s.protein
                lines.append(f"| {label} | {name} | {th:g} | {share:.1%} | {fm(b.multiplier(sub, b.eps_s_sr))} | "
                             f"{fm(b.multiplier(sub, b.eps_s_lr))} | {fm(b.multiplier(sub, INF))} | {fsig(apt, 3)} |")
    return "\n".join(lines)


# ---------------------------------------------------------------- the discount, step by step
def grouped_steps(steps):
    """The six model-level factors grouped into the three that carry the argument:
      value_share     the product's share of the value of everything made alongside it from the same raw material
                      (within-stream value x share in the route x the raw commodity's or stream's share of the animal):
                      the long-run rule when all buyers respond alike
      price_response  how this product's buyers respond to price relative to the others (route and animal levels)
      horizon         the part not absorbed by buyers of all the animal's products before supply adjusts"""
    v = steps["within_stream"] * steps.get("route_share", 1.0) * steps["animal_share"]
    e = steps.get("route_elas", 1.0) * steps["animal_elas"]
    return dict(value_share=v, price_response=e, horizon=steps["horizon"])


def steps_table(horizon="lr"):
    lines = ["| Product | Value relative to physical share in its stream | Share of the route's value (joint products) | "
             "Own buyers' response relative to the route | Raw commodity's (or part's) share of the animal | "
             "Response relative to the animal's average | Horizon: not absorbed by other buyers | Discount (product) | "
             "Multiplier | Value-share rule alone (1 / value share) |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    f = lambda v: "" if v is None else f"{v:.3f}"  # noqa: E731
    for key, sub, label in PICKS:
        br = _branch(key)
        e = _eps(br, horizon)
        if e is not None and e != INF and e <= 0:
            continue
        st = br.steps(sub, e)
        g = grouped_steps(st)
        D = math.prod(st.values())
        lines.append(f"| {label} | {f(st['within_stream'])} | {f(st.get('route_share'))} | {f(st.get('route_elas'))} | "
                     f"{f(st['animal_share'])} | {f(st['animal_elas'])} | {f(st['horizon'])} | {D:.4f} | {fm(1 / D)} | {fm(1 / g['value_share'])} |")
    return "\n".join(lines)
