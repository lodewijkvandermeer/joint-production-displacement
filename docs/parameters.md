# Parameters

Generated from `data/params/*.toml` by `python -m jpdm docs`; do not edit by hand. Tags: **[S]** sourced (see [sources.md](sources.md)), **[E]** estimated from sourced inputs, **[A]** assumption. Prices are wholesale or first-handler, US$ unless stated; quantities are per the unit shown for each animal.

## Dairy cow (2026 prices)

Unit: per 100 lb milk + pro-rata cattle sales. Prices: USDA AMS announced class prices Sep 2026 (Class I Oct 2026 advance); Dairy Market News Oct 2026 for whey products.

Supply elasticity: 0.12 within a year, 0.9 after three to five years. [S] Chavas & Klemme 1986: 0.115 (current year), 0.89 (5-year), 2.46 (10-year); EU medium-run 0.18-0.65 (Bouamra-Mechemache et al. 2005)

Milk is fungible across routes; cheese and whey are joint in fixed proportions; whey outlets are fungible.

Raw-commodity routes (share of raw volume): Fluid 0.190; Other manufactured 0.080; Butter & powder 0.130; Cheese route 0.600

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Fluid milk | Fluid | -0.4 | none | [S] Andreyeva 2010 milk 0.59; Okrent & Alston 2012 milk 0.10; EU 0.53 |
| Other dairy | Other manufactured | -0.9 | none | [S] Okrent & Alston other dairy 1.04; yogurt 1.19 |
| Butter (fat) | Butter & powder | -0.6 | none | [S] EU butter 0.47; fats & oils 0.48 |
| Milk powder (nonfat solids) | Butter & powder | -1 | 0.6 (feed-grade SMP / export at world price) | [A] traded commodity, elastic for one supplier |
| Cheese | Cheese route | -0.55 | none | [S] Andreyeva cheese 0.44; Okrent & Alston 0.70; EU 0.60 |
| Whey protein | Cheese route | -1.5 | 0.0721304 (protein valued at the other-solids price, as in dry whey) | [A] ingredient with substitutes (SPI, MPC, pea); Houck soybean meal flexibility 1.12 |
| Whey carbohydrate | Cheese route | -2 | 0.5 (feed-grade whey / permeate) | [A] feed outlet, near-perfect substitutes |
| Cull cows | Cattle sales | -0.8 | 0.15 (rendering / pet food) | [S] beef demand 0.75 (Andreyeva) |
| Calves | Cattle sales | -0.6 | 0.05 (bob veal / euthanasia) | [A] derived from fed-beef demand |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fluid milk (Class I) | Fluid milk | 0.19 | 18.88 | 18.7% | 45.36 | 3% | 1 | [S] Class I price |
| Other dairy: yogurt, ice cream, etc. (Class II) | Other dairy | 0.08 | 17.6 | 7.3% | 45.36 |  | 1 | [S] Class II price |
| Butter / cream (3.5 lb fat per cwt) | Butter (fat) | 0.13 | 5.167 | 3.5% | 1.984 |  | 1 | [S] FMMO butterfat price x 3.5 |
| Nonfat dry milk / SMP (also the casein route) | Milk powder (nonfat solids) | 0.13 | 13.77 | 9.3% | 4.071 | 35% | 1 | [S] FMMO nonfat solids price x 9.3 x 0.965 |
| Cheese (cheddar-equivalent) | Cheese | 6.36 | 1.306 | 43.2% | 0.4536 | 25% | 10.6 | [S] cheese price less make allowance |
| WPC 80 (whey protein concentrate) | Whey protein | 0.1784 | 4.166 | 3.9% | 0.4536 | 80% | 0.8775 | [S] price and other-solids price; [A] processing allowance and theta_whey |
| WPI (whey protein isolate) | Whey protein | 0.1014 | 5.937 | 3.1% | 0.4536 | 90% | 0.78 | [S] price and other-solids price; [A] processing allowance and theta_whey |
| Dry whey (sweet whey powder) | Whey carbohydrate | 0.36 | 0.4026 | 0.8% | 0.4536 | 12% | 6 | [S] price and make allowance |
| Lactose | Whey carbohydrate | 0.54 | 0.43 | 1.2% | 0.4536 |  | 4.44 | [S] price; [A] allowance |
| Permeate / condensed whey / feed | Whey carbohydrate | 0.9 | 0.26 | 1.2% | 0.4536 |  | 5.22 | [S] feed-grade whey price |
| Cull cows (manufacturing beef) | Cull cows | 1 | 0.8994 | 4.7% |  |  | 1 | [S] ERS cattle sales share; [E] 60/40 split |
| Calves (beef-on-dairy, bull calves) | Calves | 1 | 0.5996 | 3.1% |  |  | 1 | [E] |

