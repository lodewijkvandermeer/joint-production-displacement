"""Generate the markdown tables and key numbers for the rewritten paper from the model outputs."""
import json, math
from . import params
from .paths import RESULTS, TABLES

MC = FULL = EXIT = CURV = None


def load(results=RESULTS):
    """Load the model outputs the tables are built from (run the scenarios and Monte Carlo first)."""
    global MC, FULL, EXIT, CURV
    MC = json.load(open(results / "mc_results.json"))
    FULL = json.load(open(results / "full_loss.json"))
    EXIT = json.load(open(results / "exit_results.json"))
    CURV = json.load(open(results / "exit_curves.json"))
M = "−"


def pct(v, d=1):
    if v is None or (isinstance(v, float) and math.isnan(v)): return "n/a"
    s = f"{abs(v)*100:.{d}f}%"
    return (M if v < 0 else "") + s


def pct_auto(v):
    return pct(v, 0) if abs(v) >= 0.10 else pct(v, 1)


def df(v, d=3):
    return f"{v:.{d}f}"


def dfr(v, lo, hi):
    return f"{v:.3f} ({lo:.3f}–{hi:.3f})"


ROWS = {   # display rows per branch: (label, [sub names]) -- combine small sub-products
    "dairy_2026": [("Cheese", ["Cheese (cheddar-equivalent)"]), ("Fluid milk", ["Fluid milk (Class I)"]),
                   ("Nonfat dry milk / SMP (casein route)", ["Nonfat dry milk / SMP (also the casein route)"]),
                   ("Other manufactured (yogurt, ice cream)", ["Other dairy: yogurt, ice cream, etc. (Class II)"]),
                   ("WPC 80", ["WPC 80 (whey protein concentrate)"]), ("WPI", ["WPI (whey protein isolate)"]),
                   ("Butter / cream", ["Butter / cream (3.5 lb fat per cwt)"]), ("Cull cows", ["Cull cows (manufacturing beef)"]),
                   ("Calves", ["Calves (beef-on-dairy, bull calves)"]),
                   ("Dry whey, lactose, permeate", ["Dry whey (sweet whey powder)", "Lactose", "Permeate / condensed whey / feed"])],
    "beef": [("Middle meats (rib, loin steaks and roasts)", ["Middle meats: steaks and roasts from rib and loin"]),
             ("End-meat whole-muscle (chuck, round)", ["End-meat whole-muscle cuts (chuck/round roasts, steaks; 50% of chuck+round)"]),
             ("Grinding material (trim, ground chuck and round)", ["Grinding material: trim and ground chuck/round (minced beef)"]),
             ("Thin-meat whole-muscle (brisket, flank, skirt)", ["Thin-meat whole-muscle (brisket, flank, skirt; 40% of thin meats)"]),
             ("Edible offal", ["Edible offal (tongue, cheek, oxtail, liver, tripe, hearts, lips)"]), ("Tallow and technical fat", ["Tallow and technical fat"]),
             ("Hide", ["Hide"]), ("Meat and bone meal, blood meal", ["Meat & bone meal, blood meal"])],
    "eggs_2019-21": [("Shell eggs", ["Shell eggs (table)"]), ("Whole liquid and frozen egg", ["Liquid/frozen whole egg"]),
                     ("Separated egg white (liquid, dried albumen, protein fractions)", ["Liquid egg white (albumen): liquid, dried albumen, protein fractions"]),
                     ("Separated egg yolk", ["Liquid egg yolk"]), ("Spent hen", ["Spent hen (soup meat, rendering)"])],
    "broiler": [("Boneless skinless breast (fillets, whole-muscle nuggets)", ["Boneless skinless breast (fillets, whole-muscle nuggets)"]), ("Tenders", ["Tenders"]),
                ("Wings", ["Wings"]), ("Whole legs / leg quarters (dark meat)", ["Leg quarters / dark meat (whole legs)"]),
                ("Paws and giblets", ["Giblets", "Paws (export)"]), ("Backs, necks, frames (mechanically separated chicken)", ["Backs, necks, frames -> mechanically separated chicken (MSC nuggets, hot dogs)"]),
                ("Feathers, blood, viscera (rendering)", ["Feathers, blood, viscera, heads -> rendering"])],
    "pork": [("Loin (chops, roasts)", ["Loin (chops, roasts)"]), ("Ham (mostly cured)", ["Ham (mostly cured)"]), ("Belly (bacon)", ["Belly (bacon)"]),
             ("Butt (shoulder, pulled pork)", ["Butt (shoulder)"]), ("Spareribs", ["Spareribs"]),
             ("Picnic, jowl, neck bones, trim (sausage, ground pork)", ["Picnic, jowl, neck bones, trim -> sausage, ground pork"]),
             ("Drop credit (lard, offal, meals, plasma)", ["Drop credit (lard, offal, meals, plasma)"]), ("Feet, tails", ["Feet, tails (export, variety meats)"])],
    "pollock": [("Fillet blocks and fillets (fish fingers, portions)", ["Fillet blocks and fillets (fish fingers, portions)"]),
                ("Surimi (crab sticks) and mince", ["Surimi (crab sticks, kamaboko)", "Mince"]), ("Roe", ["Roe"]),
                ("Fishmeal and fish oil", ["Fishmeal", "Fish oil"]), ("Headed and gutted", ["H&G (headed and gutted)"])],
    "salmon": [("Salmon fillets and portions", ["Salmon HOG, fillets and portions"]), ("By-products (heads, frames, trimmings)", ["By-products (heads, frames, viscera, trimmings) -> oil, meal, pet food"])],
}
ANIMAL = {"dairy_2026": "milk", "beef": "fed cattle", "eggs_2019-21": "hens", "broiler": "broilers", "pork": "hogs", "pollock": "catch", "salmon": "salmon"}
NAMES = {"dairy_2026": "Dairy product", "beef": "Fed steer product", "eggs_2019-21": "Layer product", "broiler": "Broiler product", "pork": "Hog product", "pollock": "Alaska pollock product", "salmon": "Farmed salmon product"}
ALT = {"dairy_2026": "dairy_2019", "eggs_2019-21": "eggs_2025"}
ALT_LABEL = {"dairy_2026": "2019 prices", "eggs_2019-21": "Sep 2025 prices"}


