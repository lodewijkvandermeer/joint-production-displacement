"""Build the editable Excel model from data/params/*.toml (same defaults as the Python model), with live formulas."""
import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import BarChart, Reference
from openpyxl.comments import Comment
from .params import ALL, dairy, eggs
from .sources import SOURCES
from .paths import RESULTS, WORKBOOK

VERSION_DATE = "2026-10-17"   # date of the parameter snapshot; fixed so that rebuilds are identical
FONT = "Arial"
BLUE = Font(name=FONT, color="0000FF", size=10)
BLACK = Font(name=FONT, color="000000", size=10)
GREEN = Font(name=FONT, color="008000", size=10)
BOLD = Font(name=FONT, bold=True, size=10)
H1 = Font(name=FONT, bold=True, size=14)
H2 = Font(name=FONT, bold=True, size=11, color="FFFFFF")
HDR_FILL = PatternFill("solid", fgColor="1F3864")
SUB_FILL = PatternFill("solid", fgColor="D9E1F2")
YELLOW = PatternFill("solid", fgColor="FFFF00")
GREY = PatternFill("solid", fgColor="F2F2F2")
WRAP = Alignment(wrap_text=True, vertical="top")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

PCT = "0.0%"; PCT2 = "0.00%"; DF3 = "0.000"; DF4 = "0.0000"; NUM2 = "#,##0.00"; NUM3 = "#,##0.000"; NUM0 = "#,##0"

def hdr(ws, row, col, text, width=None):
    c = ws.cell(row=row, column=col, value=text); c.font = H2; c.fill = HDR_FILL; c.alignment = Alignment(wrap_text=True, vertical="center")
    if width: ws.column_dimensions[L(col)].width = width
    return c

def put(ws, row, col, value, font=BLACK, fmt=None, fill=None, wrap=False, comment=None):
    c = ws.cell(row=row, column=col, value=value); c.font = font
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    if wrap: c.alignment = WRAP
    if comment: c.comment = Comment(comment, "model")
    return c

def section(ws, row, text):
    c = ws.cell(row=row, column=1, value=text); c.font = Font(name=FONT, bold=True, size=12, color="1F3864")
    return row+1