Per-unit conversions: 0.0041 cow-years and 45.36 kg milk per model unit. [S] NASS Milk Production, Disposition and Income 2025: 24,390 lb per cow (9.498 m cows, 231.7 bn lb)

## Dairy cow (2019 prices)

Unit: per 100 lb milk + pro-rata cattle sales. Prices: 2019-2021 reference levels: USDA AMS class prices and dry whey (2019-21 averages); WPC80 and WPI approximate trade levels.

Supply elasticity: 0.12 within a year, 0.9 after three to five years. [S] Chavas & Klemme 1986: 0.115 (current year), 0.89 (5-year), 2.46 (10-year); EU medium-run 0.18-0.65 (Bouamra-Mechemache et al. 2005)

Milk is fungible across routes; cheese and whey are joint in fixed proportions; whey outlets are fungible.

Raw-commodity routes (share of raw volume): Fluid 0.190; Other manufactured 0.080; Butter & powder 0.130; Cheese route 0.600

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Fluid milk | Fluid | -0.4 | none | [S] Andreyeva 2010 milk 0.59; Okrent & Alston 2012 milk 0.10; EU 0.53 |
| Other dairy | Other manufactured | -0.9 | none | [S] Okrent & Alston other dairy 1.04; yogurt 1.19 |
| Butter (fat) | Butter & powder | -0.6 | none | [S] EU butter 0.47; fats & oils 0.48 |
| Milk powder (nonfat solids) | Butter & powder | -1 | 0.6 (feed-grade SMP / export at world price) | [A] traded commodity, elastic for one supplier |
| Cheese | Cheese route | -0.55 | none | [S] Andreyeva cheese 0.44; Okrent & Alston 0.70; EU 0.60 |
| Whey protein | Cheese route | -1.5 | 0.109923 (protein valued at the other-solids price, as in dry whey) | [A] ingredient with substitutes (SPI, MPC, pea); Houck soybean meal flexibility 1.12 |
| Whey carbohydrate | Cheese route | -2 | 0.5 (feed-grade whey / permeate) | [A] feed outlet, near-perfect substitutes |
| Cull cows | Cattle sales | -0.8 | 0.15 (rendering / pet food) | [S] beef demand 0.75 (Andreyeva) |
| Calves | Cattle sales | -0.6 | 0.05 (bob veal / euthanasia) | [A] derived from fed-beef demand |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fluid milk (Class I) | Fluid milk | 0.19 | 17.6 | 18.0% | 45.36 | 3% | 1 | [S] Class I price |
| Other dairy: yogurt, ice cream, etc. (Class II) | Other dairy | 0.08 | 16.9 | 7.3% | 45.36 |  | 1 | [S] Class II price |
| Butter / cream (3.5 lb fat per cwt) | Butter (fat) | 0.13 | 8.05 | 5.6% | 1.984 |  | 1 | [S] FMMO butterfat price x 3.5 |
| Nonfat dry milk / SMP (also the casein route) | Milk powder (nonfat solids) | 0.13 | 8.975 | 6.3% | 4.071 | 35% | 1 | [S] FMMO nonfat solids price x 9.3 x 0.965 |
| Cheese (cheddar-equivalent) | Cheese | 6.36 | 1.55 | 52.9% | 0.4536 | 25% | 10.6 | [S] cheese price less make allowance |
| WPC 80 (whey protein concentrate) | Whey protein | 0.1755 | 0.9622 | 0.9% | 0.4536 | 80% | 0.8629 | [S] price and other-solids price; [A] processing allowance and theta_whey |
| WPI (whey protein isolate) | Whey protein | 0.09971 | 1.57 | 0.8% | 0.4536 | 90% | 0.767 | [S] price and other-solids price; [A] processing allowance and theta_whey |
| Dry whey (sweet whey powder) | Whey carbohydrate | 0.354 | 0.1509 | 0.3% | 0.4536 | 12% | 5.9 | [S] price and make allowance |
| Lactose | Whey carbohydrate | 0.531 | 0.15 | 0.4% | 0.4536 |  | 4.366 | [S] price; [A] allowance |
| Permeate / condensed whey / feed | Whey carbohydrate | 0.885 | 0.1 | 0.5% | 0.4536 |  | 5.133 | [S] feed-grade whey price |
| Cull cows (manufacturing beef) | Cull cows | 1 | 0.7818 | 4.2% |  |  | 1 | [S] ERS cattle sales share; [E] 60/40 split |
| Calves (beef-on-dairy, bull calves) | Calves | 1 | 0.5212 | 2.8% |  |  | 1 | [E] |

