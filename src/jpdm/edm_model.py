"""
Nested joint-product equilibrium displacement model (EDM) with floor prices.

Structure per animal unit:
  animal A  -->  FIXED streams k (value share s_k of the animal; Q_k = A: carcass parts, cattle sales, spent hens)
            -->  a RAW commodity (value share W_raw; one unit per animal) allocated across fungible ROUTES r
                 (raw-volume shares a_r: milk to fluid / cheese / butter-powder / other; eggs to shell / breaking)
  route r   --(fixed proportions across STREAMS k, value shares S_k within r; Houck 1964)-->  stream k
  stream k  --(fungible across SUB-PRODUCTS i, shares w_i within k)-->  sub-product i

Log-differential equilibrium (E(x) = dx/x), proportional processing margins:
  Route derived-demand elasticity (Houck, value-weighted harmonic mean):  eps_r = -1 / sum_k (S_k / |eps_k|)
  Quantity-equivalent shift on route r from a shift kappa_k on stream k:   kappa_r = |eps_r| * S_k * kappa_k / |eps_k|
  Raw-commodity demand elasticity (fungible routes, VOLUME-weighted):        eps_raw = sum_r a_r * eps_r
  Animal-level: H = sum_fixed s_k/|eps_k| + W_raw/|eps_raw|;  eps_bar = -1/H
  Animal quantity: E(A) = eps_s [ sum_fixed (s_k/|eps_k|) kappa_k + (W_raw/|eps_raw|) sum_r a_r kappa_r ] / (1 + eps_s H)
  Displacement factor:  fixed stream k:          DF_k = eps_s (s_k/|eps_k|) / (1 + eps_s H)
                        stream k in route r:     DF_k = eps_s (W_raw/|eps_raw|) a_r |eps_r| (S_k/|eps_k|) / (1 + eps_s H)
                        sub-product i in k:      DF_i = w_i * DF_k
                        bundle (all products):   DF = eps_s H / (1 + eps_s H) = eps_s / (eps_s + |eps_bar|)
  Constant-cost limit (eps_s -> infinity): DF_k -> (its numerator weight) / H, the product's weight in the animal's demand.
Limiting cases:
  all streams fixed             -> DF_k = eps_s (s_k/|eps_k|) / (1 + eps_s H_fixed), H_fixed = sum s_k/|eps_k|   (Houck)
  every stream its own route    -> DF_k = eps_s s_k / (eps_s + |sum_k s_k eps_k|)                                (fully fungible)
  single product                -> DF = eps_s / (eps_s + |eps_d|)                                                (Norwood & Lusk)
Prices after a shift kappa_k on stream k (others zero):
  E(P_A) = E(A)/eps_s;  raw price E(P_raw) = (E(A) - sum_r a_r kappa_r)/eps_raw;  route quantity E(Q_r) = eps_r E(P_raw) + kappa_r;
  stream price E(P_k) = (E(Q_r) - kappa_k)/eps_k;  other streams in the same route E(P_j) = E(Q_r)/eps_j;
  streams in other routes E(P_j) = E(P_raw);  fixed streams E(P_j) = E(A)/eps_j.
NOTE: an earlier version weighted routes by value shares W_r instead of raw-volume shares a_r; the two coincide when every
route pays the same per raw unit (carcasses) and differ where they do not (eggs: a shell egg is worth twice a breaking egg).
Floor: stream k has an external outlet at price ratio phi_k = P_floor/P_k. Using the constant-elasticity (log) form,
  the stream reaches its floor at kappa_floor = exp( ln(phi_k) / g_k ) - 1, where g_k = E(P_k)/kappa_k (price response per unit shift).
  Beyond the floor the outlet absorbs the quantity at the floor and further shifts in k do not move the animal.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import math

@dataclass
class Sub:
    name: str
    qty: float
    price: float
    stream: str
    note: str = ""
    src: str = ""
    @property
    def value(self): return self.qty*self.price

@dataclass
class Stream:
    name: str
    route: str
    elas: float            # own-price demand elasticity (<0)
    floor_ratio: Optional[float] = None   # None = no external floor (internal re-routing handled by routes)
    floor_note: str = ""
    elas_src: str = ""
    basis: str = ""        # "S" sourced or "A" assumed; set by the parameter loader, used to size Monte Carlo spreads

@dataclass
class Branch:
    key: str
    name: str
    unit: str
    eps_s_sr: float
    eps_s_lr: float
    subs: List[Sub]
    streams: List[Stream]
    notes: str = ""
    supply_src: str = ""
    price_tag: str = ""
    raw_shares: Optional[dict] = None   # route -> raw-volume share for fungible routes; routes absent are fixed to the animal
    monte_carlo: dict = field(default_factory=dict)   # supply-elasticity spread for the Monte Carlo (see data/monte_carlo.toml)

    # ---- helpers
    def total(self): return sum(s.value for s in self.subs)
    def stream_value(self, k): return sum(s.value for s in self.subs if s.stream == k)
    def route_value(self, r): return sum(self.stream_value(k.name) for k in self.streams if k.route == r)
    def routes(self):
        seen = []
        for k in self.streams:
            if k.route not in seen: seen.append(k.route)
        return seen
    def W(self, r): return self.route_value(r)/self.total()
    def S(self, k):  # stream share within its route
        st = self.get(k); return self.stream_value(k)/self.route_value(st.route)
    def get(self, k): return next(s for s in self.streams if s.name == k)
    def eps_route(self, r):
        return -1.0/sum(self.S(k.name)/abs(k.elas) for k in self.streams if k.route == r)
    # ---- fixed streams vs raw commodity routes
    def fung_routes(self):
        return [r for r in self.routes() if self.raw_shares and r in self.raw_shares]
    def is_fixed(self, k):
        return self.get(k).route not in self.fung_routes()
    def a(self, r):   # raw-volume share of fungible route r
        tot = sum(self.raw_shares[x] for x in self.fung_routes())
        return self.raw_shares[r]/tot
    def W_raw(self): return sum(self.W(r) for r in self.fung_routes())
    def eps_raw(self):
        fr = self.fung_routes()
        return sum(self.a(r)*self.eps_route(r) for r in fr) if fr else None
    def H(self):
        h = sum(self.stream_value(k.name)/self.total()/abs(k.elas) for k in self.streams if self.is_fixed(k.name))
        if self.fung_routes(): h += self.W_raw()/abs(self.eps_raw())
        return h
    def eps_bar(self): return -1.0/self.H()
    def H_fixed(self):  # all-fixed Houck H over all streams with total shares
        return sum(self.stream_value(k.name)/self.total()/abs(k.elas) for k in self.streams)
    def eps_agg_fixed(self): return -1.0/self.H_fixed()
    def eps_agg_fungible(self): return sum(self.stream_value(k.name)/self.total()*k.elas for k in self.streams)
    def weight(self, k):
        """numerator weight of stream k: fixed s_k/|eps_k|; routed (W_raw/|eps_raw|) a_r |eps_r| S_k/|eps_k|."""
        st = self.get(k)
        if self.is_fixed(k):
            return self.stream_value(k)/self.total()/abs(st.elas)
        r = st.route
        return (self.W_raw()/abs(self.eps_raw()))*self.a(r)*abs(self.eps_route(r))*(self.S(k)/abs(st.elas))

    # ---- displacement factors
    def DF_stream(self, k, eps_s):
        if eps_s is None or eps_s == float("inf"):
            return self.weight(k)/self.H()
        return eps_s*self.weight(k)/(1.0+eps_s*self.H())
    def DF_stream_limit(self, k): return self.weight(k)/self.H()
    def DF_stream_fixed(self, k, eps_s):
        st = self.get(k); s_tot = self.stream_value(k)/self.total()
        return eps_s*(s_tot/abs(st.elas))/(1+eps_s*self.H_fixed())
    def DF_stream_fungible(self, k, eps_s):
        s_tot = self.stream_value(k)/self.total()
        return eps_s*s_tot/(eps_s+abs(self.eps_agg_fungible()))
    def DF_bundle(self, eps_s):   # giving up every product of the animal proportionally
        if eps_s is None or eps_s == float("inf"): return 1.0
        return eps_s*self.H()/(1.0+eps_s*self.H())
    # ---- price responses to a shift on stream k alone (per unit of kappa_k)
    def price_response(self, k, eps_s):
        st = self.get(k)
        DF = self.DF_stream(k, eps_s)
        EA = DF                                   # E(A) per unit kappa_k
        EPA = EA/eps_s if (eps_s and eps_s != float("inf")) else 0.0
        others = {}
        if self.is_fixed(k):
            EPk = (EA - 1.0)/st.elas
            for j in self.streams:
                if j.name == k: continue
                if self.is_fixed(j.name): others[j.name] = EA/j.elas
                else: others[j.name] = EA/self.eps_raw()   # E(P_raw) with no shift on raw routes
            return dict(EPA=EPA, EQr=EA, EPk=EPk, EPraw=EA/self.eps_raw() if self.fung_routes() else None, others=others)
        r = st.route
        eps_r = self.eps_route(r); S = self.S(k)
        kappa_r_per = abs(eps_r)*S/abs(st.elas)             # route shift per unit kappa_k
        EPraw = (EA - self.a(r)*kappa_r_per)/self.eps_raw()
        EQr = eps_r*EPraw + kappa_r_per
        EPk = (EQr - 1.0)/st.elas
        for j in self.streams:
            if j.name == k: continue
            if self.is_fixed(j.name): others[j.name] = EA/j.elas
            elif j.route == r: others[j.name] = EQr/j.elas
            else: others[j.name] = EPraw
        return dict(EPA=EPA, EQr=EQr, EPk=EPk, EPraw=EPraw, others=others)
    def results(self, eps_s, shift=-0.10):
        rows = []
        T = self.total()
        for st in self.streams:
            DF = self.DF_stream(st.name, eps_s)
            pr = self.price_response(st.name, eps_s)
            g = pr["EPk"]
            if st.floor_ratio is None or st.floor_ratio <= 0 or st.floor_ratio >= 1:
                kfloor = None
            else:
                kfloor = math.exp(math.log(st.floor_ratio)/g) - 1.0 if g != 0 else None
            for sub in [x for x in self.subs if x.stream == st.name]:
                w = sub.value/self.stream_value(st.name)
                DFi = w*DF
                # full replacement of sub-product i: stream shift = -w; cap at floor
                full = -w
                if kfloor is not None and kfloor > full: full = kfloor
                full_effect = DF*full
                rows.append(dict(branch=self.name, route=st.route, stream=st.name, sub=sub.name, qty=sub.qty, price=sub.price,
                                 value=sub.value, share_total=sub.value/T, stream_share_total=self.stream_value(st.name)/T,
                                 w=w, elas=st.elas, DF_stream=DF, DF=DFi,
                                 DF_fixed=w*self.DF_stream_fixed(st.name, eps_s), DF_fungible=w*self.DF_stream_fungible(st.name, eps_s),
                                 DF_limit=w*self.DF_stream_limit(st.name),
                                 EA_10=DFi*shift, EP_stream_10=g*w*shift, EP_raw_10=pr["EPA"]*w*shift,
                                 floor_ratio=st.floor_ratio, kappa_floor_stream=kfloor,
                                 kappa_floor_sub=(kfloor/w if kfloor is not None else None),
                                 full_replacement_effect=full_effect, animal_units_per_unit=DFi/sub.qty if sub.qty else None))
        return rows

def single_df(eps_s, eps_d):
    return eps_s/(eps_s+abs(eps_d))

def numeric_check():
    """Exact constant-elasticity equilibrium vs closed form for one route with two fixed streams and two fungible routes."""
    out = []
    # (a) one route, two fixed streams
    eps = [-0.6, -2.0]; y = [1.0, 0.5]; P0 = [1.0, 0.4]; eps_s = 0.8
    A0 = 1.0; a = [y[k]*A0/(P0[k]**eps[k]) for k in range(2)]
    PA0 = sum(y[k]*P0[k] for k in range(2)); b = A0/(PA0**eps_s)
    S = [y[k]*P0[k]/PA0 for k in range(2)]; H = sum(S[k]/abs(eps[k]) for k in range(2))
    def solve(kappa):
        lo, hi = 0.3, 1.7
        for _ in range(200):
            A = 0.5*(lo+hi)
            P = [(y[k]*A/(a[k]*(1+kappa[k])))**(1/eps[k]) for k in range(2)]
            As = b*(sum(y[k]*P[k] for k in range(2)))**eps_s
            if As > A: lo = A
            else: hi = A
        return A
    for k_idx in range(2):
        for shift in [-0.05, -0.10, -0.25]:
            kappa = [0,0]; kappa[k_idx] = shift
            A = solve(kappa); DF = eps_s*(S[k_idx]/abs(eps[k_idx]))/(1+eps_s*H)
            out.append(("fixed", k_idx, shift, A/A0-1, DF*shift))
    # (b) two fungible routes: Q_r = a_r (P_M)^eps_r (1+kappa_r), A = b P_M^eps_s, A = Q_1 + Q_2 (milk units)
    eps_r = [-0.4, -1.5]; W = [0.6, 0.4]; eps_s = 0.9; PM0 = 1.0; A0 = 1.0
    a = [W[r]*A0 for r in range(2)]; b = A0
    eps_bar = sum(W[r]*eps_r[r] for r in range(2))
    def solve2(kappa):
        lo, hi = 0.3, 1.7
        for _ in range(200):
            PM = 0.5*(lo+hi)
            Qd = sum(a[r]*PM**eps_r[r]*(1+kappa[r]) for r in range(2)); Qs = b*PM**eps_s
            if Qs > Qd: hi = PM
            else: lo = PM
        return b*PM**eps_s
    for r_idx in range(2):
        for shift in [-0.05, -0.10, -0.25]:
            kappa = [0,0]; kappa[r_idx] = shift
            A = solve2(kappa); DF = eps_s*W[r_idx]/(eps_s+abs(eps_bar))
            out.append(("fungible", r_idx, shift, A/A0-1, DF*shift))
    return out

if __name__ == "__main__":
    for r in numeric_check():
        print("%-9s stream/route %d shift %+.2f | exact dA/A %.5f vs closed form %.5f" % r)
