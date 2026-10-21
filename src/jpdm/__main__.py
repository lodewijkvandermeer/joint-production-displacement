"""Command line: python -m jpdm <command>.

  results    exact scenarios (price caps, full loss, curves) and Monte Carlo ranges -> results/*.json
  tables     Markdown tables and headline numbers from the results -> results/tables/
  workbook   the Excel model with live formulas -> workbook/joint_production_displacement_model.xlsx
  figures    the paper's figures as PNG -> paper/figures/
  docs       parameter and source tables -> docs/parameters.md, docs/sources.md
  check      regenerate results, tables and docs in a scratch directory and compare with the repository
  validate   print the exact solution against the closed form for 10% and 25% shifts
  summary    print displacement factors for every product at three horizons
  all        results, tables, workbook, figures and docs, in that order
"""
import argparse
import time

from .paths import RESULTS, TABLES, WORKBOOK, FIGURES


def summary():
    from . import params
    for br in params.ALL:
        print(f"\n{br.name}  (supply elasticity {br.eps_s_sr} within a year, {br.eps_s_lr} after 3-5 years)")
        print(f"  {'product':58s} {'share':>7s} {'<1 yr':>7s} {'3-5 yr':>7s} {'limit':>7s}")
        for sr, lr in zip(br.results(br.eps_s_sr) if br.eps_s_sr > 0 else [None] * len(br.subs), br.results(br.eps_s_lr)):
            dsr = sr["DF"] if sr else 0.0
            print(f"  {lr['sub'][:58]:58s} {lr['share_total']:7.1%} {dsr:7.3f} {lr['DF']:7.3f} {lr['DF_limit']:7.3f}")
        print(f"  {'all products together (bundle)':58s} {'100%':>7s} {br.DF_bundle(br.eps_s_sr) if br.eps_s_sr > 0 else 0:7.3f} {br.DF_bundle(br.eps_s_lr):7.3f} {1.0:7.3f}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m jpdm", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["results", "tables", "workbook", "figures", "docs", "check", "validate", "summary", "all"])
    ap.add_argument("-v", "--verbose", action="store_true", help="print intermediate output")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.command in ("results", "all"):
        from . import exit_runs, monte_carlo
        print("scenarios (exact model) ..."); exit_runs.main(RESULTS, a.verbose)
        print("Monte Carlo ranges (2,000 draws per animal) ..."); monte_carlo.main(RESULTS, a.verbose)
    if a.command in ("tables", "all"):
        from . import tables
        print("tables ..."); tables.main(RESULTS, TABLES, a.verbose)
    if a.command in ("workbook", "all"):
        from . import workbook
        print("workbook ..."); workbook.build(WORKBOOK, RESULTS)
        print(f"  wrote {WORKBOOK} (formulas compute when the file is opened in Excel or LibreOffice)")
    if a.command in ("figures", "all"):
        from . import figures
        print("figures ..."); figures.main(FIGURES)
    if a.command in ("docs", "all"):
        from . import docs
        print("docs ..."); docs.main()
    if a.command == "check":
        from . import check
        print("regenerating into a scratch directory and comparing ..."); check.main(a.verbose)
    if a.command == "validate":
        from . import exact_model
        exact_model.validate()
    if a.command == "summary":
        summary()
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
