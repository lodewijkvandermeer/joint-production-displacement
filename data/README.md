# Data files

Inputs used for figures that are not computed by the model. Every parameter the model itself uses is in
`src/jpdm/params.py` (listed in `docs/parameters.md`).

| File | Contents | Source | Used in |
| --- | --- | --- | --- |
| `whey_prices_central_us_2022_2026.csv` | Monthly average "mostly" prices, Central US dry whey and WPC 34%, January 2022 to September 2026, USD per lb | USDA AMS Dairy Market News | Figure 5 |
| `carcass_weight_and_value_shares.csv` | Share of live weight and of animal value by part for the fed steer, broiler and hog | Model aggregation of USDA AMS boxed beef cutout and drop value (15 Oct 2026), pork cutout (week ending 25 Sep 2026) and hog by-product values, chicken parts prices (24 Jan 2025), Cobb 500 yields | Figure 4 |
| `technical_reachability.csv` | Technical reachability for biotechnology today (1 low, 2 low to medium, 3 medium, 4 high) and the product's displacement factor after three to five years | Reachability is the authors' judgement from the state of the technologies (paper, section 8); factors from the model | Figure 11 |

The feed-grade dry whey quote of $0.35 to $0.38 per lb (5 to 9 October 2026, USDA AMS) sets the floor shown in Figure 5.
