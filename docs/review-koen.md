# Review notes for Lode

Branch `review-koen`, from commit `fe9e69d`. Koen did the code and architecture review; he is not an economist, so
everything that touches the economics is listed here for you, Lode, to decide. Nothing below was changed silently.

## 1. Changes that alter published numbers (please check these first)

Each is its own commit, so you can revert it independently.

### 1a. Short-run supply elasticity may not exceed long-run (`268c2e3`)
You confirmed that short-run > long-run is impossible. The Monte Carlo drew the two independently, which broke this in
up to 1.4% of draws (dairy 0.5%, beef 0.3%, eggs 0%, broiler 1.2%, pork 1.2%, salmon 1.4%). The pair is now redrawn until
short-run <= long-run.
- Point estimates: unchanged. MC ranges: shift slightly (at most about 11% in a low-value tail percentile).
- Alternatives I did not choose (listed in the commit message): one shared factor; draw long-run, then short-run as a
  fraction of it; clamp. **Decision for you:** is redraw the right truncation?
- **To do:** re-check the Monte Carlo ranges quoted by hand in `paper/paper.md`.

### 1b. Exact solver at price caps (`ac92c18`)
Caps and floors make the supply and route-value curves flat or jumping. The bisection returned a bracket edge there. Two
defects, both now fixed and covered by tests:
1. **Constant-cost limit, capped stream fixed to the animal.** Eggs "Spent hen" returned A = -100% (a solver artefact)
   for every cap and for full loss. It is now about -0.005% to -0.05%.
2. **Route values not equalised.** A tolerance plus a rescale broke the model's own equal-value condition.

Rows that change materially (> 1e-3) in `exit_results.json` (14 groups): dairy 2019/2026 Fluid milk LR cap 0.9; eggs
(both) Shell eggs LR caps 0.9 and 0.75; Whole egg products LR cap 0.9; Spent hen constant-cost (5 caps).
`full_loss.json` Spent hen "limit" also changes. All other values move only in the 9th decimal.
Headline displacement factors use the closed form and are unchanged.
**Decision for you:** confirm the constant-cost reading of the spent-hen case, and any paper text quoting these rows.

## 2. Questions that need your judgement (not changed)

| # | Question | Where |
|---|---|---|
| 1 | **Displacement factor units.** Is DF output change per unit of demand change, or does "tonnes replaced x factor" (README) hold? If the former, the cheese figure may be about 0.47 per tonne rather than 0.28. | README, `edm_model.py` |
| 2 | **Broiler live-weight shares** add to 89.8% (value shares add to 100%). Needs your numbers. | `data/carcass_weight_and_value_shares.csv`, pinned in `tests/test_data_loaders.py` |
| 3 | **Mixed price vintages** across inputs. | `data/params/*.toml` |
| 4 | **Whey result** rests on assumed elasticity -1.5, floor 6%, recovery 0.50. By-product demand elasticities are mostly assumptions (the main sensitivity). | `data/params/dairy.toml` |
| 5 | **Constant-cost fallback** `b.results(1.0)` in `monte_carlo.py` when long-run supply elasticity is 0: where does 1.0 come from? | `monte_carlo.py` |
| 6 | **Modelling choices**: closed economy, fixed product mix (no trade, no substitution between species, no change in carcass cutting). | paper sections 11-12 |
| 7 | **Per-animal Monte Carlo seeding.** One shared generator means changing one animal shifts every range. Per-animal seeds are more robust but move all ranges. | `monte_carlo.py` |

## 3. What you need to run

The workbook and the 11 paper figures were **not** regenerated (they differ with matplotlib version). In your
environment: `python -m jpdm all`, then commit the workbook and figures, and re-check hand-quoted numbers in
`paper/paper.md`. Figures 7 and 10 have overlapping labels.

## 4. Result-neutral changes (for information)

| Commit | Change |
|---|---|
| `ea821f6` | Scenario parameters moved from `params.py` to `data/params/*.toml` (safe loader, same public API, results byte-identical). |
| `24d1609` | Monte Carlo settings moved to `data/monte_carlo.toml`; RNG passed explicitly. |
| `bfb558a` | Exact model reads `raw_shares` from the data; `solve()` returns equilibrium residual diagnostics. |
| `111cf9c` | `python -m jpdm check` compares all outputs numerically; CI uses it; `constraints.txt` pins the reproduce environment. |
| `9b404c3` | Validated loaders for the CSV files. |
| `d70063f` | Test: exact model and closed form agree for every stream of every branch at all three horizons. |
| `b871358` | `CITATION.cff` lists both licences; README test count. |

Verification: 148 tests pass; `python -m jpdm check` reproduces every committed result, table and doc.
