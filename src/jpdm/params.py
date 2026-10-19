"""
Parameter sets for the nested joint-product EDM. Tags: [S] sourced (URL in sources.py), [E] estimate derived from sourced
inputs, [A] assumption (judgement). Prices wholesale/first-handler, US$ unless stated.
"""
from .edm_model import Sub, Stream, Branch

# ============================================================================================
# DAIRY COW  (unit: 100 lb raw milk + the pro-rata cattle sales of the cow that produced it)
# Routes (fungible): fluid, other manufactured, butter/powder, cheese route, cattle.
# Within cheese route (fixed): cheese, whey protein, whey carbohydrate. Within butter/powder (fixed): fat, nonfat solids.
# Farm-equivalent values = product price minus make allowance, times yield (the FMMO convention).
# ============================================================================================
def dairy(scenario="2026"):
    u_fluid, u_cheese, u_bp, u_other = 0.19, 0.60, 0.13, 0.08   # [E] utilisation shares from NASS volumes and standard yields
    cheese_yield = 10.6         # lb/cwt [S] CoBank/Hoard's (2020 composition)
    whey_solids = 6.0 if scenario == "2026" else 5.9   # lb/cwt [S] FMMO other-solids factor (6.0 from Dec 2025; 5.9 before)
    protein_frac = 0.13         # [S] 0.8% protein in 6.5%-solids whey
    rec_protein = 0.50          # [E] share of whey protein recovered into WPC/WPI (NASS 2025: ~0.55 bn lb protein in WPC+WPI vs ~1.1 bn lb in liquid whey)
    split_wpc80 = 0.61          # [S] NASS 2025: WPC50-90 381 m lb (x0.8 protein) vs WPI 214 m lb (x0.9): protein basis 305/(305+193)
    dry_whey_share, lactose_share, feed_share = 0.10, 0.15, 0.25   # [E] shares of whey solids by outlet
    if scenario == "2026":
        p = dict(classI=18.88, classII=17.60, cheese=1.5577, bfat=1.4762, nfs=1.5343, wpc80=9.50, wpi=14.0, drywhey=0.6694, lactose=0.70, feedwhey=0.36)
        mk = dict(cheese=0.2519, drywhey=0.2668, lactose=0.27, wpc80=1.50, wpi=2.50, feed=0.10)
        cattle_share = 0.078
        tag = "USDA AMS announced class prices Sep 2026 (Class I Oct 2026 advance); Dairy Market News Oct 2026 for whey products"
    else:
        p = dict(classI=17.60, classII=16.90, cheese=1.75, bfat=2.30, nfs=1.00, wpc80=3.00, wpi=5.00, drywhey=0.35, lactose=0.35, feedwhey=0.20)
        mk = dict(cheese=0.2003, drywhey=0.1991, lactose=0.20, wpc80=1.20, wpi=2.00, feed=0.10)
        cattle_share = 0.07
        tag = "2019-2021 reference levels: USDA AMS class prices and dry whey (2019-21 averages); WPC80 and WPI approximate trade levels"
    subs = [
        Sub("Fluid milk (Class I)", u_fluid, p["classI"], "Fluid milk", src="[S] Class I price"),
        Sub("Other dairy: yogurt, ice cream, etc. (Class II)", u_other, p["classII"], "Other dairy", src="[S] Class II price"),
        Sub("Butter / cream (3.5 lb fat per cwt)", u_bp, 3.5*p["bfat"], "Butter (fat)", src="[S] FMMO butterfat price x 3.5"),
        Sub("Nonfat dry milk / SMP (also the casein route)", u_bp, 9.3*0.965*p["nfs"], "Milk powder (nonfat solids)", src="[S] FMMO nonfat solids price x 9.3 x 0.965"),
        Sub("Cheese (cheddar-equivalent)", u_cheese*cheese_yield, p["cheese"]-mk["cheese"], "Cheese", src="[S] cheese price less make allowance"),
    ]
    prot = whey_solids*protein_frac*rec_protein
    subs += [
        Sub("WPC 80 (whey protein concentrate)", u_cheese*prot*split_wpc80/0.80, p["wpc80"]-mk["wpc80"], "Whey protein", src="[S] price; [A] processing allowance"),
        Sub("WPI (whey protein isolate)", u_cheese*prot*(1-split_wpc80)/0.90, p["wpi"]-mk["wpi"], "Whey protein", src="[S] price; [A] processing allowance"),
        Sub("Dry whey (sweet whey powder)", u_cheese*whey_solids*dry_whey_share, p["drywhey"]-mk["drywhey"], "Whey carbohydrate", src="[S] price and make allowance"),
        Sub("Lactose", u_cheese*whey_solids*lactose_share, p["lactose"]-mk["lactose"], "Whey carbohydrate", src="[S] price; [A] allowance"),
        Sub("Permeate / condensed whey / feed", u_cheese*whey_solids*feed_share, p["feedwhey"]-mk["feed"], "Whey carbohydrate", src="[S] feed-grade whey price"),
    ]
    milk_total = sum(s.value for s in subs)
    cattle_val = milk_total*cattle_share/(1-cattle_share)
    subs += [Sub("Cull cows (manufacturing beef)", 1.0, cattle_val*0.60, "Cull cows", src="[S] ERS cattle sales share; [E] 60/40 split"),
             Sub("Calves (beef-on-dairy, bull calves)", 1.0, cattle_val*0.40, "Calves", src="[E]")]
    streams = [
        Stream("Fluid milk", "Fluid", -0.40, None, "", "[S] Andreyeva 2010 milk 0.59; Okrent & Alston 2012 milk 0.10; EU 0.53"),
        Stream("Other dairy", "Other manufactured", -0.90, None, "", "[S] Okrent & Alston other dairy 1.04; yogurt 1.19"),
        Stream("Butter (fat)", "Butter & powder", -0.60, None, "", "[S] EU butter 0.47; fats & oils 0.48"),
        Stream("Milk powder (nonfat solids)", "Butter & powder", -1.00, 0.60, "feed-grade SMP / export at world price", "[A] traded commodity, elastic for one supplier"),
        Stream("Cheese", "Cheese route", -0.55, None, "", "[S] Andreyeva cheese 0.44; Okrent & Alston 0.70; EU 0.60"),
        Stream("Whey protein", "Cheese route", -1.50, 0.06, "protein valued as dry/feed whey (~$0.35-0.70 per lb solids)", "[A] ingredient with substitutes (SPI, MPC, pea); Houck soybean meal flexibility 1.12"),
        Stream("Whey carbohydrate", "Cheese route", -2.00, 0.50, "feed-grade whey / permeate", "[A] feed outlet, near-perfect substitutes"),
        Stream("Cull cows", "Cattle sales", -0.80, 0.15, "rendering / pet food", "[S] beef demand 0.75 (Andreyeva)"),
        Stream("Calves", "Cattle sales", -0.60, 0.05, "bob veal / euthanasia", "[A] derived from fed-beef demand"),
    ]
    return Branch(f"dairy_{scenario}", f"Dairy cow ({scenario} prices)", "per 100 lb milk + pro-rata cattle sales", 0.12, 0.90, subs, streams,
                  notes="Milk is fungible across routes; cheese and whey are joint in fixed proportions; whey outlets are fungible.",
                  supply_src="[S] Chavas & Klemme 1986: 0.115 (current year), 0.89 (5-year), 2.46 (10-year); EU medium-run 0.18-0.65 (Bouamra-Mechemache et al. 2005)",
                  price_tag=tag, raw_shares={"Fluid": u_fluid, "Other manufactured": u_other, "Butter & powder": u_bp, "Cheese route": u_cheese})