Per-unit conversions: 0.0041 cow-years and 45.36 kg milk per model unit. [S] NASS Milk Production, Disposition and Income 2025: 24,390 lb per cow (9.498 m cows, 231.7 bn lb)

## Fed steer (Oct 2026 prices)

Unit: per 1,400 lb Choice steer. Prices: USDA AMS boxed beef cutout 15 Oct 2026; by-product drop value 15 Oct 2026.

Supply elasticity: 0.15 within a year, 0.8 after three to five years. [S] Wohlgenant 1993 beef supply 0.15 (SR); Lusk & Norwood 2009 LR 0.82; Harrington & Dubman 2008: 1.07

Carcass cuts in fixed proportions (one route); grinding is a one-way re-route handled as a floor on whole-cut streams in the text.

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Middle meats (whole cut) | Carcass | -1 | none | [S] beef 0.75 (Andreyeva); steaks more elastic in scanner data (Tonsor & Lusk 2024) |
| End meats (whole cut) | Carcass | -0.9 | none | [A] as beef |
| Minced beef (grinding material) | Carcass | -0.85 | 0.3 (pet food / rendering) | [S] beef 0.75; ground beef 1.25 (farmdoc 2021) |
| Drop credit | Carcass | -2.5 | 0.4 (rendering / disposal; hides already near disposal value) | [A] traded by-products: hides, tallow, offal exports |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Middle meats: steaks and roasts from rib and loin | Middle meats (whole cut) | 288.1 | 5.289 | 43.4% | 0.4536 |  | 288.1 | [S] AMS primals |
| End-meat whole-muscle cuts (chuck/round roasts, steaks; 50% of chuck+round) | End meats (whole cut) | 229.1 | 3.352 | 21.9% | 0.4536 |  | 229.1 | [E] split of chuck/round |
| Thin-meat whole-muscle (brisket, flank, skirt; 40% of thin meats) | End meats (whole cut) | 54.33 | 2.643 | 4.1% | 0.4536 |  | 54.33 | [E] |
| Grinding material: trim and ground chuck/round (minced beef) | Minced beef (grinding material) | 310.6 | 2.78 | 24.6% | 0.4536 |  | 310.6 | [E] 50% of chuck/round + 60% of thin meats |
| Hide | Drop credit | 1 | 24.5 | 0.7% |  |  | 1 | [S] AMS drop value 15 Oct 2026 |
| Tallow and technical fat | Drop credit | 1 | 54.04 | 1.5% |  |  | 1 | [S] |
| Edible offal (tongue, cheek, oxtail, liver, tripe, hearts, lips) | Drop credit | 1 | 113.8 | 3.2% |  |  | 1 | [S] |
| Meat & bone meal, blood meal | Drop credit | 1 | 19.32 | 0.6% |  |  | 1 | [S] |

Per-unit conversions: 1 fed cattle and 635 kg live weight per model unit. one fed steer per model unit; the cow-calf herd behind it is not counted

## Layer hen (2019-21 prices)

Unit: per dozen eggs + pro-rata spent hen. Prices: USDA AMS Oct 2019 egg-products prices; shell eggs ~2019 annual average (approx.).

Supply elasticity: 0.03 within a year, 1.0 after three to five years. [S] Chavas 1980 SR 0.03; Chavas & Johnson 1981 LR ~1; Harrington & Dubman 2008: 1.04

Eggs flow between shell and breaking (fungible routes); white and yolk are joint in fixed proportions.