# --------------------------------------------------------------------------------------------
# Generic branch sheet writer. inputs_writer(ws, start_row) -> (next_row, qty_formula_fn, price_formula_fn)
# where the fns map sub index -> formula string (or None to use the literal value).
# --------------------------------------------------------------------------------------------
def write_branch(wb, br, sheetname, assump_row, inputs_writer=None, protein=None, unit_factor_note="", chart_title=None):
    ws = wb.create_sheet(sheetname)
    ws.sheet_properties.tabColor = "1F3864"
    for col, w in zip("ABCDEFGHIJKLMNOPQRSTUVW", [52,26,20,12,16,12,14,12,10,10,10,10,10,10,10,10,12,12,12,12,12,12,40]):
        ws.column_dimensions[col].width = w
    put(ws, 1, 1, br.name, H1)
    put(ws, 2, 1, "Unit of analysis: " + br.unit, BLACK)
    put(ws, 3, 1, "Structure: " + br.notes, BLACK, wrap=False)
    put(ws, 4, 1, "Prices: " + br.price_tag, BLACK)
    put(ws, 5, 1, "Supply elasticity sources: " + br.supply_src, BLACK)
    # globals block
    put(ws, 7, 1, "Animal supply elasticity, short run (eps_s SR)", BOLD)
    put(ws, 7, 2, f"=Assumptions!$C${assump_row}", GREEN, DF3)
    put(ws, 8, 1, "Animal supply elasticity, long run (eps_s LR)", BOLD)
    put(ws, 8, 2, f"=Assumptions!$D${assump_row}", GREEN, DF3)
    put(ws, 9, 1, "Demand shift applied to one product at a time (share of its market, negative = replacement)", BOLD)
    put(ws, 9, 2, "=Assumptions!$C$4", GREEN, PCT)
    ES_SR, ES_LR, SHIFT = "$B$7", "$B$8", "$B$9"
    r = 11
    raw_map = {}
    if inputs_writer:
        out = inputs_writer(ws, r)
        r, qty_f, price_f = out[0], out[1], out[2]
        if len(out) > 3 and out[3]: raw_map = out[3]
    else:
        qty_f = price_f = lambda i: None
    # ---------------- sub-product table ----------------
    r = section(ws, r, "A. Products of one unit of the animal (sub-products). Blue = editable inputs; black = formulas.")
    heads = ["Sub-product", "Stream (fixed proportion within route)", "Route (fungible use of the raw commodity, or fixed to the animal)", "Quantity per unit", "Quantity unit",
             "Price", "Price unit", "Value", "Share of animal value", "Protein content (share of mass)", "w: share within stream",
             "DF short run (within a year)", "DF long run (3-5 years)", "DF constant-cost limit (supply perfectly elastic)", "DF LR, all-fixed variant", "DF LR, all-fungible variant",
             "Stream price change for the shift in col. B9", "Farm (animal) price change for that shift", "Shift at which stream hits its floor (as % of this product)",
             "Animal change if this product is fully replaced (LR, floor-capped, linear)", "kg animal unit displaced per kg product (LR)", "kg animal unit per kg protein replaced (LR)", "Source / note"]
    for j, h in enumerate(heads, 1): hdr(ws, r, j, h)
    ws.row_dimensions[r].height = 72
    sub0 = r+1; n = len(br.subs); sub1 = sub0+n-1
    st0 = sub1+5; ns = len(br.streams); st1 = st0+ns-1
    routes = br.routes(); rt0 = st1+5; nr = len(routes); rt1 = rt0+nr-1
    agg0 = rt1+3
    TOTAL = f"$H${sub1+1}"
    EBAR = f"$B${agg0+1}"; HFIX = f"$B${agg0+2}"; EFUN = f"$B${agg0+3}"; WRAW = f"$B${agg0+8}"; ERAW = f"$B${agg0+9}"; HH = f"$B${agg0+10}"
    for i, s in enumerate(br.subs):
        row = sub0+i
        put(ws, row, 1, s.name, BLACK, wrap=True)
        put(ws, row, 2, s.stream, BLACK)
        put(ws, row, 3, br.get(s.stream).route, BLACK)
        qf = qty_f(i)
        put(ws, row, 4, qf if qf else s.qty, BLACK if qf else BLUE, NUM3)
        put(ws, row, 5, s.note or "", BLACK)
        pf = price_f(i)
        put(ws, row, 6, pf if pf else s.price, BLACK if pf else BLUE, NUM2)
        put(ws, row, 7, "", BLACK)
        put(ws, row, 8, f"=D{row}*F{row}", BLACK, NUM3)
        put(ws, row, 9, f"=H{row}/{TOTAL}", BLACK, PCT)
        put(ws, row, 10, (protein or {}).get(s.name, ""), BLUE, PCT)
        put(ws, row, 11, f"=IF(SUMIF($B${sub0}:$B${sub1},B{row},$H${sub0}:$H${sub1})=0,0,H{row}/SUMIF($B${sub0}:$B${sub1},B{row},$H${sub0}:$H${sub1}))", BLACK, DF3)
        def lk(col):  # lookup into the stream table by stream name
            return f"INDEX(${col}${st0}:${col}${st1},MATCH(B{row},$A${st0}:$A${st1},0))"
        put(ws, row, 12, f"=K{row}*{lk('L')}", BLACK, DF4)
        put(ws, row, 13, f"=K{row}*{lk('M')}", BLACK, DF4)
        put(ws, row, 14, f"=K{row}*{lk('N')}", BLACK, DF4)
        put(ws, row, 15, f"=K{row}*{lk('O')}", BLACK, DF4)
        put(ws, row, 16, f"=K{row}*{lk('P')}", BLACK, DF4)
        put(ws, row, 17, f"={lk('Q')}*K{row}*{SHIFT}", BLACK, PCT)
        put(ws, row, 18, f"={lk('R')}*K{row}*{SHIFT}", BLACK, PCT2)
        put(ws, row, 19, f"=IF({lk('S')}=\"\",\"no external floor\",{lk('S')}/K{row})", BLACK, PCT)
        put(ws, row, 20, f"={lk('M')}*IF({lk('S')}=\"\",-K{row},MAX(-K{row},{lk('S')}))", BLACK, PCT2)
        put(ws, row, 21, f"=IF(D{row}=0,\"\",M{row}/D{row}*{UNITF(br)})", BLACK, NUM2)
        put(ws, row, 22, f"=IF(OR(J{row}=\"\",J{row}=0),\"\",U{row}/J{row})", BLACK, NUM2)
        put(ws, row, 23, s.src, BLACK, wrap=True)
    put(ws, sub1+1, 1, "Total value of one unit of the animal", BOLD)
    put(ws, sub1+1, 8, f"=SUM(H{sub0}:H{sub1})", BOLD, NUM3)
    put(ws, sub1+1, 9, f"=SUM(I{sub0}:I{sub1})", BOLD, PCT)
    put(ws, sub1+2, 1, "Column U: " + (unit_factor_note or "animal-unit mass per unit of product; same ratio in any mass unit."), BLACK)
    # ---------------- stream table ----------------
    section(ws, st0-1, "B. Streams (the fixed-proportion joint products within a route). Edit demand elasticities and floor ratios here.")
    sh = ["Stream", "Route", "Stream value", "Share of animal value", "S_k: share within route", "Own-price demand elasticity (eps_k)", "Floor price ratio (P_floor / P_now; blank = no external floor)",
          "Floor: next-best use", "S_k / |eps_k|", "Route demand elasticity eps_r", "M_r: route weight multiplier (table C)", "DF stream, short run", "DF stream, long run",
          "DF stream, constant-cost limit", "DF LR all-fixed (Houck)", "DF LR all-fungible", "g_k: stream price change per unit shift (LR)", "Farm price change per unit shift (LR)",
          "Shift at which stream price reaches the floor (LR)", "a_r: raw-volume share of the route (blank = fixed to the animal)", "Elasticity source"]
    for j, h in enumerate(sh, 1): hdr(ws, st0-1, j, h)
    ws.row_dimensions[st0-1].height = 72
    for i, st in enumerate(br.streams):
        row = st0+i
        put(ws, row, 1, st.name, BLACK); put(ws, row, 2, st.route, BLACK)
        put(ws, row, 3, f"=SUMIF($B${sub0}:$B${sub1},A{row},$H${sub0}:$H${sub1})", BLACK, NUM3)
        put(ws, row, 4, f"=C{row}/{TOTAL}", BLACK, PCT)
        put(ws, row, 5, f"=C{row}/SUMIF($B${st0}:$B${st1},B{row},$C${st0}:$C${st1})", BLACK, PCT)
        put(ws, row, 6, st.elas, BLUE, NUM2)
        put(ws, row, 7, st.floor_ratio if st.floor_ratio is not None else "", BLUE, PCT)
        put(ws, row, 8, st.floor_note, BLACK, wrap=True)
        put(ws, row, 9, f"=E{row}/ABS(F{row})", BLACK, DF3)
        put(ws, row, 10, f"=INDEX($G${rt0}:$G${rt1},MATCH(B{row},$A${rt0}:$A${rt1},0))", BLACK, DF3)
        put(ws, row, 11, f"=INDEX($I${rt0}:$I${rt1},MATCH(B{row},$A${rt0}:$A${rt1},0))", BLACK, DF4)
        put(ws, row, 12, f"={ES_SR}*K{row}*I{row}/(1+{ES_SR}*{HH})", BLACK, DF4)
        put(ws, row, 13, f"={ES_LR}*K{row}*I{row}/(1+{ES_LR}*{HH})", BLACK, DF4)
        put(ws, row, 14, f"=K{row}*I{row}/{HH}", BLACK, DF4)
        put(ws, row, 15, f"={ES_LR}*(D{row}/ABS(F{row}))/(1+{ES_LR}*{HFIX})", BLACK, DF4)
        put(ws, row, 16, f"={ES_LR}*D{row}/({ES_LR}+ABS({EFUN}))", BLACK, DF4)
        put(ws, row, 20, f"=INDEX($E${rt0}:$E${rt1},MATCH(B{row},$A${rt0}:$A${rt1},0))", BLACK, DF3)
        # g_k: fixed stream (M-1)/eps_k ; routed stream: E(P_raw) = (M - a_r*kappa_r)/eps_raw, kappa_r = |eps_r| S/|eps_k| ; E(Q_r) = eps_r E(P_raw) + kappa_r ; g = (E(Q_r)-1)/eps_k
        put(ws, row, 17, f"=IF(T{row}=\"\",(M{row}-1)/F{row},((J{row}*((M{row}-T{row}*ABS(J{row})*I{row})/{ERAW})+ABS(J{row})*I{row})-1)/F{row})", BLACK, DF4)
        put(ws, row, 18, f"=M{row}/{ES_LR}", BLACK, DF4)
        put(ws, row, 19, f"=IF(OR(G{row}=\"\",G{row}<=0,G{row}>=1),\"\",EXP(LN(G{row})/Q{row})-1)", BLACK, PCT)
        put(ws, row, 21, st.elas_src, BLACK, wrap=True)
    # ---------------- route table ----------------
    section(ws, rt0-1, "C. Routes. A route is a fungible use of the raw commodity (enter its raw-volume share in col. D) or a bundle fixed to the animal (leave D blank).")
    for j, h in enumerate(["Route", "Route value", "Route share W_r (value)", "a_r: raw-volume share (blue input; blank = fixed to the animal)", "a_r normalised",
                           "Sum of S_k/|eps_k| over its streams", "Route demand elasticity eps_r = -1/sum", "a_r x eps_r (fungible routes)",
                           "M_r: weight multiplier (fixed: W_r; fungible: (W_raw/|eps_raw|) a_r |eps_r|)", "Contribution to H (fixed routes: W_r/|eps_r|)"], 1): hdr(ws, rt0-1, j, h)
    ws.row_dimensions[rt0-1].height = 72
    for i, rt in enumerate(routes):
        row = rt0+i
        put(ws, row, 1, rt, BLACK)
        put(ws, row, 2, f"=SUMIF($C${sub0}:$C${sub1},A{row},$H${sub0}:$H${sub1})", BLACK, NUM3)
        put(ws, row, 3, f"=B{row}/{TOTAL}", BLACK, PCT)
        if br.raw_shares and rt in br.raw_shares:
            rf = raw_map.get(rt)
            put(ws, row, 4, rf if rf else br.raw_shares[rt], BLACK if rf else BLUE, DF3)
        else:
            put(ws, row, 4, "", BLUE)
        put(ws, row, 5, f"=IF(D{row}=\"\",\"\",D{row}/SUM($D${rt0}:$D${rt1}))", BLACK, DF3)
        put(ws, row, 6, f"=SUMIF($B${st0}:$B${st1},A{row},$I${st0}:$I${st1})", BLACK, DF3)
        put(ws, row, 7, f"=-1/F{row}", BLACK, DF3)
        put(ws, row, 8, f"=IF(E{row}=\"\",\"\",E{row}*G{row})", BLACK, DF3)
        put(ws, row, 9, f"=IF(E{row}=\"\",C{row},({WRAW}/ABS({ERAW}))*E{row}*ABS(G{row}))", BLACK, DF4)
        put(ws, row, 10, f"=IF(E{row}=\"\",C{row}/ABS(G{row}),\"\")", BLACK, DF4)
    # ---------------- aggregates ----------------
    section(ws, agg0-1, "D. Aggregates")
    put(ws, agg0, 1, "Total value of one animal unit", BOLD); put(ws, agg0, 2, f"={TOTAL}", BLACK, NUM3)
    put(ws, agg0+1, 1, "eps_bar: animal-level derived-demand elasticity = -1/H", BOLD); put(ws, agg0+1, 2, f"=-1/B{agg0+10}", BLACK, DF3)
    put(ws, agg0+2, 1, "H_fixed: sum of (share / |eps|) over all streams (all-fixed Houck variant)", BOLD); put(ws, agg0+2, 2, f"=SUMPRODUCT(D{st0}:D{st1}/ABS(F{st0}:F{st1}))", BLACK, DF3)
    put(ws, agg0+3, 1, "eps_fungible: value-weighted arithmetic mean of stream elasticities (all-fungible variant)", BOLD); put(ws, agg0+3, 2, f"=SUMPRODUCT(D{st0}:D{st1},F{st0}:F{st1})", BLACK, DF3)
    put(ws, agg0+4, 1, "Houck aggregate derived-demand elasticity of the animal (all-fixed): -1/H_fixed", BOLD); put(ws, agg0+4, 2, f"=-1/B{agg0+2}", BLACK, DF3)
    put(ws, agg0+5, 1, "DF bundle, short run: animal reduction per unit of proportional reduction in ALL its products (the 'cumulative elasticity' of a full boycott) = eps_s H/(1+eps_s H)", BOLD); put(ws, agg0+5, 2, f"={ES_SR}*B{agg0+10}/(1+{ES_SR}*B{agg0+10})", BLACK, DF3)
    put(ws, agg0+6, 1, "DF bundle, long run", BOLD); put(ws, agg0+6, 2, f"={ES_LR}*B{agg0+10}/(1+{ES_LR}*B{agg0+10})", BLACK, DF3)
    put(ws, agg0+7, 1, "Check: sum of stream DF (LR) equals DF bundle (LR)", BOLD); put(ws, agg0+7, 2, f"=SUM(M{st0}:M{st1})", BLACK, DF3)
    put(ws, agg0+8, 1, "W_raw: value share of the raw commodity (sum of fungible routes)", BOLD); put(ws, agg0+8, 2, f"=SUMPRODUCT(--(E{rt0}:E{rt1}<>\"\"),C{rt0}:C{rt1})", BLACK, DF4)
    put(ws, agg0+9, 1, "eps_raw: raw-commodity demand elasticity = sum_r a_r eps_r over fungible routes", BOLD); put(ws, agg0+9, 2, f"=IF(B{agg0+8}=0,\"\",SUM(H{rt0}:H{rt1}))", BLACK, DF3)
    put(ws, agg0+10, 1, "H: sum over fixed routes of W_r/|eps_r| plus W_raw/|eps_raw| (animal-level inelasticity)", BOLD); put(ws, agg0+10, 2, f"=SUM(J{rt0}:J{rt1})+IF(B{agg0+8}=0,0,B{agg0+8}/ABS(B{agg0+9}))", BLACK, DF4)
    # ---------------- chart ----------------
    if chart_title:
        ch = BarChart(); ch.type = "col"; ch.grouping = "clustered"; ch.title = chart_title; ch.y_axis.title = "Share of animal value"; ch.y_axis.number_format = "0%"
        data = Reference(ws, min_col=4, min_row=st0-1, max_row=st1); cats = Reference(ws, min_col=1, min_row=st0, max_row=st1)
        ch.add_data(data, titles_from_data=True); ch.set_categories(cats); ch.height = 8; ch.width = 18; ch.legend = None
        ws.add_chart(ch, f"Y{sub0}")
    ws.freeze_panes = "B2"
    return ws, dict(sub0=sub0, sub1=sub1, st0=st0, st1=st1, rt0=rt0, rt1=rt1, agg0=agg0)

def UNITF(br):
    """mass of the animal unit per 'quantity unit' of the product, so that col T = animal mass per product mass."""
    # dairy: qty in lb per 100 lb milk -> animal unit mass = 100 lb (milk) ; beef: per 1,400 lb steer (qty in lb) ; eggs: per dozen (1.5 lb eggs ~ use 1.5 lb egg mass; qty in lb or dozens) ; broiler: 6 lb live ; pork: 280 lb live ; pollock: 1 t ; salmon: 1 kg HOG
    return {"dairy": 100, "beef": 1400, "eggs": 1.5, "broiler": 6, "pork": 280, "pollock": 1, "salmon": 1}[br.key.split("_")[0]]