# ============================================================================================
# FED STEER (one 1,400 lb Choice steer; 882 lb carcass at 63%)
# ============================================================================================
def beef():
    live, dress = 1400.0, 0.63
    carc = live*dress
    prim = {"Rib":(0.1140,6.7612),"Chuck":(0.2962,3.3740),"Round":(0.2232,2.9522),"Loin":(0.2126,4.5003),
            "Brisket":(0.0495,2.8783),"Short plate":(0.0710,2.2219),"Flank":(0.0335,1.6028)}   # [S] AMS yield factors; Choice primal values 15 Oct 2026
    mid_y = prim["Rib"][0]+prim["Loin"][0]; mid_v = sum(prim[k][0]*prim[k][1] for k in ["Rib","Loin"])
    end_y = prim["Chuck"][0]+prim["Round"][0]; end_v = sum(prim[k][0]*prim[k][1] for k in ["Chuck","Round"])
    thin_y = sum(prim[k][0] for k in ["Brisket","Short plate","Flank"]); thin_v = sum(prim[k][0]*prim[k][1] for k in ["Brisket","Short plate","Flank"])
    grind_y = end_y*0.5+thin_y*0.6; grind_v = end_v*0.5*0.95+thin_v*0.6*0.90
    subs = [
        Sub("Middle meats: steaks and roasts from rib and loin", carc*mid_y, mid_v/mid_y, "Middle meats (whole cut)", src="[S] AMS primals"),
        Sub("End-meat whole-muscle cuts (chuck/round roasts, steaks; 50% of chuck+round)", carc*end_y*0.5, end_v/end_y*1.05, "End meats (whole cut)", src="[E] split of chuck/round"),
        Sub("Thin-meat whole-muscle (brisket, flank, skirt; 40% of thin meats)", carc*thin_y*0.4, thin_v/thin_y*1.15, "End meats (whole cut)", src="[E]"),
        Sub("Grinding material: trim and ground chuck/round (minced beef)", carc*grind_y, grind_v/grind_y, "Minced beef (grinding material)", src="[E] 50% of chuck/round + 60% of thin meats"),
        Sub("Hide", 1.0, 1.75*live/100, "Drop credit", src="[S] AMS drop value 15 Oct 2026"),
        Sub("Tallow and technical fat", 1.0, (3.03+0.83)*live/100, "Drop credit", src="[S]"),
        Sub("Edible offal (tongue, cheek, oxtail, liver, tripe, hearts, lips)", 1.0, (1.77+1.14+0.15+1.56+0.37+0.47+0.83+1.16+0.64+0.03+0.01)*live/100, "Drop credit", src="[S]"),
        Sub("Meat & bone meal, blood meal", 1.0, (0.90+0.48)*live/100, "Drop credit", src="[S]"),
    ]
    streams = [
        Stream("Middle meats (whole cut)", "Carcass", -1.00, None, "", "[S] beef 0.75 (Andreyeva); steaks more elastic in scanner data (Tonsor & Lusk 2024)"),
        Stream("End meats (whole cut)", "Carcass", -0.90, None, "", "[A] as beef"),
        Stream("Minced beef (grinding material)", "Carcass", -0.85, 0.30, "pet food / rendering", "[S] beef 0.75; ground beef 1.25 (farmdoc 2021)"),
        Stream("Drop credit", "Carcass", -2.50, 0.40, "rendering / disposal; hides already near disposal value", "[A] traded by-products: hides, tallow, offal exports"),
    ]
    return Branch("beef", "Fed steer (Oct 2026 prices)", "per 1,400 lb Choice steer", 0.15, 0.80, subs, streams,
                  notes="Carcass cuts in fixed proportions (one route); grinding is a one-way re-route handled as a floor on whole-cut streams in the text.",
                  supply_src="[S] Wohlgenant 1993 beef supply 0.15 (SR); Lusk & Norwood 2009 LR 0.82; Harrington & Dubman 2008: 1.07",
                  price_tag="USDA AMS boxed beef cutout 15 Oct 2026; by-product drop value 15 Oct 2026")