def branch_table(key):
    br = [b for b in params.ALL if b.key == key][0]
    rs = {x["sub"]: x for x in br.results(br.eps_s_sr)}
    rl = {x["sub"]: x for x in br.results(br.eps_s_lr)}
    alt = ALT.get(key)
    bra = [b for b in params.ALL if b.key == alt][0] if alt else None
    rla = {x["sub"]: x for x in bra.results(bra.eps_s_lr)} if bra else None
    mc = MC[key]
    quota = key == "pollock"
    lines = []
    head = [NAMES[key], "Share of animal value", "DF within a year", "DF 3–5 years (80% range)", "DF constant-cost limit"]
    if alt: head.insert(4, f"DF 3–5 years, {ALT_LABEL[key]}")
    head += ["Stream price change for a 10% replacement", f"Change in {ANIMAL[key]} if the product's market is lost: 3–5 years; constant-cost limit"]
    lines.append("| " + " | ".join(head) + " |")
    for label, subs in ROWS[key]:
        share = sum(rs[s]["share_total"] for s in subs)
        dsr = sum(rs[s]["DF"] for s in subs); dlr = sum(rl[s]["DF"] for s in subs); dlim = sum(rl[s]["DF_limit"] for s in subs)
        p10 = sum(mc[s]["lr"]["p10"] for s in subs); p90 = sum(mc[s]["lr"]["p90"] for s in subs)
        eps = [rl[s]["EP_stream_10"] for s in subs]
        ep = pct(eps[0]) if len(subs) == 1 else f"{pct(max(eps))} to {pct(min(eps))}"
        stream = rl[subs[0]]["stream"]
        fl = FULL[key][stream]
        w = sum(rl[s]["w"] for s in subs)
        if stream in ("Spent hen",):
            full = "n/a (no market price)"
        else:
            # full loss of the whole stream scaled by the sub-products' share within the stream if the row is a part of a stream
            a_lr = fl["LR"]["A"]; a_lim = fl["limit"]["A"]
            if abs(w - 1.0) > 1e-6:   # row is a sub-product within a stream (WPC 80 or WPI; giblets/paws etc.): scale linearly within the stream
                a_lr *= w; a_lim *= w
            full = f"{pct_auto(a_lr)}; {('n/a' if quota else pct_auto(a_lim))}" + ("" if abs(w - 1.0) < 1e-6 else " (share of the stream)")
        row = [label, pct(share), df(dsr), dfr(dlr, p10, p90), ("n/a (quota)" if quota else df(dlim))]
        if alt: row.insert(4, df(sum(rla[s]["DF"] for s in subs)))
        row += [ep, full]
        lines.append("| " + " | ".join(row) + " |")
    b = mc["__bundle__"]
    row = ["All products together (bundle)", "100%", df(br.DF_bundle(br.eps_s_sr)), dfr(br.DF_bundle(br.eps_s_lr), b["lr"]["p10"], b["lr"]["p90"]), ("n/a (quota)" if quota else "1.000")]
    if alt: row.insert(4, df(bra.DF_bundle(bra.eps_s_lr)))
    row += ["", ""]
    lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def exit_table():
    """Regime 2: perfect substitute at a share of today's price; animal change in 3-5 years (and limit at 50%)."""
    picks = [("dairy_2026", "Cheese", "Cheese (dairy cow)"), ("dairy_2026", "Fluid milk", "Fluid milk (dairy cow)"), ("dairy_2026", "Whey protein", "Whey protein, WPC 80 and WPI (dairy cow)"),
             ("eggs_2019-21", "Shell eggs", "Shell eggs (laying hen)"), ("eggs_2019-21", "Whole egg products", "Whole liquid egg (laying hen)"), ("eggs_2019-21", "Egg white", "Separated egg white (laying hen)"),
             ("broiler", "Breast meat", "Breast meat and tenders (broiler)"), ("broiler", "Backs & necks (MSC)", "Mechanically separated chicken (broiler)"),
             ("beef", "Middle meats (whole cut)", "Middle meats (fed steer)"), ("beef", "Minced beef (grinding material)", "Grinding material (fed steer)"),
             ("pork", "Fresh pork cuts", "Loin, butt, ribs (hog)"), ("pork", "Ham", "Ham (hog)"), ("pork", "Belly", "Belly (hog)"),
             ("salmon", "Salmon flesh", "Salmon fillets (farmed salmon)"), ("pollock", "Flesh (fillets, surimi, mince)", "Pollock flesh (wild pollock)")]
    rx = {(r["branch"], r["stream"], r["horizon"]): r["exit_cap"] for r in CURV["route_exit"]}
    def get(b, k, h, c):
        for r in EXIT:
            if r["branch"] == b and r["stream"] == k and r["horizon"] == h and abs(r["cap"] - c) < 1e-9: return r
        return None
    lines = ["| Product (animal) | Animal change, substitute at 90% of today's price | at 75% | at 50% | at 25% | Substitute's share of the market at 50% | Animal change at 50%, constant-cost limit | Price below which the raw commodity leaves the product entirely (3–5 years) |"]
    for b, k, label in picks:
        cells = [label]
        for c in (0.9, 0.75, 0.5, 0.25):
            r = get(b, k, "LR", c)
            cells.append(pct_auto(r["A"]) if r else "n/a (cap below the floor)")
        r = get(b, k, "LR", 0.5); cells.append(pct(r["sub_share"], 0) if r and r["sub_share"] is not None else "n/a")
        r = get(b, k, "limit", 0.5); cells.append(("n/a (quota)" if b == "pollock" else pct_auto(r["A"])) if r else "n/a")
        ex = rx.get((b, k, "LR"))
        cells.append(f"{ex*100:.0f}% of today's price" if ex else "no threshold (joint products carry the route)" if b in ("dairy_2026", "eggs_2019-21") else "not applicable (carcass part)")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def bundle_table():
    lines = ["| Animal | Substitute for every product at 90% of today's prices | at 75% | at 50% | at 25% | Constant-cost limit, any discount |"]
    for b in params.ALL:
        if b.key in ("dairy_2019", "eggs_2025"): continue
        cells = [b.name.split(" (")[0]]
        for c in (0.9, 0.75, 0.5, 0.25):
            cells.append(pct_auto(c ** b.eps_s_lr - 1.0) if b.eps_s_lr > 0 else "0% (quota)")
        cells.append("n/a (quota)" if b.key == "pollock" else M + "100%")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def horizon_summary():
    picks = [("eggs_2019-21", "Shell eggs (table)", "Shell eggs"), ("salmon", "Salmon HOG, fillets and portions", "Farmed salmon fillets"), ("dairy_2026", "Cheese (cheddar-equivalent)", "Cheese"),
             ("broiler", "Boneless skinless breast (fillets, whole-muscle nuggets)", "Chicken breast"), ("beef", "Middle meats: steaks and roasts from rib and loin", "Beef middle meats"),
             ("pork", "Ham (mostly cured)", "Ham"), ("pork", "Loin (chops, roasts)", "Pork loin"), ("eggs_2019-21", "Liquid/frozen whole egg", "Whole liquid egg"),
             ("beef", "Grinding material: trim and ground chuck/round (minced beef)", "Beef grinding material"), ("pork", "Belly (bacon)", "Pork belly"),
             ("dairy_2026", "Fluid milk (Class I)", "Fluid milk"), ("broiler", "Wings", "Chicken wings"), ("eggs_2019-21", "Liquid egg yolk", "Separated egg yolk"),
             ("pork", "Picnic, jowl, neck bones, trim -> sausage, ground pork", "Pork sausage material"), ("broiler", "Leg quarters / dark meat (whole legs)", "Chicken dark meat"),
             ("dairy_2026", "Nonfat dry milk / SMP (also the casein route)", "Nonfat dry milk (casein route)"), ("eggs_2019-21", "Liquid egg white (albumen): liquid, dried albumen, protein fractions", "Separated egg white"),
             ("dairy_2026", "WPC 80 (whey protein concentrate)", "WPC 80 (2026 prices)"), ("dairy_2026", "WPI (whey protein isolate)", "WPI (2026 prices)"), ("dairy_2019", "WPI (whey protein isolate)", "WPI (2019 prices)"),
             ("pollock", "Fillet blocks and fillets (fish fingers, portions)", "Pollock fillets (quota)"), ("broiler", "Backs, necks, frames -> mechanically separated chicken (MSC nuggets, hot dogs)", "Mechanically separated chicken"),
             ("beef", "Hide", "Beef hide"), ("pollock", "Fishmeal", "Fishmeal (pollock)")]
    lines = ["| Product | Share of animal value | DF within a year | DF 3–5 years (80% range) | DF constant-cost limit | Animal change if the product's market is lost (3–5 years) |"]
    for key, sub, label in picks:
        br = [b for b in params.ALL if b.key == key][0]
        rs = {x["sub"]: x for x in br.results(br.eps_s_sr)}; rl = {x["sub"]: x for x in br.results(br.eps_s_lr)}
        mc = MC[key][sub]
        stream = rl[sub]["stream"]; w = rl[sub]["w"]
        a = FULL[key][stream]["LR"]["A"] * (w if abs(w - 1) > 1e-6 else 1.0)
        lim = "n/a" if key == "pollock" else df(rl[sub]["DF_limit"])
        lines.append(f"| {label} | {pct(rs[sub]['share_total'])} | {df(rs[sub]['DF'])} | {dfr(rl[sub]['DF'], mc['lr']['p10'], mc['lr']['p90'])} | {lim} | {pct_auto(a)}{'' if abs(w-1)<1e-6 else ' (share of the stream)'} |")
    return "\n".join(lines)