# --------------------------------------------------------------------------------------------
# Dairy inputs block with scenario selector
# --------------------------------------------------------------------------------------------
def dairy_inputs(ws, r):
    r = section(ws, r, "Inputs (two price scenarios; select 1 = 2026, 2 = 2019-21 in the yellow cell). Values in blue are editable.")
    put(ws, r, 1, "Scenario selector (1 = 2026 prices, 2 = 2019-21 prices)", BOLD); put(ws, r, 2, 1, BLUE, fill=YELLOW); SEL = f"$B${r}"; r += 1
    for j, h in enumerate(["Input", "Live value (used by the model)", "Scenario 1: 2026", "Scenario 2: 2019-21", "Unit", "Source / note"], 1): hdr(ws, r, j, h)
    r += 1
    rows = [  # key, label, v2026, v2019, unit, note
        ("u_fluid","Milk to fluid use (share of raw milk)",0.19,0.19,"share","[E] NASS fluid sales ~43 bn lb of 232 bn lb"),
        ("u_cheese","Milk to cheese (share)",0.60,0.60,"share","[E] 14.8 bn lb cheese / 10.6 lb per cwt / 232 bn lb"),
        ("u_bp","Milk to butter and powder (share)",0.13,0.13,"share","[E] residual"),
        ("u_other","Milk to other manufactured products (share)",0.08,0.08,"share","[E] yogurt, ice cream, etc."),
        ("cheese_yield","Cheddar yield",10.6,10.6,"lb per cwt","[S] Hoard's/CoBank (2020 composition; 11.6 in 2025)"),
        ("whey_solids","Whey solids",6.0,5.9,"lb per cwt cheese milk","[S] FMMO other-solids factor"),
        ("protein_frac","Protein share of whey solids",0.13,0.13,"share","[S] 0.8% protein in 6.5% solids whey"),
        ("rec_protein","Share of whey protein recovered into WPC/WPI",0.50,0.50,"share","[E] NASS 2025 WPC+WPI protein vs liquid whey protein"),
        ("split_wpc80","Of recovered whey protein, share going to WPC(50-90%) (rest WPI), protein basis",0.61,0.61,"share","[S] NASS 2025: 381 m lb WPC x 0.8 vs 214 m lb WPI x 0.9"),
        ("dry_whey_share","Whey solids sold as dry whey (share)",0.10,0.10,"share","[E] 845 m lb / ~8.4 bn lb solids"),
        ("lactose_share","Whey solids sold as lactose (share)",0.15,0.15,"share","[E] 1,137 m lb"),
        ("feed_share","Whey solids to permeate / condensed / feed (share)",0.25,0.25,"share","[E] remainder not recovered as food products"),
        ("classI","Class I price",18.88,17.60,"$/cwt","[S] AMS advanced Class I Oct 2026; 2019-21 approx."),
        ("classII","Class II price",17.60,16.90,"$/cwt","[S] AMS Sep 2026"),
        ("cheese","Cheese price (block/barrel survey)",1.5577,1.75,"$/lb","[S] AMS Sep 2026; 2019 approx."),
        ("bfat","FMMO butterfat price",1.4762,2.30,"$/lb","[S] AMS Sep 2026"),
        ("nfs","FMMO nonfat solids price",1.5343,1.00,"$/lb","[S] AMS Sep 2026"),
        ("wpc80","WPC 80 price",9.50,3.00,"$/lb","[S] DMN Oct 2026 'mostly $9s'; 2019-21 approx. trade level"),
        ("wpi","WPI price",14.0,5.00,"$/lb","[S] DMN Oct 2026 'mostly $14s'; 2019-21 approx."),
        ("drywhey","Dry whey price",0.6694,0.35,"$/lb","[S] AMS Sep 2026; 2019-21 ~0.35"),
        ("lactose","Lactose price",0.70,0.35,"$/lb","[S] DMN Oct 2026 mostly 0.66-0.76"),
        ("feedwhey","Feed-grade whey / permeate price",0.36,0.20,"$/lb","[S] DMN animal-feed dry whey 0.35-0.38"),
        ("mk_cheese","Make allowance: cheese",0.2519,0.2003,"$/lb","[S] FMMO (Jun 2025 / previous)"),
        ("mk_drywhey","Make allowance: dry whey",0.2668,0.1991,"$/lb","[S] FMMO"),
        ("mk_lactose","Processing allowance: lactose",0.27,0.20,"$/lb","[A]"),
        ("mk_wpc80","Processing allowance: WPC 80",1.50,1.20,"$/lb","[A] ultrafiltration + drying"),
        ("mk_wpi","Processing allowance: WPI",2.50,2.00,"$/lb","[A]"),
        ("mk_feed","Processing allowance: feed whey",0.10,0.10,"$/lb","[A]"),
        ("cattle_share","Cattle sales (cull cows + calves) as share of dairy gross value",0.078,0.07,"share","[S] ERS 2024: 1.94 of 24.94 $/cwt"),
        ("cull_split","Cull cows share of cattle sales (rest calves)",0.60,0.60,"share","[E]"),
    ]
    ref = {}
    for key, label, v1, v2, unit, note in rows:
        put(ws, r, 1, label, BLACK); put(ws, r, 2, f"=INDEX(C{r}:D{r},1,{SEL})", BLACK, NUM3 if v1 < 50 else NUM2)
        put(ws, r, 3, v1, BLUE, NUM3); put(ws, r, 4, v2, BLUE, NUM3); put(ws, r, 5, unit, BLACK); put(ws, r, 6, note, BLACK)
        ref[key] = f"$B${r}"; r += 1
    r += 1
    R = ref
    prot = f"{R['whey_solids']}*{R['protein_frac']}*{R['rec_protein']}"
    qty = {0: f"={R['u_fluid']}", 1: f"={R['u_other']}", 2: f"={R['u_bp']}", 3: f"={R['u_bp']}", 4: f"={R['u_cheese']}*{R['cheese_yield']}",
           5: f"={R['u_cheese']}*{prot}*{R['split_wpc80']}/0.8", 6: f"={R['u_cheese']}*{prot}*(1-{R['split_wpc80']})/0.9",
           7: f"={R['u_cheese']}*{R['whey_solids']}*{R['dry_whey_share']}", 8: f"={R['u_cheese']}*{R['whey_solids']}*{R['lactose_share']}",
           9: f"={R['u_cheese']}*{R['whey_solids']}*{R['feed_share']}", 10: "=1", 11: "=1"}
    # milk total (rows 0-9) needed for cattle; compute in a helper cell
    put(ws, r, 1, "Helper: milk value per cwt (sum of milk products, computed below)", BOLD); MILKTOT = f"$B${r}"; helper_row = r; r += 2
    price = {0: f"={R['classI']}", 1: f"={R['classII']}", 2: f"=3.5*{R['bfat']}", 3: f"=9.3*0.965*{R['nfs']}", 4: f"={R['cheese']}-{R['mk_cheese']}",
             5: f"={R['wpc80']}-{R['mk_wpc80']}", 6: f"={R['wpi']}-{R['mk_wpi']}", 7: f"={R['drywhey']}-{R['mk_drywhey']}", 8: f"={R['lactose']}-{R['mk_lactose']}",
             9: f"={R['feedwhey']}-{R['mk_feed']}", 10: f"={MILKTOT}*{R['cattle_share']}/(1-{R['cattle_share']})*{R['cull_split']}",
             11: f"={MILKTOT}*{R['cattle_share']}/(1-{R['cattle_share']})*(1-{R['cull_split']})"}
    raw = {"Fluid": f"={R['u_fluid']}", "Other manufactured": f"={R['u_other']}", "Butter & powder": f"={R['u_bp']}", "Cheese route": f"={R['u_cheese']}"}
    return r, (lambda i: qty.get(i)), (lambda i: price.get(i)), raw, helper_row

def eggs_inputs(ws, r):
    r = section(ws, r, "Inputs (two price scenarios; 1 = 2019-21 normal market, 2 = Sep 2025 HPAI-tight market). Blue = editable.")
    put(ws, r, 1, "Scenario selector (1 = 2019-21, 2 = 2025)", BOLD); put(ws, r, 2, 1, BLUE, fill=YELLOW); SEL = f"$B${r}"; r += 1
    for j, h in enumerate(["Input", "Live value", "Scenario 1: 2019-21", "Scenario 2: 2025", "Unit", "Source / note"], 1): hdr(ws, r, j, h)
    r += 1
    rows = [
        ("shell_share","Table eggs sold in shell (share)",0.68,0.68,"share","[S] NASS/AMS: ~32% broken"),
        ("sep_share","Broken eggs separated into white and yolk (share of broken)",0.36,0.36,"share","[E] NASS white/yolk volumes"),
        ("liquid","Edible liquid per dozen",1.29,1.29,"lb","[S] NASS 2025"),
        ("white_frac","White share of liquid (by mass)",0.58/0.89,0.58/0.89,"share","[S] USDA grading manual 58/31/11"),
        ("shell","Shell egg price, large white, wholesale",0.95,2.08,"$/dozen","[S] AMS; 2019 approx. annual average"),
        ("whole","Liquid whole egg",0.33,1.155,"$/lb","[S] AMS Oct 2019 / Sep 2025"),
        ("white","Liquid egg white",0.23,0.914,"$/lb","[S] AMS"),
        ("yolk","Liquid egg yolk",0.46,3.57,"$/lb","[S] AMS"),
        ("hen","Spent hen value",0.02,0.02,"$/bird","[S] removal cost 0-5 c/head; nominal"),
        ("doz_per_hen","Dozens per hen-year",25,25,"dozen","[E] ~300 eggs"),
    ]
    ref = {}
    for key, label, v1, v2, unit, note in rows:
        put(ws, r, 1, label, BLACK); put(ws, r, 2, f"=INDEX(C{r}:D{r},1,{SEL})", BLACK, NUM3)
        put(ws, r, 3, v1, BLUE, NUM3); put(ws, r, 4, v2, BLUE, NUM3); put(ws, r, 5, unit, BLACK); put(ws, r, 6, note, BLACK)
        ref[key] = f"$B${r}"; r += 1
    r += 1; R = ref
    qty = {0: f"={R['shell_share']}", 1: f"=(1-{R['shell_share']})*(1-{R['sep_share']})*{R['liquid']}",
           2: f"=(1-{R['shell_share']})*{R['sep_share']}*{R['liquid']}*{R['white_frac']}",
           3: f"=(1-{R['shell_share']})*{R['sep_share']}*{R['liquid']}*(1-{R['white_frac']})", 4: f"=1/{R['doz_per_hen']}"}
    price = {0: f"={R['shell']}", 1: f"={R['whole']}", 2: f"={R['white']}", 3: f"={R['yolk']}", 4: f"={R['hen']}"}
    raw = {"Shell": f"={R['shell_share']}", "Products: whole": f"=(1-{R['shell_share']})*(1-{R['sep_share']})", "Products: separated": f"=(1-{R['shell_share']})*{R['sep_share']}"}
    return r, (lambda i: qty.get(i)), (lambda i: price.get(i)), raw

