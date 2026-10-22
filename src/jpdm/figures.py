"""The paper's eleven figures as PNG files, drawn from the model and from the data files in data/.

python -m jpdm figures   (writes paper/figures/fig01.png ... fig11.png)
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from . import data, params  # noqa: E402
from .paths import FIGURES, RESULTS  # noqa: E402

# reference palette (light mode): surface, text, neutrals and the first categorical slots
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
QUIET = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
VIOLET = "#6250d6"
LIGHT_BLUE = "#9ec5f4"
MINUS = "−"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": QUIET, "xtick.color": QUIET, "ytick.color": QUIET,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "lines.linewidth": 2,
    "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round", "legend.frameon": False,
})


def _title(fig, title, subtitle=None):
    """Title and subtitle at the top left; returns the figure fraction left for the plot (pass to subplots_adjust top)."""
    import textwrap
    h = fig.get_figheight()
    tl = textwrap.wrap(title, 84)
    fig.text(0.02, 1 - 0.14 / h, "\n".join(tl), ha="left", va="top", fontsize=12, fontweight="bold", color=INK, linespacing=1.25)
    y = 0.14 + 0.25 * len(tl) + 0.08
    if subtitle:
        sl = textwrap.wrap(subtitle, 122)
        fig.text(0.02, 1 - y / h, "\n".join(sl), ha="left", va="top", fontsize=9, color=QUIET, linespacing=1.3)
        y += 0.19 * len(sl)
    return 1 - (y + 0.3) / h


def _grid(ax, axis="y"):
    ax.grid(True, axis=axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _pct(v, d=0):
    s = f"{abs(v) * 100:.{d}f}%"
    return (MINUS if v < 0 else "") + s


def _save(fig, out_dir, name):
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / name, dpi=200)
    plt.close(fig)


def _rows(br, eps=None):
    return br.results(br.eps_s_lr if eps is None else eps)


def _df(br, stream=None, sub=None, horizon="lr"):
    if stream is not None:
        if horizon == "limit":
            return br.DF_stream_limit(stream)
        return br.DF_stream(stream, br.eps_s_lr if horizon == "lr" else br.eps_s_sr)
    key = "DF_limit" if horizon == "limit" else "DF"
    eps = br.eps_s_sr if horizon == "sr" else br.eps_s_lr
    return sum(r[key] for r in br.results(eps) if r["sub"].startswith(sub))


def _shares(br):
    out = {}
    for r in _rows(br):
        out[r["stream"]] = out.get(r["stream"], 0.0) + r["share_total"]
    return out


def _sub_shares(br):
    return {r["sub"]: r["share_total"] for r in _rows(br)}


# ---------------------------------------------------------------- figure 1
def fig01(out):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    top = _title(fig, "Displacement rises steeply with the supply elasticity and falls as demand becomes elastic",
           "Single-product displacement factor = supply elasticity / (supply elasticity + |demand elasticity|)")
    fig.subplots_adjust(left=0.08, right=0.76, top=top, bottom=0.12)
    es = [i / 100 for i in range(1, 251)]
    ax.axvspan(0.03, 0.40, color=GRID, alpha=0.6, lw=0)
    ax.axvspan(0.70, 1.50, color=LIGHT_BLUE, alpha=0.35, lw=0)
    ax.text(0.215, 0.97, "within a year\n0.03 to 0.40", ha="center", va="top", fontsize=8.5, color=QUIET, transform=ax.get_xaxis_transform())
    ax.text(1.10, 0.97, "three to five years\n0.70 to 1.50", ha="center", va="top", fontsize=8.5, color=QUIET, transform=ax.get_xaxis_transform())
    for ed, c in ((0.3, BLUE), (0.6, AQUA), (1.0, ORANGE), (2.0, VIOLET)):
        y = [e / (e + ed) for e in es]
        ax.plot(es, y, color=c)
        ax.text(2.55, y[-1], f"demand elasticity {MINUS}{ed:g}", va="center", fontsize=9, color=INK)
    ax.set_xlim(0, 2.5)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Supply elasticity")
    ax.set_ylabel("Displacement factor")
    _grid(ax)
    _save(fig, out, "fig01.png")


# ---------------------------------------------------------------- flow diagrams (figures 2 and 9)
def _flow(out, name, title, subtitle, nodes, edges, height=5.2):
    fig = plt.figure(figsize=(8, height))
    top = _title(fig, title, subtitle)
    ax = fig.add_axes([0.02, 0.02, 0.96, top - 0.02])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    pos = {}
    for n in nodes:
        x, y, w = n["x"], n["y"], n.get("w", 13)
        h = 11
        main = n.get("kind") == "main"
        raw = n.get("kind") == "raw"
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                             facecolor=("#dbe9fa" if main else GRID if raw else SURFACE),
                             edgecolor=(BLUE if main else AXIS), linewidth=(1.6 if main else 1.0))
        ax.add_patch(box)
        ax.text(x, y + 1.6, n["label"], ha="center", va="center", fontsize=8.6, fontweight="bold", color=INK)
        if n.get("share"):
            ax.text(x, y - 2.6, n["share"], ha="center", va="center", fontsize=8.3, color=QUIET)
        pos[n["id"]] = (x, y, h)
    for a, b in edges:
        x1, y1, h1 = pos[a]
        x2, y2, h2 = pos[b]
        ym = (y1 - h1 / 2 + y2 + h2 / 2) / 2
        ax.plot([x1, x1, x2, x2], [y1 - h1 / 2, ym, ym, y2 + h2 / 2 + 0.8], color=AXIS, lw=1.1, solid_joinstyle="miter")
        ax.annotate("", xy=(x2, y2 + h2 / 2), xytext=(x2, y2 + h2 / 2 + 1.2), arrowprops=dict(arrowstyle="-|>", color=AXIS, lw=1.1, mutation_scale=8))
    _save(fig, out, name)


def fig02(out):
    br = params.dairy("2026")
    s, ss = _shares(br), _sub_shares(br)
    p = lambda v: f"{v * 100:.1f}%"  # noqa: E731
    raw = sum(s[k] for k in ("Fluid milk", "Other dairy", "Butter (fat)", "Milk powder (nonfat solids)", "Cheese", "Whey protein", "Whey carbohydrate"))
    whey = s["Whey protein"] + s["Whey carbohydrate"]
    nodes = [
        dict(id="cow", label="Dairy cow", x=50, y=92, kind="raw"),
        dict(id="milk", label="Raw milk", share=f"{raw * 100:.0f}% of revenue", x=34, y=72, kind="raw", w=16),
        dict(id="cattle", label="Cattle sales", share=f"{(1 - raw) * 100:.0f}% of revenue", x=80, y=72, kind="raw", w=16),
        dict(id="fluid", label="Fluid milk", share=p(s["Fluid milk"]), x=8, y=50),
        dict(id="other", label="Yogurt, ice cream", share=p(s["Other dairy"]), x=23, y=50, w=14),
        dict(id="bp", label="Butter, powder", share=p(s["Butter (fat)"] + s["Milk powder (nonfat solids)"]), x=38.5, y=50, w=14),
        dict(id="cr", label="Cheese route", share=p(s["Cheese"] + whey), x=55, y=50, kind="raw"),
        dict(id="cull", label="Cull cows", share=p(s["Cull cows"]), x=74, y=50),
        dict(id="calf", label="Calves", share=p(s["Calves"]), x=89, y=50),
        dict(id="cheese", label="Cheese", share=p(s["Cheese"]), x=47, y=29, kind="main"),
        dict(id="whey", label="Whey", share=p(whey), x=64, y=29),
        dict(id="wp", label="WPC 80 and WPI", share=f"{p(s['Whey protein'])} ({p(ss['WPC 80 (whey protein concentrate)'])} + {p(ss['WPI (whey protein isolate)'])})", x=55, y=8, w=20),
        dict(id="wc", label="Dry whey, lactose", share=p(s["Whey carbohydrate"]), x=77, y=8, w=16),
    ]
    edges = [("cow", "milk"), ("cow", "cattle"), ("milk", "fluid"), ("milk", "other"), ("milk", "bp"), ("milk", "cr"),
             ("cattle", "cull"), ("cattle", "calf"), ("cr", "cheese"), ("cr", "whey"), ("whey", "wp"), ("whey", "wc")]
    _flow(out, "fig02.png", f"Cheese carries {s['Cheese'] * 100:.0f}% of the dairy cow's revenue; the whey that comes with it, {whey * 100:.0f}%",
          "Share of a US dairy cow's revenue by product at September to October 2026 prices, farm-equivalent values (model estimate). "
          "Milk is allocated across uses; cheese and whey come in fixed proportions.", nodes, edges)


def fig09(out):
    br = params.eggs("2019-21")
    s = _shares(br)
    p = lambda v: f"{v * 100:.1f}%"  # noqa: E731
    eggs = 1 - s["Spent hen"]
    brk = s["Whole egg products"] + s["Egg white"] + s["Egg yolk"]
    sep = s["Egg white"] + s["Egg yolk"]
    raw = br.raw_shares
    nodes = [
        dict(id="hen", label="Laying hen", x=50, y=92, kind="raw"),
        dict(id="eggs", label="Eggs", share=f"{eggs * 100:.1f}% of revenue", x=38, y=72, kind="raw", w=16),
        dict(id="spent", label="Spent hen", share=f"{s['Spent hen'] * 100:.1f}%", x=78, y=72),
        dict(id="shell", label="Shell eggs", share=f"{p(s['Shell eggs'])} ({raw['Shell'] * 100:.0f}% of eggs)", x=22, y=50, kind="main", w=20),
        dict(id="brk", label="Breaking plant", share=f"{p(brk)} ({(1 - raw['Shell']) * 100:.0f}% of eggs)", x=58, y=50, kind="raw", w=20),
        dict(id="whole", label="Whole liquid egg", share=p(s["Whole egg products"]), x=44, y=29, w=16),
        dict(id="sep", label="Separated", share=f"{p(sep)} ({raw['Products: separated'] * 100:.1f}% of eggs)", x=72, y=29, w=20),
        dict(id="white", label="Egg white", share=p(s["Egg white"]), x=63, y=8),
        dict(id="yolk", label="Egg yolk", share=p(s["Egg yolk"]), x=81, y=8),
    ]
    edges = [("hen", "eggs"), ("hen", "spent"), ("eggs", "shell"), ("eggs", "brk"), ("brk", "whole"), ("brk", "sep"), ("sep", "white"), ("sep", "yolk")]
    _flow(out, "fig09.png", f"Shell eggs carry {s['Shell eggs'] * 100:.0f}% of a laying hen's revenue; separated egg white, {s['Egg white'] * 100:.0f}%",
          "Share of a US laying hen's revenue by product at 2019-21 price relationships (model estimate; USDA NASS volumes and AMS prices). "
          "Eggs go to the shell market or the breaking plant; white and yolk come in fixed proportions.", nodes, edges)


# ---------------------------------------------------------------- figure 3
def fig03(out):
    groups = [("Cheese", ["Cheese"]), ("Fluid milk", ["Fluid milk"]), ("Whey protein (WPC 80, WPI)", ["Whey protein"]),
              ("Nonfat dry milk", ["Milk powder (nonfat solids)"]), ("Yogurt, ice cream, other", ["Other dairy"]),
              ("Cull cows", ["Cull cows"]), ("Butter", ["Butter (fat)"]), ("Calves", ["Calves"]), ("Whey carbohydrate", ["Whey carbohydrate"])]
    old, new = _shares(params.dairy("2019")), _shares(params.dairy("2026"))
    fig, ax = plt.subplots(figsize=(8, 5.2))
    wp_old, wp_new = old["Whey protein"], new["Whey protein"]
    top = _title(fig, f"Whey protein rose from {wp_old * 100:.0f}% to {wp_new * 100:.0f}% of the dairy cow's revenue between 2019-21 and 2026 prices",
           "Share of a US dairy cow's revenue by product, farm-equivalent values (model estimate)")
    fig.subplots_adjust(left=0.29, right=0.95, top=top, bottom=0.11)
    for i, (label, ks) in enumerate(groups):
        a, b = sum(old[k] for k in ks), sum(new[k] for k in ks)
        y = len(groups) - 1 - i
        ax.barh(y + 0.19, a * 100, height=0.36, color=MUTED, edgecolor=SURFACE, linewidth=1)
        ax.barh(y - 0.19, b * 100, height=0.36, color=BLUE, edgecolor=SURFACE, linewidth=1)
        ax.text(a * 100 + 0.6, y + 0.19, f"{a * 100:.1f}%", va="center", fontsize=8, color=QUIET)
        ax.text(b * 100 + 0.6, y - 0.19, f"{b * 100:.1f}%", va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([g[0] for g in groups][::-1], color=INK)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 60)
    ax.set_xlabel("Share of revenue (%)")
    _grid(ax, "x")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=MUTED), plt.Rectangle((0, 0), 1, 1, color=BLUE)],
              labels=["2019-21 prices", "September to October 2026 prices"], loc="lower right", fontsize=8.5)
    _save(fig, out, "fig03.png")


# ---------------------------------------------------------------- figure 4
def fig04(out):
    rows = data.carcass_shares()
    animals = ["Fed steer", "Broiler", "Hog"]
    heads = {"Fed steer": "Fed steer: the rib and loin are {w:.0f}% of live weight and {v:.0f}% of value",
             "Broiler": "Broiler: breast and tenders are {w:.0f}% of live weight and {v:.0f}% of value",
             "Hog": "Hog: loin, butt and ribs are {w:.0f}% of live weight and {v:.0f}% of value"}
    n = [sum(1 for r in rows if r["animal"] == a) for a in animals]
    fig, axes = plt.subplots(3, 1, figsize=(8, 8.4), gridspec_kw=dict(height_ratios=n, hspace=0.55))
    top = _title(fig, "Value concentrates in a few parts of every carcass",
           "Grey = share of live weight; blue = share of the animal's value (USDA AMS cutouts, drop values and parts prices; Cobb 500 yields)")
    fig.subplots_adjust(left=0.33, right=0.95, top=top, bottom=0.07)
    for ax, a in zip(axes, animals):
        rs = [r for r in rows if r["animal"] == a]
        first = rs[0]
        ax.set_title(heads[a].format(w=first["live_weight_pct"], v=first["value_pct"]), loc="left", fontsize=9.5, color=INK, x=-0.45)
        for i, r in enumerate(rs):
            y = len(rs) - 1 - i
            w, v = r["live_weight_pct"], r["value_pct"]
            ax.barh(y + 0.19, w, height=0.36, color=MUTED, edgecolor=SURFACE)
            ax.barh(y - 0.19, v, height=0.36, color=BLUE, edgecolor=SURFACE)
            ax.text(w + 0.6, y + 0.19, f"{w:.1f}%", va="center", fontsize=7.5, color=QUIET)
            ax.text(v + 0.6, y - 0.19, f"{v:.1f}%", va="center", fontsize=7.5, color=INK)
        ax.set_yticks(range(len(rs)))
        ax.set_yticklabels([r["part"] for r in rs][::-1], color=INK, fontsize=8.5)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, 60)
        _grid(ax, "x")
    axes[-1].set_xlabel("Share (%)")
    _save(fig, out, "fig04.png")


# ---------------------------------------------------------------- figure 5
def fig05(out):
    rows = data.whey_prices()
    t = lambda m: int(m[:4]) + (int(m[5:7]) - 1) / 12  # noqa: E731
    fig, ax = plt.subplots(figsize=(8, 4.6))
    top = _title(fig, "Whey prices swing between the feed-grade floor and three times it within three years",
           "USD per lb, monthly averages, Central US (USDA AMS Dairy Market News); WPC 80 and WPI (no monthly series) went from "
           "under $4 in 2023 to $9 to $14 in 2026")
    fig.subplots_adjust(left=0.08, right=0.88, top=top, bottom=0.1)
    floor = 0.365
    ax.axhline(floor, color=MUTED, lw=1, ls=(0, (4, 3)))
    ax.text(2024.4, floor - 0.1, r"feed-grade dry whey, October 2026: \$0.35 to \$0.38", fontsize=8.5, color=QUIET)
    for series, c in (("Dry whey", MUTED), ("WPC 34%", BLUE)):
        pts = [(t(r["month"]), r["usd_per_lb"], r["month"]) for r in rows if r["series"] == series]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=c)
        ax.text(pts[-1][0] + 0.05, pts[-1][1], series, va="center", fontsize=9, color=INK)
        if series == "Dry whey":
            lo = min(pts, key=lambda p: p[1])
            ax.annotate(f"{lo[2]}: ${lo[1]:.2f}", (lo[0], lo[1]), xytext=(0, -14), textcoords="offset points", ha="center", fontsize=8, color=QUIET)
        else:
            ax.annotate(f"{pts[-1][2]}: ${pts[-1][1]:.2f}", (pts[-1][0], pts[-1][1]), xytext=(-6, 6), textcoords="offset points", ha="right", fontsize=8, color=INK)
    ax.set_xlim(2022, 2026.75)
    ax.set_ylim(0, 2.6)
    ax.set_xticks([2022, 2023, 2024, 2025, 2026])
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:.2f}"))
    _grid(ax)
    _save(fig, out, "fig05.png")


# ---------------------------------------------------------------- figure 6
RANKING = [
    ("Shell eggs", "eggs_2019-21", "Shell eggs", None), ("Farmed salmon fillets", "salmon", None, "Salmon HOG"),
    ("Cheese", "dairy_2026", "Cheese", None), ("Chicken breast", "broiler", None, "Boneless skinless breast"),
    ("Beef middle meats (rib, loin)", "beef", "Middle meats (whole cut)", None), ("Ham", "pork", "Ham", None),
    ("Pork loin", "pork", None, "Loin"), ("Whole liquid egg", "eggs_2019-21", "Whole egg products", None),
    ("Beef grinding material (mince)", "beef", "Minced beef (grinding material)", None), ("Pork belly (bacon)", "pork", "Belly", None),
    ("Beef end-meat whole-muscle cuts", "beef", None, "End-meat whole-muscle"), ("Fluid milk", "dairy_2026", "Fluid milk", None),
    ("Chicken wings", "broiler", "Wings", None), ("Separated egg yolk", "eggs_2019-21", "Egg yolk", None),
    ("Pork sausage material (trim)", "pork", "Sausage & trim", None), ("Chicken dark meat (leg quarters)", "broiler", "Dark meat", None),
    ("Nonfat dry milk / casein route", "dairy_2026", "Milk powder (nonfat solids)", None), ("Other dairy (yogurt, ice cream)", "dairy_2026", "Other dairy", None),
    ("Separated egg white", "eggs_2019-21", "Egg white", None), ("Dairy cull cows", "dairy_2026", "Cull cows", None),
    ("Pollock fillets (fish fingers)", "pollock", None, "Fillet blocks"), ("WPC 80 (2026 prices)", "dairy_2026", None, "WPC 80"),
    ("Pork drop credit (lard, offal)", "pork", None, "Drop credit"), ("WPI (2026 prices)", "dairy_2026", None, "WPI"),
    ("Chicken paws", "broiler", None, "Paws"), ("Beef edible offal", "beef", None, "Edible offal"), ("WPI (2019 prices)", "dairy_2019", None, "WPI"),
    ("Mechanically separated chicken", "broiler", "Backs & necks (MSC)", None), ("Beef tallow", "beef", None, "Tallow"),
    ("Fishmeal", "pollock", None, "Fishmeal"), ("Beef hide", "beef", None, "Hide"), ("Spent laying hen", "eggs_2019-21", "Spent hen", None),
]


def fig06(out):
    by_key = {b.key: b for b in params.ALL}
    rows = sorted(((lab, _df(by_key[k], stream=st, sub=sb)) for lab, k, st, sb in RANKING), key=lambda r: -r[1])
    fig, ax = plt.subplots(figsize=(8, 8.6))
    top = _title(fig, "Primary products displace a tenth to a half of the volume replaced; by-products under a twentieth",
           "Displacement factor after three to five years by product; dark blue 0.10 and above, light blue 0.05 to 0.10, grey below 0.05")
    fig.subplots_adjust(left=0.36, right=0.95, top=top, bottom=0.06)
    for i, (lab, v) in enumerate(rows):
        y = len(rows) - 1 - i
        c = BLUE if v >= 0.10 else LIGHT_BLUE if v >= 0.05 else MUTED
        ax.barh(y, v, height=0.62, color=c, edgecolor=SURFACE)
        ax.text(v + 0.005, y, "<0.001" if v < 0.0005 else f"{v:.3f}" if v < 0.1 else f"{v:.2f}", va="center", fontsize=7.8, color=INK)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1], color=INK, fontsize=8.2)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 0.52)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("Displacement factor, three to five years")
    _grid(ax, "x")
    _save(fig, out, "fig06.png")


# ---------------------------------------------------------------- figure 7
def fig07(out):
    cow, cow19, bro = params.dairy("2026"), params.dairy("2019"), params.broiler()
    series = [
        ("Dairy cow, all products", [cow.DF_bundle(cow.eps_s_sr), cow.DF_bundle(cow.eps_s_lr), 1.0], MUTED, (0, (4, 3))),
        ("Cheese", [_df(cow, "Cheese", horizon=h) for h in ("sr", "lr", "limit")], BLUE, "-"),
        ("Chicken breast", [_df(bro, sub="Boneless skinless breast", horizon=h) for h in ("sr", "lr", "limit")], AQUA, "-"),
        ("Fluid milk", [_df(cow, "Fluid milk", horizon=h) for h in ("sr", "lr", "limit")], VIOLET, "-"),
        ("Whey protein (WPC 80 and WPI)", [_df(cow, "Whey protein", horizon=h) for h in ("sr", "lr", "limit")], ORANGE, "-"),
        ("Mechanically separated chicken", [_df(bro, "Backs & necks (MSC)", horizon=h) for h in ("sr", "lr", "limit")], MAGENTA, "-"),
    ]
    fig, ax = plt.subplots(figsize=(8, 5.0))
    top = _title(fig, "The elasticity discount shrinks with the horizon; the joint-production discount does not",
           "Displacement factor at three horizons (log scale); the slope is the supply response, the gap between lines is joint production")
    fig.subplots_adjust(left=0.09, right=0.66, top=top, bottom=0.1)
    xs = [0, 1, 2]
    ends = sorted(((ys[-1], name) for name, ys, c, ls in series), reverse=True)
    pos, last = {}, None
    for v, name in ends:   # keep end labels at least a factor 1.6 apart on the log axis
        y = v if last is None else min(v, last / 1.6)
        pos[name] = last = y
    for name, ys, c, ls in series:
        ax.plot(xs, ys, color=c, ls=ls, marker="o", markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.annotate(f"{name}  {ys[-1]:.3f}".replace("1.000", "1"), (2, ys[-1]), xytext=(2.08, pos[name]), textcoords="data",
                    va="center", fontsize=8.5, color=INK, annotation_clip=False)
    ax.set_yscale("log")
    ax.set_ylim(0.0003, 1.3)
    ax.set_xticks(xs)
    ax.set_xticklabels(["within a year", "three to five years", "constant-cost limit"], color=INK)
    ax.set_xlim(-0.1, 2.05)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    _grid(ax)
    _save(fig, out, "fig07.png")


# ---------------------------------------------------------------- figure 8
def fig08(out, results=RESULTS):
    cow = params.dairy("2026")
    g = cow.price_response("Whey protein", cow.eps_s_lr)["EPk"]
    df = cow.DF_stream("Whey protein", cow.eps_s_lr)
    floor = cow.get("Whey protein").floor_ratio
    full = json.load(open(results / "full_loss.json"))["dairy_2026"]["Whey protein"]["LR"]["A"]
    share_wpi = _sub_shares(cow)["WPI (whey protein isolate)"] / _shares(cow)["Whey protein"]
    xs = [i / 200 for i in range(0, 200)]
    ys = [max(floor, (1 - x) ** g) for x in xs]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    m1 = share_wpi
    top = _title(fig, f"Taking {m1 * 100:.0f}% of the whey protein market cuts its price by {(1 - (1 - m1) ** g) * 100:.0f}% and milk output by {df * m1 * 100:.1f}%",
           f"Whey protein stream (WPC 80 and WPI) price as a share of today's, by share of the stream replaced; three to five years, 2026 parameters "
           f"(price = (1 {MINUS} share) to the power {g:.2f}, floored at {floor:.0%})")
    fig.subplots_adjust(left=0.09, right=0.95, top=top, bottom=0.12)
    ax.axhline(floor, color=MUTED, lw=1, ls=(0, (4, 3)))
    ax.text(0.02, floor + 0.025, f"floor: feed-grade whey, {floor:.0%} of today's price", fontsize=8.5, color=QUIET)
    ax.plot(xs, ys, color=ORANGE)
    for m, lab, off, ha in ((m1, "all WPI replaced", (8, 8), "left"), (m1 + (1 - m1) / 2, "WPI and half of WPC 80 replaced", (-10, -4), "right")):
        p = (1 - m) ** g
        ax.plot([m], [p], "o", color=ORANGE, markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.annotate(f"{lab}: price {_pct(p - 1)}, milk {_pct(-df * m, 1)}", (m, p), xytext=off, textcoords="offset points", fontsize=8.5,
                    color=INK, ha=ha, va="top" if ha == "right" else "bottom")
    ax.annotate(f"whole stream at the floor: milk {_pct(full, 1)} (exact solution)", (0.99, floor), xytext=(-10, 26), textcoords="offset points",
                ha="right", fontsize=8.5, color=INK, arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    ax.set_xlabel("Share of the whey protein stream replaced")
    ax.set_ylabel("Price, share of today's")
    _grid(ax)
    _save(fig, out, "fig08.png")


# ---------------------------------------------------------------- figure 10
def fig10(out, results=RESULTS):
    cv = json.load(open(results / "exit_curves.json"))["curves"]
    series = [("dairy_2026", "Cheese", "Cheese (milk output)", BLUE), ("dairy_2026", "Whey protein", "Whey protein (milk output)", ORANGE),
              ("eggs_2019-21", "Shell eggs", "Shell eggs (hens)", AQUA), ("eggs_2019-21", "Egg white", "Egg white (hens)", VIOLET)]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    pick = lambda b, s, c: next(r["A"] for r in cv if r["branch"] == b and r["stream"] == s and r["horizon"] == "LR" and abs(r["cap"] - c) < 1e-9)  # noqa: E731
    top = _title(fig, f"At half today's price a substitute removes {_pct(-pick('dairy_2026', 'Cheese', 0.5))} of milk through cheese, "
                f"{_pct(-pick('dairy_2026', 'Whey protein', 0.5), 1)} through whey protein",
           "Animal output after three to five years against the substitute's price as a share of today's; exact solution of the model; "
           "a line ends at the product's floor price and flattens once the substitute holds the whole market")
    fig.subplots_adjust(left=0.09, right=0.72, top=top, bottom=0.12)
    offs = {"Cheese": (6, 0, "left", "center"), "Shell eggs": (6, 0, "left", "center"), "Whey protein": (6, 0, "left", "center"),
            "Egg white": (0, -16, "center", "top")}
    for b, s, lab, c in series:
        pts = sorted(((r["cap"], r["A"]) for r in cv if r["branch"] == b and r["stream"] == s and r["horizon"] == "LR"), reverse=True)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=c)
        dx, dy, ha, va = offs[s]
        ax.annotate(f"{lab}\n{_pct(pts[-1][1], 1)} at {pts[-1][0]:.0%} of today's price", (pts[-1][0], pts[-1][1]), xytext=(dx, dy),
                    textcoords="offset points", ha=ha, va=va, fontsize=8.3, color=INK, annotation_clip=False)
    ax.set_xlim(1.0, 0.0)
    ax.set_ylim(-0.5, 0.02)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: _pct(v)))
    ax.set_xlabel("Substitute's price, share of today's price")
    ax.set_ylabel("Change in animal output")
    _grid(ax)
    _save(fig, out, "fig10.png")


# ---------------------------------------------------------------- figure 11
LABEL_SIDE = {"Chicken breast": "l", "Fluid milk": "l", "Ham": "l", "Whole liquid egg": "l", "Cheese": "l", "Pork loin": "l"}
JITTER = {"Whey protein, 2026 prices": 0.1, "Separated egg white": -0.35, "Whey protein, 2019 prices": 0.05, "Mechanically separated chicken": -0.05,
          "Pork sausage trim": -0.25, "Fishmeal and oil": 0.4, "Tallow, hides, lard": -0.1, "Pollock fillets (fish fingers)": 0.15,
          "Chicken breast": 0.1, "Fluid milk": -0.1, "Ham": -0.1, "Cheese": -0.15, "Farmed salmon": 0.15, "Beef middle meats (steaks)": 0.1, "Pork loin": -0.1}
DY = {"Whey protein, 2026 prices": 1.0, "Separated egg white": 1.0, "Whey protein, 2019 prices": 1.12, "Mechanically separated chicken": 0.9,
      "Pork sausage trim": 1.0, "Fishmeal and oil": 1.12, "Tallow, hides, lard": 0.85, "Pollock fillets (fish fingers)": 1.0, "Fluid milk": 0.93,
      "Farmed salmon": 0.92, "Shell eggs": 1.08, "Ham": 1.04}


def fig11(out):
    rows = data.reachability()
    fig, ax = plt.subplots(figsize=(8, 5.6))
    top = _title(fig, "The fractions biotechnology reaches first are the ones with the lowest displacement",
           "Displacement factor after three to five years (log scale) against technical reachability; reachability is a judgement (section 8)")
    fig.subplots_adjust(left=0.1, right=0.97, top=top, bottom=0.12)
    for r in rows:
        x = r["reachability"] + JITTER.get(r["product"], 0.0)
        y = r["df_3_5_years"]
        c = BLUE if y >= 0.10 else ORANGE if r["reachability"] == 4 else MUTED
        ax.plot([x], [y], "o", color=c, markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
        left = LABEL_SIDE.get(r["product"]) == "l"
        ax.text(x + (-0.07 if left else 0.07), y * DY.get(r["product"], 1.0), r["product"], ha="right" if left else "left", va="center", fontsize=7.6, color=INK)
    ax.set_yscale("log")
    ax.set_ylim(0.0015, 0.8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels(["low", "low to medium", "medium", "high"], color=INK)
    ax.set_xlim(0.4, 5.4)
    ax.set_xlabel("Technical reachability for biotechnology today")
    ax.set_ylabel("Displacement factor, three to five years")
    _grid(ax)
    _save(fig, out, "fig11.png")


def main(out_dir=FIGURES):
    out_dir = Path(out_dir)
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10, fig11):
        f(out_dir)
    print(f"  wrote 11 figures to {out_dir}")


if __name__ == "__main__":
    main()