# ============================================================================================
# LAYER HEN (one dozen eggs + pro-rata spent hen; ~25 dozen per hen-year)
# Routes (fungible): shell eggs | egg products whole | separated (white+yolk fixed) | spent hen
# ============================================================================================
def eggs(scenario="2019-21"):
    shell_share, breaking_share = 0.68, 0.32    # [S] 32% broken (NASS/AMS)
    sep_share = 0.36                             # [E] NASS white/yolk volumes imply ~36% of broken eggs separated
    liquid_per_doz = 1.29                        # [S] NASS 2025
    wf, yf = 0.58/0.89, 0.31/0.89                # [S] USDA egg grading manual composition
    if scenario == "2019-21":
        p = dict(shell=0.95, whole=0.33, white=0.23, yolk=0.46); tag = "USDA AMS Oct 2019 egg-products prices; shell eggs ~2019 annual average (approx.)"
    else:
        p = dict(shell=2.08, whole=1.155, white=0.914, yolk=3.57); tag = "USDA AMS Sep 2025 (HPAI-tight market)"
    subs = [
        Sub("Shell eggs (table)", shell_share, p["shell"], "Shell eggs", src="[S]"),
        Sub("Liquid/frozen whole egg", breaking_share*(1-sep_share)*liquid_per_doz, p["whole"], "Whole egg products", src="[S]"),
        Sub("Liquid egg white (albumen): liquid, dried albumen, protein fractions", breaking_share*sep_share*liquid_per_doz*wf, p["white"], "Egg white", src="[S]"),
        Sub("Liquid egg yolk", breaking_share*sep_share*liquid_per_doz*yf, p["yolk"], "Egg yolk", src="[S]"),
        Sub("Spent hen (soup meat, rendering)", 1/25.0, 0.02, "Spent hen", src="[S] removal cost 0-5 c/head: nominal $0.02"),
    ]
    streams = [
        Stream("Shell eggs", "Shell", -0.27, None, "", "[S] Andreyeva 2010 eggs 0.27; Okrent & Alston 0.24; Bakhtavoryan 2021 conventional 0.235"),
        Stream("Whole egg products", "Products: whole", -0.80, 0.50, "dried whole-egg inventory / export / feed", "[A] breaker demand more elastic than table demand (Blakely 1984)"),
        Stream("Egg white", "Products: separated", -1.50, 0.35, "dried albumen at surplus prices / feed", "[A] ingredient with substitutes"),
        Stream("Egg yolk", "Products: separated", -1.00, 0.50, "industrial yolk (pet food, feed)", "[A]"),
        Stream("Spent hen", "Spent hen", -5.00, 0.00, "rendering / composting", "[A] effectively perfectly elastic at ~0"),
    ]
    return Branch(f"eggs_{scenario}", f"Layer hen ({scenario} prices)", "per dozen eggs + pro-rata spent hen", 0.03, 1.00, subs, streams,
                  notes="Eggs flow between shell and breaking (fungible routes); white and yolk are joint in fixed proportions.",
                  supply_src="[S] Chavas 1980 SR 0.03; Chavas & Johnson 1981 LR ~1; Harrington & Dubman 2008: 1.04",
                  price_tag=tag, raw_shares={"Shell": shell_share, "Products: whole": breaking_share*(1-sep_share), "Products: separated": breaking_share*sep_share})