def generic_inputs(rows_spec, qty_map, price_map, title):
    """rows_spec: list of (key,label,value,unit,note). qty_map/price_map: dict sub_index -> formula template using {key} placeholders."""
    def writer(ws, r):
        r = section(ws, r, title)
        for j, h in enumerate(["Input", "Value", "Unit", "Source / note"], 1): hdr(ws, r, j, h)
        r += 1; ref = {}
        for key, label, v, unit, note in rows_spec:
            put(ws, r, 1, label, BLACK); put(ws, r, 2, v, BLUE, NUM3 if abs(v) < 100 else NUM2); put(ws, r, 3, unit, BLACK); put(ws, r, 4, note, BLACK)
            ref[key] = f"$B${r}"; r += 1
        r += 1
        q = {i: "=" + f.format(**ref) for i, f in qty_map.items()}
        p = {i: "=" + f.format(**ref) for i, f in price_map.items()}
        return r, (lambda i: q.get(i)), (lambda i: p.get(i)), None
    return writer

BEEF_ROWS = [("live","Live weight",1400,"lb","[S] AMS drop report: typical steer 1,400 lb"),("dress","Dressing percentage",0.63,"share","[S] AMS 63.0%"),
    ("y_rib","Rib yield (share of carcass)",0.1140,"share","[S] AMS cutout yield factors"),("p_rib","Rib primal value",6.7612,"$/lb","[S] AMS 15 Oct 2026 Choice"),
    ("y_chuck","Chuck yield",0.2962,"share","[S]"),("p_chuck","Chuck primal value",3.3740,"$/lb","[S]"),
    ("y_round","Round yield",0.2232,"share","[S]"),("p_round","Round primal value",2.9522,"$/lb","[S]"),
    ("y_loin","Loin yield",0.2126,"share","[S]"),("p_loin","Loin primal value",4.5003,"$/lb","[S]"),
    ("y_brisket","Brisket yield",0.0495,"share","[S]"),("p_brisket","Brisket primal value",2.8783,"$/lb","[S]"),
    ("y_plate","Short plate yield",0.0710,"share","[S]"),("p_plate","Short plate primal value",2.2219,"$/lb","[S]"),
    ("y_flank","Flank yield",0.0335,"share","[S]"),("p_flank","Flank primal value",1.6028,"$/lb","[S]"),
    ("f_endwm","Share of chuck+round sold as whole-muscle cuts (rest ground)",0.50,"share","[E]"),("u_endwm","Value uplift of whole-muscle end cuts vs primal average",1.05,"x","[A]"),
    ("f_thinwm","Share of thin meats sold whole-muscle (rest ground)",0.40,"share","[E]"),("u_thinwm","Value uplift of whole-muscle thin meats",1.15,"x","[A]"),
    ("d_endgr","Value discount of ground chuck/round vs primal average",0.95,"x","[A]"),("d_thingr","Value discount of ground thin meats",0.90,"x","[A]"),
    ("hide","Drop value: hide",1.75,"$/cwt live","[S] AMS 15 Oct 2026"),("tallow","Drop value: tallow + technical fat",3.86,"$/cwt live","[S]"),
    ("offal","Drop value: edible offal",8.13,"$/cwt live","[S] sum of tongues, cheek, head meat, oxtails, hearts, lips, livers, tripe, lungs, melts"),("meals","Drop value: meat & bone meal + blood meal",1.38,"$/cwt live","[S]")]
BEEF_Q = {0:"{live}*{dress}*({y_rib}+{y_loin})", 1:"{live}*{dress}*({y_chuck}+{y_round})*{f_endwm}", 2:"{live}*{dress}*({y_brisket}+{y_plate}+{y_flank})*{f_thinwm}",
          3:"{live}*{dress}*(({y_chuck}+{y_round})*(1-{f_endwm})+({y_brisket}+{y_plate}+{y_flank})*(1-{f_thinwm}))", 4:"1", 5:"1", 6:"1", 7:"1"}
BEEF_P = {0:"({y_rib}*{p_rib}+{y_loin}*{p_loin})/({y_rib}+{y_loin})", 1:"({y_chuck}*{p_chuck}+{y_round}*{p_round})/({y_chuck}+{y_round})*{u_endwm}",
          2:"({y_brisket}*{p_brisket}+{y_plate}*{p_plate}+{y_flank}*{p_flank})/({y_brisket}+{y_plate}+{y_flank})*{u_thinwm}",
          3:"(({y_chuck}*{p_chuck}+{y_round}*{p_round})*(1-{f_endwm})*{d_endgr}+({y_brisket}*{p_brisket}+{y_plate}*{p_plate}+{y_flank}*{p_flank})*(1-{f_thinwm})*{d_thingr})/(({y_chuck}+{y_round})*(1-{f_endwm})+({y_brisket}+{y_plate}+{y_flank})*(1-{f_thinwm}))",
          4:"{hide}*{live}/100", 5:"{tallow}*{live}/100", 6:"{offal}*{live}/100", 7:"{meals}*{live}/100"}

BROILER_ROWS = [("live","Live weight",6.0,"lb","[S] Cobb 500 poster 2.73 kg"),
    ("y_breast","Breast fillet yield (share of live)",0.2205,"share","[S] Cobb"),("p_breast","B/S breast price",1.486,"$/lb","[S] AMS 24 Jan 2025"),
    ("y_tender","Tenders yield",0.040,"share","[S]"),("p_tender","Tenders price",1.734,"$/lb","[S]"),
    ("y_wing","Wings yield",0.0758,"share","[S]"),("p_wing","Wings price",1.906,"$/lb","[S]"),
    ("y_lq","Whole legs yield (leg quarters less back)",0.2301,"share","[S] Cobb: whole legs 23.01%"),("p_lq","Leg quarters price",0.514,"$/lb","[S]"),
    ("y_back","Backs, necks, frames yield",0.121,"share","[S] back/frame 8.61 + neck 3.50"),("p_back","Backs/necks price",0.125,"$/lb","[S]"),
    ("y_gib","Giblets yield",0.030,"share","[S]"),("p_gib","Giblets price",0.40,"$/lb","[A]"),
    ("y_paw","Paws yield",0.045,"share","[S]"),("p_paw","Paws price",0.60,"$/lb","[E]"),
    ("y_rend","Feathers, blood, viscera, heads yield",0.135,"share","[S]"),("p_rend","Rendering raw-material value",0.08,"$/lb","[E]")]
BROILER_Q = {0:"{live}*{y_breast}",1:"{live}*{y_tender}",2:"{live}*{y_wing}",3:"{live}*{y_lq}",4:"{live}*{y_back}",5:"{live}*{y_gib}",6:"{live}*{y_paw}",7:"{live}*{y_rend}"}
BROILER_P = {0:"{p_breast}",1:"{p_tender}",2:"{p_wing}",3:"{p_lq}",4:"{p_back}",5:"{p_gib}",6:"{p_paw}",7:"{p_rend}"}

PORK_ROWS = [("live","Live weight",280,"lb","[S] AMS by-product report"),("carc","Carcass weight",215,"lb","[S] AMS cutout basis"),
    ("y_loin","Loin yield",0.2517,"share","[S] AMS pork cutout yields"),("p_loin","Loin value",0.879,"$/lb","[S] w/e 25 Sep 2026"),
    ("y_butt","Butt yield",0.1016,"share","[S]"),("p_butt","Butt value",1.115,"$/lb","[S]"),
    ("y_rib","Sparerib yield",0.0481,"share","[S]"),("p_rib","Sparerib value",1.592,"$/lb","[S]"),
    ("y_ham","Ham yield",0.2459,"share","[S]"),("p_ham","Ham value",0.869,"$/lb","[S]"),
    ("y_belly","Belly yield",0.1628,"share","[S]"),("p_belly","Belly value",0.968,"$/lb","[S]"),
    ("y_saus","Picnic + jowl + neck bones + trim yield",0.1451,"share","[S] 11.37+1.45+1.69"),("p_saus","Sausage-material value",0.66,"$/lb","[S] picnic 0.677; [E] blend"),
    ("y_feet","Feet and tails yield",0.0230,"share","[S]"),("p_feet","Feet/tails value",0.50,"$/lb","[A]"),
    ("drop","Hog by-product drop value",5.12,"$/cwt live","[S] AMS 9 Oct 2026")]
