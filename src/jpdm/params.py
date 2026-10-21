"""Loads every animal's parameters from data/params/<animal>.toml into the model's Branch objects.

All numbers live in the TOML files, with their [S] sourced / [E] estimated / [A] assumed tags beside them. This module
holds no numbers, only the loader. Quantities, prices and shares in the files may be plain numbers or arithmetic
expressions over the names in the file's [vars] table (and, in [derived], over total_value(), the summed value of the
[[subs]] products). Expressions are parsed with `ast` and limited to numbers, names, + - * / ** and total_value();
nothing else can run.

File layout (see data/params/dairy.toml for a full example):
  key, name, unit, eps_s_sr, eps_s_lr, notes, supply_src, price_tag   Branch metadata
  default_scenario, [scenarios.<name>] (+ .vars)                       optional price scenarios; they override
                                                                       metadata and add to / override [vars]
  [vars]            named inputs and intermediate values (resolved lazily, so order does not matter)
  [raw_shares]      route -> share of the raw commodity (fungible routes)
  [[subs]]          products: name, stream, qty, price, src
  [derived]         values that need total_value()
  [[derived_subs]]  products that use [derived] values; appended after [[subs]]
  [[streams]]       name, route, elas, floor (omit for none), floor_note, elas_src
"""
import ast
import operator
import sys
from typing import Optional

from .edm_model import Branch, Stream, Sub
from .paths import PARAMS

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

_BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.Pow: operator.pow}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


class _Names:
    """Evaluates the expressions of one animal/scenario; named values are resolved on demand."""

    def __init__(self, raw_vars: dict):
        self._raw = dict(raw_vars)
        self._done = {}
        self._active = []
        self.total = None            # set once the [[subs]] exist

    def value(self, x):
        """A number as given, or the value of an expression string."""
        if isinstance(x, str):
            return self._node(ast.parse(x.strip(), mode="eval").body, x)
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"expected a number or an expression, got {x!r}")
        return x

    def define(self, name, raw):
        self._raw[name] = raw

    def _name(self, name):
        if name in self._done:
            return self._done[name]
        if name not in self._raw:
            raise ValueError(f"unknown name {name!r}")
        if name in self._active:
            raise ValueError("circular definition: " + " -> ".join(self._active + [name]))
        self._active.append(name)
        try:
            self._done[name] = self.value(self._raw[name])
        finally:
            self._active.pop()
        return self._done[name]

    def _node(self, node, source):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name):
            return self._name(node.id)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](self._node(node.operand, source))
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            return _BINARY[type(node.op)](self._node(node.left, source), self._node(node.right, source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "total_value" \
                and not node.args and not node.keywords:
            if self.total is None:
                raise ValueError("total_value() is only available in [derived] and [[derived_subs]]")
            return self.total
        raise ValueError(f"not allowed in a parameter expression: {source!r}")


def _read(animal: str) -> dict:
    with open(PARAMS / f"{animal}.toml", "rb") as f:
        return tomllib.load(f)


def _basis(animal: str, stream: dict) -> str:
    """'S' or 'A' from the leading tag of elas_src; a missing or malformed tag is an error, not a silent default."""
    tag = stream.get("elas_src", "")[:3]
    if tag not in ("[S]", "[A]"):
        raise ValueError(f"{animal}: stream {stream['name']!r} elas_src must start with [S] or [A], got {tag!r}")
    return tag[1]


def load(animal: str, scenario: Optional[str] = None) -> Branch:
    """Build the Branch for `animal` (the file's stem) at `scenario` (default: the file's default_scenario)."""
    data = _read(animal)
    scenarios = data.get("scenarios")
    meta = {k: v for k, v in data.items()
            if k not in ("vars", "derived", "raw_shares", "subs", "derived_subs", "streams", "scenarios", "default_scenario")}
    names = dict(data.get("vars", {}))
    if scenarios:
        scenario = scenario or data["default_scenario"]
        if scenario not in scenarios:
            raise ValueError(f"{animal}: unknown scenario {scenario!r}; available: {', '.join(scenarios)}")
        chosen = dict(scenarios[scenario])
        names.update(chosen.pop("vars", {}))
        meta.update(chosen)
        for field in ("key", "name"):
            meta[field] = meta[field].format(scenario=scenario)
    elif scenario is not None:
        raise ValueError(f"{animal} has no scenarios")

    env = _Names(names)

    def make_sub(d):
        return Sub(d["name"], env.value(d["qty"]), env.value(d["price"]), d["stream"], src=d.get("src", ""))

    subs = [make_sub(d) for d in data["subs"]]
    if "derived_subs" in data:
        env.total = sum(s.value for s in subs)
        for name, raw in data.get("derived", {}).items():
            env.define(name, raw)
        subs += [make_sub(d) for d in data["derived_subs"]]

    streams = [Stream(d["name"], d["route"], d["elas"], d.get("floor"), d.get("floor_note", ""), d.get("elas_src", ""),
                      _basis(animal, d)) for d in data["streams"]]
    raw_shares = {route: env.value(x) for route, x in data["raw_shares"].items()} if "raw_shares" in data else None

    return Branch(meta["key"], meta["name"], meta["unit"], meta["eps_s_sr"], meta["eps_s_lr"], subs, streams,
                  notes=meta.get("notes", ""), supply_src=meta.get("supply_src", ""), price_tag=meta.get("price_tag", ""),
                  raw_shares=raw_shares, monte_carlo=dict(data.get("monte_carlo", {})))


def dairy(scenario="2026"): return load("dairy", scenario)
def eggs(scenario="2019-21"): return load("eggs", scenario)
def beef(): return load("beef")
def broiler(): return load("broiler")
def pork(): return load("pork")
def pollock(): return load("pollock")
def salmon(): return load("salmon")


ALL = [dairy("2026"), dairy("2019"), beef(), eggs("2019-21"), eggs("2025"), broiler(), pork(), pollock(), salmon()]
