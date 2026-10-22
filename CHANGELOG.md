# Changelog

## 1.1.0 (22 October 2026)

Per-unit outputs, a revised valuation of whey protein, and fixes after the code review of version 1.0.

- **What the factor measures.** The displacement factor of 1.0 is the % change in animal output per % of a product's
  market displaced. It is renamed the market-share factor. For products fixed to the animal (carcass parts, cull
  cows, spent hens) it is also the share of each tonne displaced that leaves production; 1.0's README and paper read it
  that way for every product, which was wrong for routed and joint products (cheese, whey, egg products, fluid milk).
- **New outputs** (`per_unit.py`, `results/per_unit.json`, `results/tables/per_kg*.md`, workbook sheet Per kg):
  animals and raw commodity removed per tonne displaced, animals per tonne of protein, and the multiplier (animals'
  worth displaced per animal removed, against the naive rule that credits a product with all the raw material needed
  to make it), at three horizons, with 80% ranges and whole-market averages. Conversions: NASS 2025 milk per cow and
  eggs per hen; one bird, steer or hog per carcass.
- **The discount step by step** (`Branch.steps`, `per_unit.grouped_steps`, `results/tables/steps.md`, Figure 7):
  value share, buyers' price response, horizon, and a yield basis for products sharing a stream.
- **Whey protein valuation.** WPC 80 and WPI are valued at the protein's federal-order other-solids value plus a
  share theta of the premium above it (0.5 central; 0 and 1 in `results/tables/theta.md`). 1.0 counted all of it as
  milk value (theta = 1). Whey protein falls from 12.6% to 7.0% of the dairy cow's value at 2026 prices; cheese rises
  from 40.4% to 43.2%; every dairy number moves. The whey protein floor is the other-solids value.
- Monte Carlo: by-product dominance statistics recorded; ranges updated for the short-run <= long-run truncation.
- Figures: 12 (new Figure 7; Figures 6 and 12 now show multipliers; titles no longer clipped).
- Broiler weight shares: labelled residual row for the 10.2% of live weight not sold.
- Figure 12's reachability file now points at model streams instead of storing factors.

## 1.0.0 (October 2026)

First public release, matching the working paper of October 2026.

- Closed-form nested displacement model for seven animals and about fifty products, at three horizons.
- Exact non-linear solution with price floors, price caps and route exits; full-loss and price-cap scenarios.
- Monte Carlo ranges over the demand and supply elasticities (2,000 draws per animal, fixed seed).
- Excel workbook with live formulas; paper tables and figures generated from the model.
- Egg and milk routes weighted by raw volume; weighting them by value would overstate the shell-egg factor by about
  a third and understate the egg-product factors by about half.