PORK_Q = {0:"{carc}*{y_loin}",1:"{carc}*{y_butt}",2:"{carc}*{y_rib}",3:"{carc}*{y_ham}",4:"{carc}*{y_belly}",5:"{carc}*{y_saus}",6:"{carc}*{y_feet}",7:"1"}
PORK_P = {0:"{p_loin}",1:"{p_butt}",2:"{p_rib}",3:"{p_ham}",4:"{p_belly}",5:"{p_saus}",6:"{p_feet}",7:"{drop}*{live}/100"}

POLLOCK_ROWS = [("catch","Catch (round weight)",1430,"kt","[S] 2024 ~1.43 Mt"),
    ("v_fil","Fillets (PBO + deep-skin + other)",168.0,"kt product","[S] NOAA 2024"),("p_fil","Fillet price",4500,"$/t","[E] blocks >$5,000/t EU; fillets $3.35/kg export"),
    ("v_hg","H&G",40.0,"kt","[S]"),("p_hg","H&G price",2000,"$/t","[E]"),
    ("v_sur","Surimi",170.3,"kt","[S]"),("p_sur","Surimi price",2500,"$/t","[S] GAPP $2,200-2,900/t"),
    ("v_min","Mince",24.4,"kt","[S]"),("p_min","Mince price",1500,"$/t","[A]"),
    ("v_roe","Roe",20.8,"kt","[S]"),("p_roe","Roe price",6000,"$/t","[A]"),
    ("v_meal","Fishmeal",69.6,"kt","[S]"),("p_meal","Fishmeal price",1700,"$/t","[S] World Bank 2024-25 avg"),
    ("v_oil","Fish oil",27.4,"kt","[S]"),("p_oil","Fish oil price",2500,"$/t","[E]")]
POLLOCK_Q = {0:"{v_fil}/{catch}",1:"{v_hg}/{catch}",2:"{v_sur}/{catch}",3:"{v_min}/{catch}",4:"{v_roe}/{catch}",5:"{v_meal}/{catch}",6:"{v_oil}/{catch}"}
POLLOCK_P = {0:"{p_fil}",1:"{p_hg}",2:"{p_sur}",3:"{p_min}",4:"{p_roe}",5:"{p_meal}",6:"{p_oil}"}

SALMON_ROWS = [("p_hog","Salmon price, HOG",75.0,"NOK/kg","[S] 2026 YTD spot"),("y_bp","By-products per kg HOG",0.33,"kg","[S] Thunen 2025: 33% of HOG"),("p_bp","By-product value",7.0,"NOK/kg","[S] SINTEF 2023 ~NOK 7/kg utilised")]
SALMON_Q = {0:"1",1:"{y_bp}"}; SALMON_P = {0:"{p_hog}",1:"{p_bp}"}

PROTEIN = {"Fluid milk (Class I)":0.033,"Other dairy: yogurt, ice cream, etc. (Class II)":0.04,"Butter / cream (3.5 lb fat per cwt)":0.005,
           "Nonfat dry milk / SMP (also the casein route)":0.36,"Cheese (cheddar-equivalent)":0.25,"WPC 80 (whey protein concentrate)":0.80,"WPI (whey protein isolate)":0.90,
           "Dry whey (sweet whey powder)":0.12,"Lactose":0.0,"Permeate / condensed whey / feed":0.04,"Cull cows (manufacturing beef)":0.18,"Calves (beef-on-dairy, bull calves)":0.18,
           "Middle meats: steaks and roasts from rib and loin":0.20,"End-meat whole-muscle cuts (chuck/round roasts, steaks; 50% of chuck+round)":0.20,
           "Thin-meat whole-muscle (brisket, flank, skirt; 40% of thin meats)":0.19,"Grinding material: trim and ground chuck/round (minced beef)":0.17,
           "Shell eggs (table)":0.125,"Liquid/frozen whole egg":0.125,"Liquid egg white (albumen): liquid, dried albumen, protein fractions":0.11,"Liquid egg yolk":0.16,
           "Boneless skinless breast (fillets, whole-muscle nuggets)":0.23,"Tenders":0.23,"Wings":0.19,"Leg quarters / dark meat":0.18,
           "Backs, necks, frames -> mechanically separated chicken (MSC nuggets, hot dogs)":0.14,
           "Loin (chops, roasts)":0.21,"Butt (shoulder)":0.18,"Spareribs":0.16,"Ham (mostly cured)":0.20,"Belly (bacon)":0.12,"Picnic, jowl, neck bones, trim -> sausage, ground pork":0.15,
           "Fillet blocks and fillets (fish fingers, portions)":0.17,"H&G (headed and gutted)":0.16,"Surimi (crab sticks, kamaboko)":0.15,"Mince":0.15,"Fishmeal":0.65,
           "Salmon HOG, fillets and portions":0.20}