# ============================================================================================
# BROILER (one 6.0 lb live bird; yields Cobb 500; prices AMS 24 Jan 2025)
# ============================================================================================
def broiler():
    live = 6.0
    subs = [
        Sub("Boneless skinless breast (fillets, whole-muscle nuggets)", live*0.2205, 1.486, "Breast meat", src="[S] Cobb yield; AMS price"),
        Sub("Tenders", live*0.040, 1.734, "Breast meat", src="[S]"),
        Sub("Wings", live*0.0758, 1.906, "Wings", src="[S]"),
        Sub("Leg quarters / dark meat (whole legs)", live*0.2301, 0.514, "Dark meat", src="[S] Cobb whole legs 23.01% (leg quarters 31.62% include the back)"),
        Sub("Backs, necks, frames -> mechanically separated chicken (MSC nuggets, hot dogs)", live*0.121, 0.125, "Backs & necks (MSC)", src="[S] backs/necks price"),
        Sub("Giblets", live*0.030, 0.40, "Giblets & paws", src="[A]"),
        Sub("Paws (export)", live*0.045, 0.60, "Giblets & paws", src="[E] from FAS export unit values"),
        Sub("Feathers, blood, viscera, heads -> rendering", live*0.135, 0.08, "Rendering", src="[E] rendered meal values"),
    ]
    streams = [
        Stream("Breast meat", "Carcass", -0.80, None, "", "[S] poultry 0.68 (Andreyeva); 0.81 (Okrent & Alston)"),
        Stream("Wings", "Carcass", -1.00, None, "", "[A]"),
        Stream("Dark meat", "Carcass", -1.50, 0.25, "pet food / rendering; exported at world price", "[A] export-exposed, elastic"),
        Stream("Backs & necks (MSC)", "Carcass", -3.00, 0.50, "rendering", "[A] residual raw material"),
        Stream("Giblets & paws", "Carcass", -2.00, 0.15, "rendering", "[A]"),
        Stream("Rendering", "Carcass", -5.00, None, "already the floor", "[A]"),
    ]
    return Branch("broiler", "Broiler (Jan 2025 prices)", "per 6.0 lb live bird", 0.10, 0.70, subs, streams,
                  notes="Carcass parts in fixed proportions.",
                  supply_src="[S] Kapombe & Colyer 1998 SR 0.07 / LR 0.13; Chavas & Johnson 1982 0.02; Lusk & Norwood 2009 LR 0.70; Harrington & Dubman 1.15",
                  price_tag="USDA AMS weekly national composite 24 Jan 2025; Cobb 500 yield poster")