def numbers():
    """key numbers for the prose"""
    out = {}
    for key in ["dairy_2026", "dairy_2019", "beef", "eggs_2019-21", "eggs_2025", "broiler", "pork", "pollock", "salmon"]:
        br = [b for b in params.ALL if b.key == key][0]
        rl = {x["sub"]: x for x in br.results(br.eps_s_lr)}; rs = {x["sub"]: x for x in br.results(br.eps_s_sr)}
        out[key] = dict(bundle_sr=br.DF_bundle(br.eps_s_sr), bundle_lr=br.DF_bundle(br.eps_s_lr), bundle_mc=MC[key]["__bundle__"], eps_bar=br.eps_bar(), H=br.H(),
                        streams={k.name: dict(share=br.stream_value(k.name)/br.total(), DF_lr=br.DF_stream(k.name, br.eps_s_lr), DF_sr=br.DF_stream(k.name, br.eps_s_sr), DF_lim=br.DF_stream_limit(k.name),
                                              g=br.price_response(k.name, br.eps_s_lr)["EPk"], full=FULL[key][k.name]) for k in br.streams},
                        subs={s: dict(share=rl[s]["share_total"], DF_lr=rl[s]["DF"], DF_sr=rs[s]["DF"], DF_lim=rl[s]["DF_limit"], w=rl[s]["w"], mc=MC[key][s], ep10=rl[s]["EP_stream_10"], kg=rl[s]["animal_units_per_unit"]) for s in rl})
        if br.fung_routes():
            out[key]["routes"] = {r: dict(W=br.W(r), a=(br.a(r) if r in br.fung_routes() else None), eps_r=br.eps_route(r)) for r in br.routes()}
            out[key]["eps_raw"] = br.eps_raw(); out[key]["W_raw"] = br.W_raw()
    return out


def main(results=RESULTS, out_dir=TABLES, echo=False):
    load(results)
    out_dir.mkdir(parents=True, exist_ok=True)
    for key in ROWS:
        open(out_dir / f"results_{key}.md", "w").write(branch_table(key))
    open(out_dir / "exit.md", "w").write(exit_table())
    open(out_dir / "bundle_cap.md", "w").write(bundle_table())
    open(out_dir / "horizons.md", "w").write(horizon_summary())
    json.dump(numbers(), open(out_dir / "numbers.json", "w"), indent=0, default=float)
    if echo:
        for f in ["horizons", "exit", "bundle_cap", "results_dairy_2026", "results_eggs_2019-21", "results_broiler"]:
            print("\n###", f); print(open(out_dir / f"{f}.md").read())
