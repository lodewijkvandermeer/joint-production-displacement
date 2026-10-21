"""
Exact (non-linear) constant-elasticity equilibrium for the nested joint-product model, in index form.

Baseline normalisation: every quantity, price and value index equals 1 at the observed equilibrium.
  Animal units A (A0 = 1); raw commodity per animal unit = 1; fungible routes r receive q_r raw units
  (sum_r q_r = A; baseline q_r0 = a_r, the raw-volume shares); streams k in route r produce Q_k = q_r / a_r
  (so Q_k0 = 1). Streams fixed to the animal (carcass parts, cattle sales, spent hen) produce Q_k = A.
  Demand for stream k (food market): Q^d_k = (1 + kappa_k) * P_k^eps_k.   Inverse: P_k = (Q / (1+kappa_k))^(1/eps_k).
  Floor: P_k >= phi_k; the outlet (feed, rendering, export) absorbs Q - Q^d(phi_k) at phi_k.
  Cap (perfect substitute offered at pi_k): P_k <= pi_k; the substitute supplies Q^d(pi_k) - Q when positive.
  Route value per raw unit (index): v_r = sum_{k in r} S_k * P_k, S_k = stream share of route value (sum = 1).
  Processors allocate raw commodity so that v_r is equal across routes (the baseline relative values persist,
  i.e. the classified-pricing structure is kept): v_r(q_r) = v for all routes with q_r > 0.
  Farm price index: P_A = sum_r W_r v + sum_{fixed k} s_k P_k(A);  supply: A = P_A^eps_s  (or P_A = 1 in the constant-cost limit).

The model is the exact counterpart of the log-differential EDM in edm_model.py and reduces to it for small shifts.
"""
import math
from typing import Dict, Optional
from . import edm_model as M

BIG = 1e9