# ============================================================================================
# HOG (one 280 lb live hog; 215 lb carcass; AMS primal yields; values week ending 25 Sep 2026)
# ============================================================================================
def pork():
    carc, live = 215.0, 280.0
    subs = [
        Sub("Loin (chops, roasts)", carc*0.2517, 0.879, "Fresh pork cuts", src="[S]"),
        Sub("Butt (shoulder)", carc*0.1016, 1.115, "Fresh pork cuts", src="[S]"),
        Sub("Spareribs", carc*0.0481, 1.592, "Fresh pork cuts", src="[S]"),
        Sub("Ham (mostly cured)", carc*0.2459, 0.869, "Ham", src="[S]"),
        Sub("Belly (bacon)", carc*0.1628, 0.968, "Belly", src="[S]"),
        Sub("Picnic, jowl, neck bones, trim -> sausage, ground pork", carc*(0.1137+0.0145+0.0169), 0.66, "Sausage & trim", src="[S] picnic; [E] jowl/neck"),
        Sub("Feet, tails (export, variety meats)", carc*(0.0092+0.0123+0.0015), 0.50, "Variety meats & drop", src="[A]"),
        Sub("Drop credit (lard, offal, meals, plasma)", 1.0, 5.12*live/100, "Variety meats & drop", src="[S] AMS hog by-product value 9 Oct 2026"),
    ]
    streams = [
        Stream("Fresh pork cuts", "Carcass", -0.90, None, "", "[S] pork 0.72 (Andreyeva); loin 1.45 scanner (Tonsor & Lusk 2024)"),
        Stream("Ham", "Carcass", -0.75, None, "", "[A] processed, inelastic"),
        Stream("Belly", "Carcass", -0.80, None, "", "[S] bacon 0.83 scanner"),
        Stream("Sausage & trim", "Carcass", -1.20, 0.30, "pet food / rendering", "[A] trim competes with beef and poultry trim"),
        Stream("Variety meats & drop", "Carcass", -2.50, 0.40, "rendering", "[A]"),
    ]
    return Branch("pork", "Hog (Sep 2026 prices)", "per 280 lb live hog", 0.40, 1.50, subs, streams,
                  notes="Carcass primals in fixed proportions.",
                  supply_src="[S] Wohlgenant 1993 hog supply 0.40 (SR); Lusk & Norwood 2009 LR 1.56; Harrington & Dubman 0.79",
                  price_tag="USDA AMS pork cutout week ending 25 Sep 2026; hog by-product value 9 Oct 2026")