Raw-commodity routes (share of raw volume): Shell 0.680; Products: whole 0.205; Products: separated 0.115

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Shell eggs | Shell | -0.27 | none | [S] Andreyeva 2010 eggs 0.27; Okrent & Alston 0.24; Bakhtavoryan 2021 conventional 0.235 |
| Whole egg products | Products: whole | -0.8 | 0.5 (dried whole-egg inventory / export / feed) | [A] breaker demand more elastic than table demand (Blakely 1984) |
| Egg white | Products: separated | -1.5 | 0.35 (dried albumen at surplus prices / feed) | [A] ingredient with substitutes |
| Egg yolk | Products: separated | -1 | 0.5 (industrial yolk (pet food, feed)) | [A] |
| Spent hen | Spent hen | -5 | 0 (rendering / composting) | [A] effectively perfectly elastic at ~0 |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Shell eggs (table) | Shell eggs | 0.68 | 0.95 | 82.8% | 0.5851 | 13% | 1 | [S] |
| Liquid/frozen whole egg | Whole egg products | 0.2642 | 0.33 | 11.2% | 0.4536 | 13% | 1.29 | [S] |
| Liquid egg white (albumen): liquid, dried albumen, protein fractions | Egg white | 0.09685 | 0.23 | 2.9% | 0.4536 | 11% | 0.8407 | [S] |
| Liquid egg yolk | Egg yolk | 0.05176 | 0.46 | 3.1% | 0.4536 | 16% | 0.4493 | [S] |
| Spent hen (soup meat, rendering) | Spent hen | 0.04 | 0.02 | 0.1% |  |  | 0.04 | [S] removal cost 0-5 c/head: nominal $0.02 |

Per-unit conversions: 0.04167 hen-years and 0.5851 kg liquid egg per model unit. [S] NASS Chickens and Eggs 2025 Summary: 288 eggs per layer (all layers, 2025)

## Layer hen (2025 prices)

Unit: per dozen eggs + pro-rata spent hen. Prices: USDA AMS Sep 2025 (HPAI-tight market).

Supply elasticity: 0.03 within a year, 1.0 after three to five years. [S] Chavas 1980 SR 0.03; Chavas & Johnson 1981 LR ~1; Harrington & Dubman 2008: 1.04

Eggs flow between shell and breaking (fungible routes); white and yolk are joint in fixed proportions.

Raw-commodity routes (share of raw volume): Shell 0.680; Products: whole 0.205; Products: separated 0.115

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Shell eggs | Shell | -0.27 | none | [S] Andreyeva 2010 eggs 0.27; Okrent & Alston 0.24; Bakhtavoryan 2021 conventional 0.235 |
| Whole egg products | Products: whole | -0.8 | 0.5 (dried whole-egg inventory / export / feed) | [A] breaker demand more elastic than table demand (Blakely 1984) |
| Egg white | Products: separated | -1.5 | 0.35 (dried albumen at surplus prices / feed) | [A] ingredient with substitutes |
| Egg yolk | Products: separated | -1 | 0.5 (industrial yolk (pet food, feed)) | [A] |
| Spent hen | Spent hen | -5 | 0 (rendering / composting) | [A] effectively perfectly elastic at ~0 |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Shell eggs (table) | Shell eggs | 0.68 | 2.08 | 70.9% | 0.5851 | 13% | 1 | [S] |
| Liquid/frozen whole egg | Whole egg products | 0.2642 | 1.155 | 15.3% | 0.4536 | 13% | 1.29 | [S] |
| Liquid egg white (albumen): liquid, dried albumen, protein fractions | Egg white | 0.09685 | 0.914 | 4.4% | 0.4536 | 11% | 0.8407 | [S] |
| Liquid egg yolk | Egg yolk | 0.05176 | 3.57 | 9.3% | 0.4536 | 16% | 0.4493 | [S] |
| Spent hen (soup meat, rendering) | Spent hen | 0.04 | 0.02 | 0.0% |  |  | 0.04 | [S] removal cost 0-5 c/head: nominal $0.02 |

Per-unit conversions: 0.04167 hen-years and 0.5851 kg liquid egg per model unit. [S] NASS Chickens and Eggs 2025 Summary: 288 eggs per layer (all layers, 2025)

## Broiler (Jan 2025 prices)

