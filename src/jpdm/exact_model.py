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

    @staticmethod
    def _preimage(f, t, lo=1e-9, hi=1e3, n=70):
        """(x_lo, x_hi): the interval of x on which the non-increasing continuous f equals t.

        A cap or floor makes f flat, so the preimage of a level can be a whole interval, and a level that f never
        takes (f jumps over it) has an empty interior; bisection on a single side then lands on one edge. Both ends
        are located separately, with no tolerance, and the search-interval edges are returned when f never reaches t.
        """
        flo, fhi = f(lo), f(hi)
        if fhi >= t:
            x_hi = hi
        elif flo < t:
            x_hi = lo
        else:
            a, b = lo, hi
            for _ in range(n):
                m = 0.5 * (a + b)
                if f(m) >= t: a = m
                else: b = m
            x_hi = 0.5 * (a + b)
        if flo <= t:
            x_lo = lo
        elif fhi > t:
            x_lo = hi
        else:
            a, b = lo, hi
            for _ in range(n):
                m = 0.5 * (a + b)
                if f(m) <= t: b = m
                else: a = m
            x_lo = 0.5 * (a + b)
        return min(x_lo, x_hi), x_hi

    def q_bounds(self, r, v, kappa, cap):
        """[q_lo, q_hi]: the set of raw quantities at which route r's value index equals v (an interval where the value is flat)."""
        return self._preimage(lambda q: self.route_value(r, q, kappa, cap), v)

    def q_of_v(self, r, v, kappa, cap):
        return self.q_bounds(r, v, kappa, cap)[1]

    def fixed_value(self, A, kappa, cap):
        return sum(self.s_tot[k] * self.price(k, A, kappa, cap) for k in self.fixed_streams)

    def solve(self, kappa=None, cap=None, eps_s=None, constant_cost=False):
        kappa = kappa or {}
        cap = cap or {}
        eps_s = self.br.eps_s_lr if eps_s is None else eps_s
        Wf = sum(self.W[r] for r in self.fung)

        def A_bounds(v):
            """(A_lo, A_hi): the animal numbers that satisfy the supply condition at fungible-route value v.

            Normally a single point. At constant cost with a capped or floored stream fixed to the animal, supply is
            horizontal over an interval of A at one critical v, so it is a set.
            """
            if constant_cost:
                # P_A = 1 -> fixed(A) = 1 - Wf v ; fixed is non-increasing in A
                return self._preimage(lambda A: self.fixed_value(A, kappa, cap), 1.0 - Wf * v)
            lo, hi = 1e-9, 1e3
            for _ in range(70):
                mid = 0.5 * (lo + hi)
                PA = Wf * v + self.fixed_value(mid, kappa, cap)
                if PA ** eps_s > mid:      # g(A) = P_A^eps_s - A is strictly decreasing: unique root
                    lo = mid
                else:
                    hi = mid
            A = 0.5 * (lo + hi)
            return A, A

        if not self.fung:
            # pure carcass: A from supply = demand
            A = A_bounds(0.0)[0] if not constant_cost else self._preimage(
                lambda x: self.fixed_value(x, kappa, cap), 1.0)[1]
            v = None
            q = {}
        elif constant_cost and not self.fixed_streams:
            v = 1.0 / Wf                        # supply is flat at this value; the animal number follows from balance
            q = {r: self.q_bounds(r, v, kappa, cap)[1] for r in self.fung}
            A = sum(q.values())
        else:
            # find v: sum_r q_hi_r(v) (non-increasing) crosses A_lo(v) (non-decreasing in v)
            lo, hi = 1e-6, 1e3
            for _ in range(70):
                v = 0.5 * (lo + hi)
                if sum(self.q_bounds(r, v, kappa, cap)[1] for r in self.fung) < A_bounds(v)[0]:
                    hi = v
                else:
                    lo = v
            # at the crossing the routes and the supply may each be an interval; pick the point where the totals match
            v = lo
            up = {r: self.q_bounds(r, lo, kappa, cap)[1] for r in self.fung}
            dn = {r: min(self.q_bounds(r, hi, kappa, cap)[0], up[r]) for r in self.fung}
            sU, sL = sum(up.values()), sum(dn.values())
            a_lo, a_hi = A_bounds(lo)[0], A_bounds(hi)[1]
            if constant_cost:
                A = max(min(a_hi, sU), max(a_lo, sL))
            else:
                A = A_bounds(lo)[0]
            th = min(1.0, max(0.0, (A - sL) / (sU - sL))) if sU > sL else 0.0
            q = {r: dn[r] + th * (up[r] - dn[r]) for r in self.fung}
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