class Exact:
    def __init__(self, br: M.Branch, raw_shares: Optional[Dict[str, float]] = None):
        self.br = br
        self.raw = raw_shares or {}
        T = br.total()
        self.streams = [k.name for k in br.streams]
        self.eps = {k.name: k.elas for k in br.streams}
        self.phi = {k.name: (k.floor_ratio if (k.floor_ratio is not None and 0 < k.floor_ratio < 1) else 0.0) for k in br.streams}
        self.route_of = {k.name: k.route for k in br.streams}
        self.s_tot = {k.name: br.stream_value(k.name) / T for k in br.streams}          # share of animal value
        self.S = {k.name: br.S(k.name) for k in br.streams}                            # share within route
        self.W = {r: br.W(r) for r in br.routes()}
        self.fung = [r for r in br.routes() if r in self.raw]
        self.fixed_streams = [k for k in self.streams if self.route_of[k] not in self.raw]
        if self.fung:
            tot = sum(self.raw[r] for r in self.fung)
            self.a = {r: self.raw[r] / tot for r in self.fung}
        else:
            self.a = {}

    # ---- stream price given its quantity index, with shift, floor and cap
    def price(self, k, Q, kappa, cap):
        e = self.eps[k]
        p = (max(Q, 1e-12) / (1.0 + kappa.get(k, 0.0))) ** (1.0 / e)
        p = max(p, self.phi[k])
        c = cap.get(k)
        if c is not None:
            p = min(p, c)
        return p

    def route_value(self, r, q, kappa, cap):
        return sum(self.S[k] * self.price(k, q / self.a[r], kappa, cap) for k in self.streams if self.route_of[k] == r)

    def q_bounds(self, r, v, kappa, cap, tol=1e-9):
        """[q_lo, q_hi]: the set of raw quantities at which route r's value index equals v (an interval where the value is flat)."""
        lo, hi = 1e-9, 1e3
        if self.route_value(r, hi, kappa, cap) >= v - tol:    # value never falls to v: route absorbs everything
            return hi, hi
        if self.route_value(r, lo, kappa, cap) <= v + tol:    # value never reaches v: route gets nothing
            return lo, lo
        # q_hi: largest q with value >= v - tol
        a, b = lo, hi
        for _ in range(60):
            m = 0.5 * (a + b)
            if self.route_value(r, m, kappa, cap) >= v - tol: a = m
            else: b = m
        q_hi = 0.5 * (a + b)
        # q_lo: smallest q with value <= v + tol
        a, b = lo, hi
        for _ in range(60):
            m = 0.5 * (a + b)
            if self.route_value(r, m, kappa, cap) <= v + tol: b = m
            else: a = m
        q_lo = 0.5 * (a + b)
        return min(q_lo, q_hi), q_hi

    def q_of_v(self, r, v, kappa, cap):
        return self.q_bounds(r, v, kappa, cap)[1]

    def fixed_value(self, A, kappa, cap):
        return sum(self.s_tot[k] * self.price(k, A, kappa, cap) for k in self.fixed_streams)

    def solve(self, kappa=None, cap=None, eps_s=None, constant_cost=False):
        kappa = kappa or {}
        cap = cap or {}
        eps_s = self.br.eps_s_lr if eps_s is None else eps_s
        Wf = sum(self.W[r] for r in self.fung)

        def A_given_v(v):
            # A = (Wf v + fixed(A))^eps_s ; RHS decreasing in A -> bisection
            if constant_cost:
                # P_A = 1 -> fixed(A) = 1 - Wf v ; fixed decreasing in A
                target = 1.0 - Wf * v
                if not self.fixed_streams:
                    return None  # determined by balance alone
                lo, hi = 1e-9, 1e3
                for _ in range(70):
                    mid = 0.5 * (lo + hi)
                    if self.fixed_value(mid, kappa, cap) > target:
                        lo = mid
                    else:
                        hi = mid
                return 0.5 * (lo + hi)
            lo, hi = 1e-9, 1e3
            for _ in range(70):
                mid = 0.5 * (lo + hi)
                PA = Wf * v + self.fixed_value(mid, kappa, cap)
                As = PA ** eps_s
                if As > mid:
                    lo = mid
                else:
                    hi = mid
            return 0.5 * (lo + hi)

        if not self.fung:
            # pure carcass: A from supply = demand
            if constant_cost:
                lo, hi = 1e-9, 1e3
                for _ in range(70):
                    mid = 0.5 * (lo + hi)
                    if self.fixed_value(mid, kappa, cap) > 1.0:
                        lo = mid
                    else:
                        hi = mid
                A = 0.5 * (lo + hi)
            else:
                A = A_given_v(0.0)
            v = None
            q = {}
        else:
            # find v: sum_r q_hi_r(v) (decreasing) = A(v) (increasing)
            lo, hi = 1e-6, 1e3
            v = None
            for _ in range(70):
                v = 0.5 * (lo + hi)
                if constant_cost and not self.fixed_streams:
                    v = 1.0 / Wf
                    A = sum(self.q_bounds(r, v, kappa, cap)[1] for r in self.fung)
                    break
                A = A_given_v(v)
                Qhi = sum(self.q_bounds(r, v, kappa, cap)[1] for r in self.fung)
                if Qhi < A: hi = v
                else: lo = v
            else:
                v = lo            # the feasible side of any discontinuity (flat route at v)
                A = A_given_v(v)
            bounds = {r: self.q_bounds(r, v, kappa, cap) for r in self.fung}
            q = {r: b[0] for r, b in bounds.items()}
            resid = A - sum(q.values())
            slack = {r: max(0.0, b[1] - b[0]) for r, b in bounds.items()}
            tot_slack = sum(slack.values())
            if resid > 0 and tot_slack > 0:
                for r in self.fung:
                    q[r] += resid * slack[r] / tot_slack
            tot = sum(q.values())
            if tot > 0:
                q = {r: x * A / tot for r, x in q.items()}
        # outputs
        out = dict(A=A, v=v, q=q, P={}, Q={}, cons={}, outlet={}, sub={}, sub_share={})
        for k in self.streams:
            r = self.route_of[k]
            Qk = A if k in self.fixed_streams else q[r] / self.a[r]
            Pk = self.price(k, Qk, kappa, cap)
            Qd = (1.0 + kappa.get(k, 0.0)) * Pk ** self.eps[k]   # food demand at Pk
            out["Q"][k] = Qk
            out["P"][k] = Pk
            if k in cap and Pk >= cap[k] - 1e-12 and Qd > Qk:
                out["sub"][k] = Qd - Qk
                out["sub_share"][k] = (Qd - Qk) / Qd
                out["cons"][k] = Qk
                out["outlet"][k] = 0.0
            elif Pk <= self.phi[k] + 1e-12 and Qd < Qk:
                out["outlet"][k] = Qk - Qd
                out["cons"][k] = Qd
                out["sub"][k] = 0.0
                out["sub_share"][k] = 0.0
            else:
                out["cons"][k] = Qk
                out["outlet"][k] = 0.0
                out["sub"][k] = 0.0
                out["sub_share"][k] = 0.0
        out["PA"] = (sum(self.W[r] * v for r in self.fung) if self.fung else 0.0) + self.fixed_value(A, kappa, cap)
        out["revenue"] = out["PA"]   # revenue per animal unit, index
        out["diag"] = self.residuals(out, kappa, cap, eps_s, constant_cost)
        return out

    def residuals(self, out, kappa, cap, eps_s, constant_cost, edge=2e-9):
        """How well a solution satisfies the model's own equilibrium conditions (all ~0 for a true equilibrium).

        supply   : A = P_A^eps_s (or P_A = 1 at constant cost)
        balance  : the raw quantities sent to the fungible routes add up to A
        value    : every route that receives raw commodity has the common value v
        boundary : the solution sits on the edge of the solver's search interval, so it is an exit (A ~ 0) or an
                   unbounded supply rather than a located root
        """
        A, v, q = out["A"], out["v"], out["q"]
        boundary = A <= edge or A >= 1e3 * (1 - 1e-9)
        supply = abs(out["PA"] - 1.0) if constant_cost else abs(A - out["PA"] ** eps_s)
        value = max([abs(self.route_value(r, x, kappa, cap) - v) for r, x in q.items() if x > 1e-6] or [0.0])
        return dict(supply=0.0 if boundary else supply, balance=abs(sum(q.values()) - A) if q else 0.0,
                    value=value, boundary=boundary)


def exact_for(br: M.Branch):
    return Exact(br, br.raw_shares)


def validate():
    """Compare the exact solution with the closed form for 10% and 25% shifts (printed)."""
    from . import params
    # validation: volume shift vs EDM closed form
    for br in [params.dairy("2026"), params.eggs("2019-21"), params.broiler(), params.beef(), params.pork()]:
        ex = exact_for(br)
        print("==", br.name)
        for k in ex.streams:
            for shift in (-0.10, -0.25):
                res = ex.solve(kappa={k: shift})
                df = br.DF_stream(k, br.eps_s_lr)
                # closed form with floor cap
                print(f"  {k[:28]:28s} shift {shift:+.2f}: exact dA {res['A']-1:+.4f}  EDM {df*shift:+.4f}  P_k {res['P'][k]:.3f}  outlet {res['outlet'][k]:.3f}")