Unit: per 6.0 lb live bird. Prices: USDA AMS weekly national composite 24 Jan 2025; Cobb 500 yield poster.

Supply elasticity: 0.1 within a year, 0.7 after three to five years. [S] Kapombe & Colyer 1998 SR 0.07 / LR 0.13; Chavas & Johnson 1982 0.02; Lusk & Norwood 2009 LR 0.70; Harrington & Dubman 1.15

Carcass parts in fixed proportions.

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Breast meat | Carcass | -0.8 | none | [S] poultry 0.68 (Andreyeva); 0.81 (Okrent & Alston) |
| Wings | Carcass | -1 | none | [A] |
| Dark meat | Carcass | -1.5 | 0.25 (pet food / rendering; exported at world price) | [A] export-exposed, elastic |
| Backs & necks (MSC) | Carcass | -3 | 0.5 (rendering) | [A] residual raw material |
| Giblets & paws | Carcass | -2 | 0.15 (rendering) | [A] |
| Rendering | Carcass | -5 | none | [A] |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Boneless skinless breast (fillets, whole-muscle nuggets) | Breast meat | 1.323 | 1.486 | 45.2% | 0.4536 | 22% | 1.323 | [S] Cobb yield; AMS price |
| Tenders | Breast meat | 0.24 | 1.734 | 9.6% | 0.4536 | 22% | 0.24 | [S] |
| Wings | Wings | 0.4548 | 1.906 | 19.9% | 0.4536 |  | 0.4548 | [S] |
| Leg quarters / dark meat (whole legs) | Dark meat | 1.381 | 0.514 | 16.3% | 0.4536 |  | 1.381 | [S] Cobb whole legs 23.01% (leg quarters 31.62% include the back) |
| Backs, necks, frames -> mechanically separated chicken (MSC nuggets, hot dogs) | Backs & necks (MSC) | 0.726 | 0.125 | 2.1% | 0.4536 |  | 0.726 | [S] backs/necks price |
| Giblets | Giblets & paws | 0.18 | 0.4 | 1.7% | 0.4536 |  | 0.18 | [A] |
| Paws (export) | Giblets & paws | 0.27 | 0.6 | 3.7% | 0.4536 |  | 0.27 | [E] from FAS export unit values |
| Feathers, blood, viscera, heads -> rendering | Rendering | 0.81 | 0.08 | 1.5% | 0.4536 |  | 0.81 | [E] rendered meal values |

Per-unit conversions: 1 birds and 2.722 kg live weight per model unit. one bird per model unit

## Hog (Sep 2026 prices)

Unit: per 280 lb live hog. Prices: USDA AMS pork cutout week ending 25 Sep 2026; hog by-product value 9 Oct 2026.

Supply elasticity: 0.4 within a year, 1.5 after three to five years. [S] Wohlgenant 1993 hog supply 0.40 (SR); Lusk & Norwood 2009 LR 1.56; Harrington & Dubman 0.79

Carcass primals in fixed proportions.

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Fresh pork cuts | Carcass | -0.9 | none | [S] pork 0.72 (Andreyeva); loin 1.45 scanner (Tonsor & Lusk 2024) |
| Ham | Carcass | -0.75 | none | [A] processed, inelastic |
| Belly | Carcass | -0.8 | none | [S] bacon 0.83 scanner |
| Sausage & trim | Carcass | -1.2 | 0.3 (pet food / rendering) | [A] trim competes with beef and poultry trim |
| Variety meats & drop | Carcass | -2.5 | 0.4 (rendering) | [A] |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Loin (chops, roasts) | Fresh pork cuts | 54.12 | 0.879 | 23.1% | 0.4536 |  | 54.12 | [S] |
| Butt (shoulder) | Fresh pork cuts | 21.84 | 1.115 | 11.8% | 0.4536 |  | 21.84 | [S] |
| Spareribs | Fresh pork cuts | 10.34 | 1.592 | 8.0% | 0.4536 |  | 10.34 | [S] |
| Ham (mostly cured) | Ham | 52.87 | 0.869 | 22.3% | 0.4536 |  | 52.87 | [S] |
| Belly (bacon) | Belly | 35 | 0.968 | 16.5% | 0.4536 |  | 35 | [S] |
| Picnic, jowl, neck bones, trim -> sausage, ground pork | Sausage & trim | 31.2 | 0.66 | 10.0% | 0.4536 |  | 31.2 | [S] picnic; [E] jowl/neck |
| Feet, tails (export, variety meats) | Variety meats & drop | 4.945 | 0.5 | 1.2% | 0.4536 |  | 4.945 | [A] |
| Drop credit (lard, offal, meals, plasma) | Variety meats & drop | 1 | 14.34 | 7.0% |  |  | 1 | [S] AMS hog by-product value 9 Oct 2026 |