def build(path=WORKBOOK, results=RESULTS):
    wb = Workbook()
    # ---------------- README ----------------
    ws = wb.active; ws.title = "README"; ws.column_dimensions["A"].width = 120
    lines = [
        ("Joint-production equilibrium displacement model for animal-product markets", H1),
        (f"Version {VERSION_DATE}. Companion workbook to the paper 'Elasticity and joint production in animal-product markets'.", BLACK),
        ("", BLACK),
        ("WHAT IT DOES", BOLD),
        ("For each animal (dairy cow, fed steer, layer hen, broiler, hog, Alaska pollock, farmed salmon) the workbook lists the products of one animal unit, their prices and value shares,", BLACK),
        ("and computes for each product the displacement factor DF: the share of a demand reduction in that product (e.g. by a novel ingredient) that shows up as fewer animals produced,", BLACK),
        ("in the short run and the long run. It also computes the price fall of the product, the floor price (next-best use) for by-products, and the animal reduction if the product were fully replaced.", BLACK),
        ("", BLACK),
        ("HOW TO USE", BOLD),
        ("1. Assumptions sheet: supply elasticities per animal (short run, long run) and the size of the demand shift. Blue cells are inputs.", BLACK),
        ("2. Branch sheets (Dairy, Beef, Eggs, Broiler, Pork, Pollock, Salmon): inputs block (yields, prices, allowances; blue), then table A (products), table B (streams: edit demand elasticities and floor ratios), table C (routes: raw-volume shares of fungible routes), table D (aggregates).", BLACK),
        ("3. Summary sheet: all products side by side, linked (green) to the branch sheets, with three horizons (within a year, 3-5 years, constant-cost limit). Sensitivity sheet: the single-product formula across elasticities, and a target calculator. Exit sheet: price-cap (perfect substitute) scenarios from the exact non-linear model. Ranges sheet: Monte Carlo 10th-90th percentiles over the elasticity ranges. The Exit and Ranges sheets are computed in the companion Python model and pasted as values.", BLACK),
        ("4. Dairy and Eggs have a scenario selector (yellow cell) switching between two price years, because by-product value shares move a lot with prices.", BLACK),
        ("Colour legend: blue = hard-coded input you can edit; black = formula; green = link to another sheet; yellow fill = scenario selector.", BLACK),
        ("", BLACK),
        ("MODEL (log-differential equilibrium displacement model, proportional processing margins)", BOLD),
        ("Animal supply: E(A) = eps_s * E(P_A). Each animal unit yields FIXED streams (carcass parts, cattle sales, spent hens; value shares s_k) and a RAW commodity (milk, eggs; value share W_raw) that processors allocate across fungible routes r with raw-volume shares a_r; streams k within a route are joint products in fixed proportions (shares S_k); sub-products within a stream are fungible (shares w_i).", BLACK),
        ("Route derived-demand elasticity (Houck 1964): eps_r = -1 / sum_k (S_k / |eps_k|).   Raw-commodity demand elasticity: eps_raw = sum_r a_r * eps_r (volume-weighted).   Animal-level inelasticity: H = sum over fixed routes of W_r/|eps_r| + W_raw/|eps_raw|;  eps_bar = -1/H.", BLACK),
        ("Displacement factor of stream k: DF_k = eps_s * M_r * (S_k / |eps_k|) / (1 + eps_s H), with M_r = W_r for a fixed route and M_r = (W_raw/|eps_raw|) a_r |eps_r| for a fungible route.   Sub-product i: DF_i = w_i * DF_k.   Bundle: DF = eps_s H/(1 + eps_s H).   Constant-cost limit (eps_s -> infinity): DF_k -> M_r (S_k/|eps_k|)/H, the product's weight in the animal's demand.", BLACK),
        ("Limiting cases: all streams fixed -> DF_k = eps_s*(s_k/|eps_k|)/(1+eps_s*H_fixed) with H_fixed = sum s_k/|eps_k| (Houck); every stream its own route -> DF_k = eps_s*s_k/(eps_s+|eps_fungible|); single product -> DF = eps_s/(eps_s+|eps_d|).", BLACK),
        ("Price of stream k after a shift kappa_k (per unit): E(A) = DF_k; farm price E(P_A) = E(A)/eps_s; raw price E(P_raw) = (E(A) - a_r kappa_r)/eps_raw with kappa_r = |eps_r| S_k/|eps_k|; route quantity E(Q_r) = eps_r E(P_raw) + kappa_r; stream price E(P_k) = (E(Q_r) - kappa_k)/eps_k (fixed stream: (E(A) - kappa_k)/eps_k).", BLACK),
        ("Floor: a stream with an external outlet (feed, rendering, export at world price) cannot fall below P_floor; the shift at which it gets there is kappa_floor = exp(ln(P_floor/P_now)/g_k) - 1, g_k = E(P_k) per unit shift. Beyond it, further shifts do not move the animal.", BLACK),
        ("Validity: a local (first-order) approximation; checked against exact constant-elasticity equilibria: error < 2% of the effect at a 10% shift, ~5% at 25%. Full-replacement figures are linear extrapolations (upper bounds in magnitude).", BLACK),
        ("", BLACK),
        ("SOURCE TAGS", BOLD),
        ("[S] sourced from public data (URL on the Sources sheet). [E] estimate derived by the author from sourced inputs. [A] assumption / judgement. Demand elasticities for by-product streams are [A] unless marked otherwise; they are the main sensitivity.", BLACK),
        ("Prices are a snapshot (date stated on each sheet). Value shares, and therefore DF, change with relative prices; this is a feature of the problem, not a bug of the workbook.", BLACK),
    ]
    for i, (t, f) in enumerate(lines, 1):
        c = ws.cell(row=i, column=1, value=t); c.font = f; c.alignment = Alignment(wrap_text=True, vertical="top")
    # ---------------- Assumptions ----------------
    wa = wb.create_sheet("Assumptions"); wa.sheet_properties.tabColor = "FFC000"
    for col, w in zip("ABCDE", [44, 16, 14, 14, 90]): wa.column_dimensions[col].width = w
    put(wa, 1, 1, "Global assumptions", H1)
    put(wa, 3, 1, "Demand shift applied to a single product (share of its market; negative = replacement)", BOLD); put(wa, 4, 1, "Shift"); put(wa, 4, 3, -0.10, BLUE, PCT, fill=YELLOW)
    put(wa, 6, 1, "Animal supply elasticities", BOLD)
    for j, h in enumerate(["Animal", "Sheet", "Short run", "Long run", "Source and range"], 1): hdr(wa, 7, j, h)
    brs = [b for b in ALL if b.key not in ("dairy_2019", "eggs_2025")]
    sheetnames = {"dairy_2026": "Dairy", "beef": "Beef", "eggs_2019-21": "Eggs", "broiler": "Broiler", "pork": "Pork", "pollock": "Pollock", "salmon": "Salmon"}
    arow = {}
    for i, b in enumerate(brs):
        row = 8+i; arow[b.key] = row
        put(wa, row, 1, b.name.split(" (")[0], BLACK); put(wa, row, 2, sheetnames[b.key], BLACK)
        put(wa, row, 3, b.eps_s_sr, BLUE, DF3); put(wa, row, 4, b.eps_s_lr, BLUE, DF3); put(wa, row, 5, b.supply_src, BLACK, wrap=True)
    put(wa, 8+len(brs)+1, 1, "Short run = within a production cycle (months to ~1 year); long run = after herd/flock/capacity adjustment (3-5 years). Milk at a 10-year horizon: 2.5 (Chavas & Klemme). Wild capture under quota: ~0 at any horizon.", BLACK, wrap=True)
    # ---------------- branch sheets ----------------
    refs = {}
    d = dairy("2026")
    ws_d, refs["Dairy"] = write_branch(wb, d, "Dairy", arow["dairy_2026"], inputs_writer=lambda ws, r: dairy_inputs(ws, r)[:4], protein=PROTEIN,
                                       unit_factor_note="lb of raw milk displaced per lb of product replaced (long run).", chart_title="Where the dairy cow's revenue comes from (value share by stream)")
    # fill dairy helper cell: milk value = sum of first 10 sub rows
    s0 = refs["Dairy"]["sub0"]
    for row in range(1, 60):
        if ws_d.cell(row=row, column=1).value and str(ws_d.cell(row=row, column=1).value).startswith("Helper: milk value"):
            ws_d.cell(row=row, column=2, value=f"=SUM(H{s0}:H{s0+9})").font = BLACK; ws_d.cell(row=row, column=2).number_format = NUM3
    b = [x for x in ALL if x.key == "beef"][0]
    _, refs["Beef"] = write_branch(wb, b, "Beef", arow["beef"], inputs_writer=lambda ws, r: generic_inputs(BEEF_ROWS, BEEF_Q, BEEF_P, "Inputs: carcass yields, primal values, drop credit (blue = editable)")(ws, r)[:4],
                                   protein=PROTEIN, unit_factor_note="lb of live steer displaced per lb of product replaced (long run).", chart_title="Fed steer: value share by stream")
    e = eggs("2019-21")
    _, refs["Eggs"] = write_branch(wb, e, "Eggs", arow["eggs_2019-21"], inputs_writer=lambda ws, r: eggs_inputs(ws, r)[:4], protein=PROTEIN,
                                   unit_factor_note="lb of eggs (in shell, 1.5 lb per dozen) displaced per lb of product replaced (long run).", chart_title="Layer hen: value share by stream")
    br_ = [x for x in ALL if x.key == "broiler"][0]
    _, refs["Broiler"] = write_branch(wb, br_, "Broiler", arow["broiler"], inputs_writer=lambda ws, r: generic_inputs(BROILER_ROWS, BROILER_Q, BROILER_P, "Inputs: part yields (share of live weight) and prices (blue = editable)")(ws, r)[:4],
                                      protein=PROTEIN, unit_factor_note="lb of live bird displaced per lb of product replaced (long run).", chart_title="Broiler: value share by stream")
    p = [x for x in ALL if x.key == "pork"][0]
    _, refs["Pork"] = write_branch(wb, p, "Pork", arow["pork"], inputs_writer=lambda ws, r: generic_inputs(PORK_ROWS, PORK_Q, PORK_P, "Inputs: primal yields and values, drop credit (blue = editable)")(ws, r)[:4],
                                   protein=PROTEIN, unit_factor_note="lb of live hog displaced per lb of product replaced (long run).", chart_title="Hog: value share by stream")
    po = [x for x in ALL if x.key == "pollock"][0]
    _, refs["Pollock"] = write_branch(wb, po, "Pollock", arow["pollock"], inputs_writer=lambda ws, r: generic_inputs(POLLOCK_ROWS, POLLOCK_Q, POLLOCK_P, "Inputs: 2024 product volumes and prices (blue = editable)")(ws, r)[:4],
                                      protein=PROTEIN, unit_factor_note="tonnes of round-weight catch displaced per tonne of product replaced (long run; ~0 under a binding TAC).", chart_title="Alaska pollock: value share by stream")
    sa = [x for x in ALL if x.key == "salmon"][0]
    _, refs["Salmon"] = write_branch(wb, sa, "Salmon", arow["salmon"], inputs_writer=lambda ws, r: generic_inputs(SALMON_ROWS, SALMON_Q, SALMON_P, "Inputs (blue = editable)")(ws, r)[:4],
                                     protein=PROTEIN, unit_factor_note="kg HOG displaced per kg of product replaced (long run).", chart_title="Farmed salmon: value share by stream")
    # ---------------- Summary ----------------
    wsum = wb.create_sheet("Summary", 1); wsum.sheet_properties.tabColor = "00B050"
    for col, w in zip("ABCDEFGHIJKLMNO", [12, 56, 12, 10, 12, 12, 12, 12, 12, 14, 14, 30, 16, 12, 60]): wsum.column_dimensions[col].width = w
    put(wsum, 1, 1, "Summary: displacement factors and floors by product (linked to branch sheets)", H1)
    put(wsum, 2, 1, "DF = share of a demand reduction in the product that becomes a reduction in animals produced, at three horizons (within a year; 3-5 years; constant-cost limit, where supply is perfectly elastic). 1 - DF = the total discount, the elasticity discount 1/(1+eps_s*H) and the joint-production discount together; DF(3-5 years)/DF(limit) is the bundle factor, so 1 - that ratio is the elasticity discount alone. Floor = next-best use as a share of the current price.", BLACK)
    heads = ["Branch", "Product", "Share of animal value", "Demand elasticity (stream)", "DF short run (within a year)", "DF long run (3-5 years)", "DF constant-cost limit", "Total discount (1-DF, 3-5 years)", "Stream price change for a 10% replacement",
             "Animal change if fully replaced (LR, linear, floor-capped)", "Floor ratio (P_floor/P_now)", "Biotech route most likely to target it", "Technical reachability", "Animal mass per kg product (LR)", "Reading"]
    for j, h in enumerate(heads, 1): hdr(wsum, 4, j, h)
    wsum.row_dimensions[4].height = 60
    ROUTE = {"Fluid milk (Class I)":("Precision fermentation (whey+casein) / plant-based milks","Medium"),
             "Other dairy: yogurt, ice cream, etc. (Class II)":("Plant-based / PF casein and whey","Medium"),
             "Butter / cream (3.5 lb fat per cwt)":("Plant oils; fermentation-derived fats","High"),
             "Nonfat dry milk / SMP (also the casein route)":("PF casein + lactose blends","Medium"),
             "Cheese (cheddar-equivalent)":("PF casein (micelle-forming) + plant fats","Low-medium"),
             "WPC 80 (whey protein concentrate)":("PF beta-lactoglobulin","High"),
             "WPI (whey protein isolate)":("PF beta-lactoglobulin","High"),
             "Dry whey (sweet whey powder)":("none economic (floor-priced)","n/a"),
             "Lactose":("none (floor-priced)","n/a"),"Permeate / condensed whey / feed":("none","n/a"),
             "Cull cows (manufacturing beef)":("Plant-based / mycoprotein mince, blends","High"),
             "Calves (beef-on-dairy, bull calves)":("n/a","n/a"),
             "Middle meats: steaks and roasts from rib and loin":("Cultivated / mycoprotein whole-cut","Low"),
             "End-meat whole-muscle cuts (chuck/round roasts, steaks; 50% of chuck+round)":("Cultivated / plant-based whole-cut","Low"),
             "Thin-meat whole-muscle (brisket, flank, skirt; 40% of thin meats)":("Plant-based whole-cut","Low"),
             "Grinding material: trim and ground chuck/round (minced beef)":("Plant-based / mycoprotein mince, blends, cultivated fat","High"),
             "Hide":("Mycelium / bio-based leather","High"),"Tallow and technical fat":("Oleochemicals / fermentation fats","High"),
             "Edible offal (tongue, cheek, oxtail, liver, tripe, hearts, lips)":("n/a","Low"),"Meat & bone meal, blood meal":("SCP / insect meal","High"),
             "Shell eggs (table)":("Plant-based liquid egg; PF ovalbumin","Low-medium"),"Liquid/frozen whole egg":("Plant-based egg; PF ovalbumin","Medium"),
             "Liquid egg white (albumen): liquid, dried albumen, protein fractions":("PF ovalbumin / albumen proteins","High"),"Liquid egg yolk":("Plant lipids / PF","Low-medium"),
             "Spent hen (soup meat, rendering)":("n/a","n/a"),
             "Boneless skinless breast (fillets, whole-muscle nuggets)":("Plant-based / mycoprotein / cultivated","Medium"),"Tenders":("as breast","Medium"),"Wings":("n/a (bone-in)","Low"),
             "Leg quarters / dark meat":("Plant-based dark meat","Medium"),"Backs, necks, frames -> mechanically separated chicken (MSC nuggets, hot dogs)":("Plant-based / mycoprotein nuggets, hot dogs","High"),
             "Giblets":("n/a","n/a"),"Paws (export)":("n/a","n/a"),"Feathers, blood, viscera, heads -> rendering":("SCP / insect meal","High"),
             "Loin (chops, roasts)":("Cultivated / plant whole-cut","Low"),"Butt (shoulder)":("Plant-based pulled pork","Medium"),"Spareribs":("n/a (bone-in)","Low"),
             "Ham (mostly cured)":("Plant-based deli","Medium"),"Belly (bacon)":("Plant-based / mycelium bacon; cultivated fat","Medium"),
             "Picnic, jowl, neck bones, trim -> sausage, ground pork":("Plant-based sausage, blends","High"),"Feet, tails (export, variety meats)":("n/a","n/a"),
             "Drop credit (lard, offal, meals, plasma)":("Fermentation fats / SCP","High"),
             "Fillet blocks and fillets (fish fingers, portions)":("Plant-based / mycoprotein fish fingers","High"),"H&G (headed and gutted)":("n/a","Low"),
             "Surimi (crab sticks, kamaboko)":("Plant-based / mycoprotein surimi","High"),"Mince":("as surimi","High"),"Roe":("n/a","Low"),
             "Fishmeal":("SCP, insect, algal meal","High"),"Fish oil":("Algal omega-3","High"),
             "Salmon HOG, fillets and portions":("Cultivated / plant-based salmon","Low-medium"),
             "By-products (heads, frames, viscera, trimmings) -> oil, meal, pet food":("Algal omega-3 / SCP","High")}
    row = 5
    for sheet, key in [("Dairy","dairy_2026"),("Beef","beef"),("Eggs","eggs_2019-21"),("Broiler","broiler"),("Pork","pork"),("Pollock","pollock"),("Salmon","salmon")]:
        brx = [x for x in ALL if x.key == key][0]; rf = refs[sheet]
        for i, s in enumerate(brx.subs):
            sr = rf["sub0"]+i
            put(wsum, row, 1, sheet, BLACK)
            put(wsum, row, 2, f"='{sheet}'!A{sr}", GREEN, wrap=True)
            put(wsum, row, 3, f"='{sheet}'!I{sr}", GREEN, PCT)
            put(wsum, row, 4, f"=INDEX('{sheet}'!$F${rf['st0']}:$F${rf['st1']},MATCH('{sheet}'!B{sr},'{sheet}'!$A${rf['st0']}:$A${rf['st1']},0))", GREEN, NUM2)
            put(wsum, row, 5, f"='{sheet}'!L{sr}", GREEN, DF3)
            put(wsum, row, 6, f"='{sheet}'!M{sr}", GREEN, DF3)
            put(wsum, row, 7, f"='{sheet}'!N{sr}", GREEN, DF3)
            put(wsum, row, 8, f"=1-F{row}", BLACK, PCT)
            put(wsum, row, 9, f"='{sheet}'!Q{sr}", GREEN, PCT)
            put(wsum, row, 10, f"='{sheet}'!T{sr}", GREEN, PCT)
            put(wsum, row, 11, f"=INDEX('{sheet}'!$G${rf['st0']}:$G${rf['st1']},MATCH('{sheet}'!B{sr},'{sheet}'!$A${rf['st0']}:$A${rf['st1']},0))", GREEN, PCT)
            rt = ROUTE.get(s.name, ("", ""))
            put(wsum, row, 12, rt[0], BLUE, wrap=True); put(wsum, row, 13, rt[1], BLUE)
            put(wsum, row, 14, f"='{sheet}'!U{sr}", GREEN, NUM2)
            put(wsum, row, 15, f"=IF(F{row}>=0.2,\"primary product: displacement is a fifth or more of the replaced volume\",IF(F{row}>=0.05,\"co-product: a twentieth to a fifth\",\"by-product or quota-limited: under a twentieth; price falls toward the floor instead\"))", BLACK, wrap=True)
            row += 1
        row += 1
    put(wsum, row+1, 1, "Bundle displacement (giving up every product of the animal), for comparison with 'cumulative elasticity' figures in the literature:", BOLD)
    row += 2
    for j, h in enumerate(["Animal", "", "", "", "DF bundle SR", "DF bundle LR", "DF bundle, constant-cost limit", "", "Norwood & Lusk (2011) figure"], 1):
        if h: hdr(wsum, row, j, h)
    nl = {"Dairy":0.56,"Beef":0.68,"Eggs":0.91,"Broiler":0.76,"Pork":0.74,"Pollock":None,"Salmon":None}
    row += 1
    for sheet in ["Dairy","Beef","Eggs","Broiler","Pork","Pollock","Salmon"]:
        rf = refs[sheet]; put(wsum, row, 1, sheet, BLACK)
        put(wsum, row, 5, f"='{sheet}'!B{rf['agg0']+5}", GREEN, DF3); put(wsum, row, 6, f"='{sheet}'!B{rf['agg0']+6}", GREEN, DF3); put(wsum, row, 7, 1.0, BLACK, DF3)
        if nl[sheet]: put(wsum, row, 9, nl[sheet], BLUE, DF3)
        row += 1
    wsum.freeze_panes = "C5"
    # ---------------- Sensitivity ----------------
    wsn = wb.create_sheet("Sensitivity"); wsn.sheet_properties.tabColor = "7030A0"
    wsn.column_dimensions["A"].width = 40
    put(wsn, 1, 1, "Sensitivity: single-product displacement factor DF = eps_s / (eps_s + |eps_d|)", H1)
    put(wsn, 2, 1, "Rows: supply elasticity eps_s. Columns: demand elasticity eps_d. Blue axis values are editable.", BLACK)
    es = [0.02,0.05,0.1,0.15,0.2,0.3,0.4,0.5,0.7,0.9,1.0,1.5,2.0,2.5]; ed = [-0.1,-0.2,-0.3,-0.4,-0.5,-0.6,-0.75,-0.9,-1.0,-1.5,-2.0,-3.0]
    put(wsn, 4, 1, "eps_s \\ eps_d", BOLD)
    for j, e in enumerate(ed): put(wsn, 4, 2+j, e, BLUE, NUM2); wsn.column_dimensions[L(2+j)].width = 9
    for i, s in enumerate(es):
        put(wsn, 5+i, 1, s, BLUE, NUM2)
        for j in range(len(ed)):
            put(wsn, 5+i, 2+j, f"=$A{5+i}/($A{5+i}+ABS({L(2+j)}$4))", BLACK, DF3)
    r0 = 5+len(es)+2
    put(wsn, r0, 1, "Joint-product version: DF for a product with value share s and elasticity eps_k inside a fixed-proportion bundle with aggregate elasticity eps_bar", BOLD)
    put(wsn, r0+1, 1, "Value share of the product (s)"); put(wsn, r0+1, 2, 0.05, BLUE, PCT)
    put(wsn, r0+2, 1, "Own-price elasticity of the product (eps_k)"); put(wsn, r0+2, 2, -1.5, BLUE, NUM2)
    put(wsn, r0+3, 1, "Aggregate derived-demand elasticity of the animal (eps_bar)"); put(wsn, r0+3, 2, -0.65, BLUE, NUM2)
    put(wsn, r0+4, 1, "Supply elasticity (eps_s)"); put(wsn, r0+4, 2, 0.9, BLUE, NUM2)
    put(wsn, r0+5, 1, "DF of the product = eps_s * |eps_bar| * (s/|eps_k|) / (eps_s + |eps_bar|)", BOLD); put(wsn, r0+5, 2, f"=B{r0+4}*ABS(B{r0+3})*(B{r0+1}/ABS(B{r0+2}))/(B{r0+4}+ABS(B{r0+3}))", BLACK, DF4)
    put(wsn, r0+6, 1, "Decomposition: DF = DF_bundle x omega, with DF_bundle = eps_s/(eps_s+|eps_bar|) and omega = (s/|eps_k|) x |eps_bar| (inelasticity-weighted value share)", BLACK)
    put(wsn, r0+7, 1, "DF_bundle"); put(wsn, r0+7, 2, f"=B{r0+4}/(B{r0+4}+ABS(B{r0+3}))", BLACK, DF3)
    put(wsn, r0+8, 1, "omega"); put(wsn, r0+8, 2, f"=(B{r0+1}/ABS(B{r0+2}))*ABS(B{r0+3})", BLACK, DF3)
    r1 = r0+11
    put(wsn, r1, 1, "Target calculator: how much of product i must be replaced to cut the animal population by a target share?", BOLD)
    put(wsn, r1+1, 1, "Target animal reduction (share)"); put(wsn, r1+1, 2, 0.05, BLUE, PCT, fill=YELLOW)
    put(wsn, r1+2, 1, "DF of the product (long run; copy from Summary col F)"); put(wsn, r1+2, 2, 0.0135, BLUE, DF4, fill=YELLOW)
    put(wsn, r1+3, 1, "g: stream price change per unit shift (copy from branch sheet table B col Q)"); put(wsn, r1+3, 2, 0.62, BLUE, DF3, fill=YELLOW)
    put(wsn, r1+4, 1, "w: product share within its stream (branch sheet col K)"); put(wsn, r1+4, 2, 0.42, BLUE, DF3, fill=YELLOW)
    put(wsn, r1+5, 1, "Floor ratio of the stream (blank or 0 if none)"); put(wsn, r1+5, 2, 0.06, BLUE, PCT, fill=YELLOW)
    put(wsn, r1+6, 1, "Required demand shift in the product (share of its market)", BOLD); put(wsn, r1+6, 2, f"=-B{r1+1}/B{r1+2}", BLACK, PCT)
    put(wsn, r1+7, 1, "Feasible within the product's market? (|shift| <= 100%)", BOLD); put(wsn, r1+7, 2, f"=IF(ABS(B{r1+6})<=1,\"yes\",\"no: the whole product market is too small\")", BLACK)
    put(wsn, r1+8, 1, "Implied stream price after the shift (share of today's price, log form)", BOLD); put(wsn, r1+8, 2, f"=EXP(B{r1+3}*LN(MAX(0.0001,1+B{r1+6}*B{r1+4})))", BLACK, PCT)
    put(wsn, r1+9, 1, "Below the floor? (then the floor binds and the target is not reachable through this product)", BOLD); put(wsn, r1+9, 2, f"=IF(AND(B{r1+5}>0,B{r1+8}<B{r1+5}),\"floor binds\",\"ok\")", BLACK)
    # ---------------- Ranges (Monte Carlo, pasted values from monte_carlo.py) ----------------
    import json as _json
    MCR = _json.load(open(results / "mc_results.json"))
    wsr = wb.create_sheet("Ranges"); wsr.sheet_properties.tabColor = "C00000"
    for col, w in zip("ABCDEFGHIJKLM", [14, 56, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12]): wsr.column_dimensions[col].width = w
    put(wsr, 1, 1, "Ranges: 10th, 50th and 90th percentiles of each displacement factor over 2,000 draws of the elasticities (values pasted from the Python model, monte_carlo.py; they do not recalculate)", H1)
    put(wsr, 2, 1, "Sampling: stream demand elasticities lognormal around the point value, sigma 0.25 for sourced [S] streams and 0.45 for assumed [A] streams; long-run supply elasticities lognormal with sigma 0.6 (dairy), 0.35 (beef), 0.4 (eggs), 0.7 (broiler), 0.3 (hog), 0.8 (salmon), uniform 0 to 0.17 (pollock); short-run supply sigma 0.5. Prices and value shares held at the scenario snapshot.", BLACK)
    heads = ["Branch", "Product", "DF within a year p10", "p50", "p90", "DF 3-5 years p10", "p50", "p90", "DF constant-cost limit p10", "p50", "p90"]
    for j, h in enumerate(heads, 1): hdr(wsr, 4, j, h)
    wsr.row_dimensions[4].height = 45
    row = 5
    for key, label in [("dairy_2026", "Dairy (2026)"), ("dairy_2019", "Dairy (2019-21)"), ("beef", "Beef"), ("eggs_2019-21", "Eggs (2019-21)"), ("eggs_2025", "Eggs (2025)"), ("broiler", "Broiler"), ("pork", "Pork"), ("pollock", "Pollock"), ("salmon", "Salmon")]:
        for sub, d in MCR[key].items():
            name = "All products together (bundle)" if sub == "__bundle__" else sub
            put(wsr, row, 1, label, BLACK); put(wsr, row, 2, name, BLACK, wrap=True)
            put(wsr, row, 3, d["sr"]["p10"], BLACK, DF4); put(wsr, row, 4, d["sr"]["p50"], BLACK, DF4); put(wsr, row, 5, d["sr"]["p90"], BLACK, DF4)
            put(wsr, row, 6, d["lr"]["p10"], BLACK, DF4); put(wsr, row, 7, d["lr"]["p50"], BLACK, DF4); put(wsr, row, 8, d["lr"]["p90"], BLACK, DF4)
            if "lim" in d:
                put(wsr, row, 9, d["lim"]["p10"], BLACK, DF4); put(wsr, row, 10, d["lim"]["p50"], BLACK, DF4); put(wsr, row, 11, d["lim"]["p90"], BLACK, DF4)
            row += 1
        row += 1
    wsr.freeze_panes = "C5"
    # ---------------- Exit (price-cap scenarios, pasted values from exit_runs.py on the exact model) ----------------
    EXR = _json.load(open(results / "exit_results.json")); FLR = _json.load(open(results / "full_loss.json")); CVR = _json.load(open(results / "exit_curves.json"))
    wse = wb.create_sheet("Exit"); wse.sheet_properties.tabColor = "C00000"
    for col, w in zip("ABCDEFGHIJKL", [14, 40, 10, 10, 12, 14, 14, 14, 16, 16, 16, 40]): wse.column_dimensions[col].width = w
    put(wse, 1, 1, "Exit: a perfect substitute offered at a fixed share of today's price (price cap), solved on the exact non-linear model (exact_model.py / exit_runs.py); values pasted, they do not recalculate", H1)
    put(wse, 2, 1, "Regime 2: one product capped. The animal keeps selling its joint output at the cap; the substitute supplies the extra demand at the lower price. A product that is the only output of a fungible route (fluid milk, shell eggs) loses the raw commodity entirely once the cap falls below the commodity's value in other routes ('route exit price'). 'Limit' = constant-cost supply (the farm price returns to today's level after the herd adjusts).", BLACK)
    heads = ["Branch", "Product (stream)", "Horizon", "Cap (share of today's price)", "Animal change", "Product output change (animal side)", "Substitute's share of the product market", "Quantity to the outlet (share of baseline)", "Farm price change", "Highest co-product price (index)", "Raw commodity to each route (index)", "Note"]
    for j, h in enumerate(heads, 1): hdr(wse, 4, j, h)
    wse.row_dimensions[4].height = 60
    row = 5
    for r in EXR:
        put(wse, row, 1, r["branch"], BLACK); put(wse, row, 2, r["stream"], BLACK, wrap=True); put(wse, row, 3, "3-5 years" if r["horizon"] == "LR" else "constant-cost limit", BLACK)
        put(wse, row, 4, r["cap"], BLACK, PCT); put(wse, row, 5, r["A"], BLACK, PCT); put(wse, row, 6, r["Q_k"], BLACK, PCT)
        if r["sub_share"] is not None: put(wse, row, 7, r["sub_share"], BLACK, PCT)
        if r["outlet"] is not None: put(wse, row, 8, r["outlet"], BLACK, PCT)
        put(wse, row, 9, r["PA"], BLACK, PCT)
        if r["max_other_price"] is not None: put(wse, row, 10, r["max_other_price"], BLACK, DF3)
        if r["route_q"]: put(wse, row, 11, "; ".join(f"{k}: {v:.3f}" for k, v in r["route_q"].items()), BLACK, wrap=True)
        if r["stream"] == "ALL PRODUCTS": put(wse, row, 12, "Regime 3: every product capped; animal change = cap^eps_s (3-5 years) or -100% (constant cost)", BLACK, wrap=True)
        row += 1
    row += 2
    put(wse, row, 1, "Full loss of a product's market: cap at the floor price where one exists, otherwise at zero", BOLD); row += 1
    for j, h in enumerate(["Branch", "Product (stream)", "Cap used", "Animal change within a year", "Animal change 3-5 years", "Animal change, constant-cost limit", "Product output change (3-5 years)", "Highest co-product price (3-5 years, index)", "Which co-product"], 1): hdr(wse, row, j, h)
    row += 1
    for key, d in FLR.items():
        for k, v in d.items():
            put(wse, row, 1, key, BLACK); put(wse, row, 2, k, BLACK, wrap=True); put(wse, row, 3, v["cap"], BLACK, PCT)
            put(wse, row, 4, v["SR"]["A"], BLACK, PCT); put(wse, row, 5, v["LR"]["A"], BLACK, PCT); put(wse, row, 6, v["limit"]["A"], BLACK, PCT)
            put(wse, row, 7, v["LR"]["Q_k"], BLACK, PCT)
            if v["LR"]["max_other"] is not None: put(wse, row, 8, v["LR"]["max_other"], BLACK, DF3); put(wse, row, 9, v["LR"]["argmax_other"], BLACK)
            row += 1
    row += 2
    put(wse, row, 1, "Route exit prices: the cap below which a single-product route receives no raw commodity", BOLD); row += 1
    for j, h in enumerate(["Branch", "Product (route)", "Horizon", "Exit cap (share of today's price)"], 1): hdr(wse, row, j, h)
    row += 1
    for r in CVR["route_exit"]:
        put(wse, row, 1, r["branch"], BLACK); put(wse, row, 2, r["stream"], BLACK); put(wse, row, 3, "3-5 years" if r["horizon"] == "LR" else "constant-cost limit", BLACK); put(wse, row, 4, r["exit_cap"], BLACK, PCT)
        row += 1
    wse.freeze_panes = "C5"
    # ---------------- Sources ----------------
    wso = wb.create_sheet("Sources"); wso.sheet_properties.tabColor = "808080"
    for col, w in zip("ABCD", [8, 70, 60, 90]): wso.column_dimensions[col].width = w
    put(wso, 1, 1, "Sources (pages opened; as-of October 2026)", H1)
    for j, h in enumerate(["#", "Source", "Used for", "URL"], 1): hdr(wso, 3, j, h)
    for i, (name, used, url) in enumerate(SOURCES):
        put(wso, 4+i, 1, i+1, BLACK); put(wso, 4+i, 2, name, BLACK, wrap=True); put(wso, 4+i, 3, used, BLACK, wrap=True); put(wso, 4+i, 4, url, BLACK)
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return refs

if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else WORKBOOK)
    print("built")
