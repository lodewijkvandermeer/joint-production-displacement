"""Generate docs/parameters.md and docs/sources.md from data/params/*.toml and sources.py, so the documentation cannot drift
from the numbers the model uses. python -m jpdm docs"""
from . import params
from .paths import ROOT
from .sources import SOURCES

DOCS = ROOT / "docs"


def _esc(s):
    return str(s).replace("|", "\\|")


def parameters_md():
    out = ["# Parameters", "",
           "Generated from `data/params/*.toml` by `python -m jpdm docs`; do not edit by hand. Tags: **[S]** sourced "
           "(see [sources.md](sources.md)), **[E]** estimated from sourced inputs, **[A]** assumption. Prices are wholesale or "
           "first-handler, US$ unless stated; quantities are per the unit shown for each animal.", ""]
    for br in params.ALL:
        T = br.total()
        out += [f"## {br.name}", "", f"Unit: {br.unit}. Prices: {br.price_tag}.", "",
                f"Supply elasticity: {br.eps_s_sr} within a year, {br.eps_s_lr} after three to five years. {_esc(br.supply_src)}", ""]
        if br.notes:
            out += [br.notes, ""]
        if br.raw_shares:
            out += ["Raw-commodity routes (share of raw volume): " + "; ".join(f"{r} {v:.3f}" for r, v in br.raw_shares.items()), ""]
        out += ["| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |", "| --- | --- | --- | --- | --- |"]
        for st in br.streams:
            fl = "none" if st.floor_ratio is None else f"{st.floor_ratio:g} ({_esc(st.floor_note)})" if st.floor_note else f"{st.floor_ratio:g}"
            out.append(f"| {_esc(st.name)} | {_esc(st.route)} | {st.elas:g} | {fl} | {_esc(st.elas_src)} |")
        out += ["", "| Product | Stream | Quantity per unit | Price | Value share | Source |", "| --- | --- | --- | --- | --- | --- |"]
        for s in br.subs:
            out.append(f"| {_esc(s.name)} | {_esc(s.stream)} | {s.qty:.4g} | {s.price:.4g} | {s.value / T:.1%} | {_esc(s.src)} |")
        out.append("")
    return "\n".join(out)


def sources_md():
    out = ["# Sources", "", "Generated from `src/jpdm/sources.py` by `python -m jpdm docs`. Pages opened October 2026.", "",
           "| # | Source | Used for |", "| --- | --- | --- |"]
    for i, (name, used, url) in enumerate(SOURCES, 1):
        out.append(f"| {i} | [{_esc(name)}]({url}) | {_esc(used)} |")
    return "\n".join(out) + "\n"


def main(out_dir=DOCS):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "parameters.md").write_text(parameters_md())
    (out_dir / "sources.md").write_text(sources_md())
    print(f"  wrote {out_dir / 'parameters.md'} and sources.md")


if __name__ == "__main__":
    main()