# ============================================================================================
# ALASKA POLLOCK (wild, TAC; one tonne round weight; 2024 product mix, NOAA)
# ============================================================================================
def pollock():
    catch = 1430.0
    subs = [
        Sub("Fillet blocks and fillets (fish fingers, portions)", 168.0/catch, 4500, "Flesh (fillets, surimi, mince)", src="[S] volumes; [E] prices"),
        Sub("H&G (headed and gutted)", 40.0/catch, 2000, "Flesh (fillets, surimi, mince)", src="[E]"),
        Sub("Surimi (crab sticks, kamaboko)", 170.3/catch, 2500, "Flesh (fillets, surimi, mince)", src="[S] GAPP ~$2,500-2,900/t"),
        Sub("Mince", 24.4/catch, 1500, "Flesh (fillets, surimi, mince)", src="[A]"),
        Sub("Roe", 20.8/catch, 6000, "Roe", src="[A]"),
        Sub("Fishmeal", 69.6/catch, 1700, "Meal & oil", src="[S] World Bank 2024-25 fishmeal ~$1,700/t"),
        Sub("Fish oil", 27.4/catch, 2500, "Meal & oil", src="[E]"),
    ]
    streams = [
        Stream("Flesh (fillets, surimi, mince)", "Fish", -1.10, None, "", "[S] whitefish fillets ~-0.5 to -1.9 (Asche et al. 2007)"),
        Stream("Roe", "Fish", -1.00, 0.30, "meal value", "[A]"),
        Stream("Meal & oil", "Fish", -5.00, None, "already the floor", "[A] at the outlet price: near-perfectly elastic for one supplier; aggregate fishmeal demand is inelastic (Tveteras 2010)"),
    ]
    return Branch("pollock", "Alaska pollock (wild, TAC-managed)", "per tonne round weight", 0.00, 0.05, subs, streams,
                  notes="Flesh is allocated between fillets and surimi (fungible sub-products); roe and meal are joint by-products.",
                  supply_src="[S] quota-managed capture: supply elasticity ~0 (World Bank 2013; estimates 0 to 0.17; can be negative)",
                  price_tag="NOAA 2024 production via SeafoodSource; GAPP surimi prices; EUMOFA fillet import prices")

def salmon():
    subs = [Sub("Salmon HOG, fillets and portions", 1.0, 75.0, "Salmon flesh", src="[S] NOK/kg 2026 YTD"),
            Sub("By-products (heads, frames, viscera, trimmings) -> oil, meal, pet food", 0.33, 7.0, "Salmon by-products", src="[S] SINTEF 2023")]
    streams = [Stream("Salmon flesh", "Fish", -1.00, None, "", "[S] salmon ~-1 (Asche et al. 2007)"),
               Stream("Salmon by-products", "Fish", -3.00, 0.30, "ensilage / biogas", "[A]")]
    return Branch("salmon", "Farmed Atlantic salmon (Norway)", "per kg HOG (NOK)", 0.10, 0.80, subs, streams,
                  notes="Flesh and by-products joint; by-products ~3% of value.",
                  supply_src="[S] Asheim et al. 2011 SR 0.09 / LR 0.14; Steen et al. 1997 LR 1.4-1.6; licences cap Norwegian biomass",
                  price_tag="Norwegian spot price 2026 YTD NOK 75/kg; by-product value ~NOK 7/kg (SINTEF)")

ALL = [dairy("2026"), dairy("2019"), beef(), eggs("2019-21"), eggs("2025"), broiler(), pork(), pollock(), salmon()]