Per-unit conversions: 1 hogs and 127 kg live weight per model unit. one market hog per model unit; the breeding herd is not counted

## Alaska pollock (wild, TAC-managed)

Unit: per tonne round weight. Prices: NOAA 2024 production via SeafoodSource; GAPP surimi prices; EUMOFA fillet import prices.

Supply elasticity: 0.0 within a year, 0.05 after three to five years. [S] quota-managed capture: supply elasticity ~0 (World Bank 2013; estimates 0 to 0.17; can be negative)

Flesh is allocated between fillets and surimi (fungible sub-products); roe and meal are joint by-products.

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Flesh (fillets, surimi, mince) | Fish | -1.1 | none | [S] whitefish fillets ~-0.5 to -1.9 (Asche et al. 2007) |
| Roe | Fish | -1 | 0.3 (meal value) | [A] |
| Meal & oil | Fish | -5 | none | [A] at the outlet price: near-perfectly elastic for one supplier; aggregate fishmeal demand is inelastic (Tveteras 2010) |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fillet blocks and fillets (fish fingers, portions) | Flesh (fillets, surimi, mince) | 0.1175 | 4500 | 47.0% | 1000 |  | 0.1175 | [S] volumes; [E] prices |
| H&G (headed and gutted) | Flesh (fillets, surimi, mince) | 0.02797 | 2000 | 5.0% | 1000 |  | 0.02797 | [E] |
| Surimi (crab sticks, kamaboko) | Flesh (fillets, surimi, mince) | 0.1191 | 2500 | 26.4% | 1000 |  | 0.1191 | [S] GAPP ~$2,500-2,900/t |
| Mince | Flesh (fillets, surimi, mince) | 0.01706 | 1500 | 2.3% | 1000 |  | 0.01706 | [A] |
| Roe | Roe | 0.01455 | 6000 | 7.8% | 1000 |  | 0.01455 | [A] |
| Fishmeal | Meal & oil | 0.04867 | 1700 | 7.3% | 1000 |  | 0.04867 | [S] World Bank 2024-25 fishmeal ~$1,700/t |
| Fish oil | Meal & oil | 0.01916 | 2500 | 4.3% | 1000 |  | 0.01916 | [E] |

Per-unit conversions: 1667 fish and 1000 kg round weight per model unit. [A] about 0.6 kg average round weight per fish

## Farmed Atlantic salmon (Norway)

Unit: per kg HOG (NOK). Prices: Norwegian spot price 2026 YTD NOK 75/kg; by-product value ~NOK 7/kg (SINTEF).

Supply elasticity: 0.1 within a year, 0.8 after three to five years. [S] Asheim et al. 2011 SR 0.09 / LR 0.14; Steen et al. 1997 LR 1.4-1.6; licences cap Norwegian biomass

Flesh and by-products joint; by-products ~3% of value.

| Stream | Route | Demand elasticity | Floor (share of today's price) | Source |
| --- | --- | --- | --- | --- |
| Salmon flesh | Fish | -1 | none | [S] salmon ~-1 (Asche et al. 2007) |
| Salmon by-products | Fish | -3 | 0.3 (ensilage / biogas) | [A] |

| Product | Stream | Quantity per unit | Price | Value share | kg per quantity unit | Protein | Naive yield per unit | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Salmon HOG, fillets and portions | Salmon flesh | 1 | 75 | 97.0% | 1 |  | 1 | [S] NOK/kg 2026 YTD |
| By-products (heads, frames, viscera, trimmings) -> oil, meal, pet food | Salmon by-products | 0.33 | 7 | 3.0% | 1 |  | 0.33 | [S] SINTEF 2023 |

Per-unit conversions: 0.2222 fish and 1 kg head-on gutted per model unit. [A] about 4.5 kg head-on gutted per harvested fish
