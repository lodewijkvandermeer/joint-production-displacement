"""Regenerate every committed output into a scratch directory and compare it with the repository.

JSON files are compared number by number (relative tolerance, so a different numpy or libm does not fail the check on
the 12th decimal); Markdown tables and docs must match as text. Exit status is non-zero on any difference.
"""
import json
import math
import tempfile
from pathlib import Path

from . import docs, exit_runs, monte_carlo, tables
from .docs import DOCS
from .paths import RESULTS, TABLES

RTOL = 1e-7
ATOL = 1e-9


def diff_json(a, b, path="", out=None):
    """Differences between two parsed JSON documents, as a list of (path, committed, regenerated)."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append((f"{path}/{k}", a.get(k, "<missing>"), b.get(k, "<missing>")))
            else:
                diff_json(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path + " (length)", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            diff_json(x, y, f"{path}[{i}]", out)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        if not math.isclose(a, b, rel_tol=RTOL, abs_tol=ATOL):
            out.append((path, a, b))
    elif a != b or isinstance(a, bool) != isinstance(b, bool):
        out.append((path, a, b))
    return out


def _compare(committed: Path, fresh: Path, report: list):
    for f in sorted(fresh.iterdir()):
        if f.is_dir():
            continue
        ref = committed / f.name
        if not ref.exists():
            report.append(f"{ref}: not in the repository")
        elif f.suffix == ".json":
            for p, x, y in diff_json(json.loads(ref.read_text()), json.loads(f.read_text()))[:5]:
                report.append(f"{ref.name}{p}: committed {x} != regenerated {y}")
        elif ref.read_text() != f.read_text():
            report.append(f"{ref}: text differs")


def main(verbose=False):
    report = []
    with tempfile.TemporaryDirectory() as tmp:
        res, tab, doc = Path(tmp) / "results", Path(tmp) / "tables", Path(tmp) / "docs"
        for d in (res, tab):
            d.mkdir()
        exit_runs.main(res, verbose)
        monte_carlo.main(res, verbose)
        tables.main(res, tab, verbose)
        docs.main(doc)
        _compare(RESULTS, res, report)
        _compare(TABLES, tab, report)
        _compare(DOCS, doc, report)
    if report:
        print("\nOutputs differ from the repository:")
        for line in report:
            print("  " + line)
        raise SystemExit(1)
    print("  all committed outputs reproduce")
