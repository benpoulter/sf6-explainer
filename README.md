# SF₆: a small emission with a large warming effect

An explainer on sulfur hexafluoride (SF₆) emissions, concentrations and warming, comparing bottom-up inventories with an atmospheric inversion and CMIP7 scenarios.

**Live page:** https://benpoulter.github.io/sf6-explainer/

The page was generated using Claude Opus 5.5. Several numbers on it are calculations made for this page rather than published values (the country and regional sums of gridded data, the one-box concentrations and the warming estimates); they are marked as such on the page, and this repository holds the data and scripts behind them. Comments and corrections are welcome as [GitHub issues](https://github.com/benpoulter/sf6-explainer/issues); the "Comments welcome" section at the bottom of the page opens one with the section filled in.

## Repository layout

```
index.html        the page: one self-contained file with all data embedded (d3 v7 from cdnjs)
data/             processed series behind the page, as CSV (tonnes SF₆ per year unless stated)
scripts/          Python scripts that regenerate data/ from the raw sources
raw/              raw inputs, not committed (downloaded by the scripts or placed by hand)
```

## Data

| File | Contents | Source |
|---|---|---|
| `edgar_sf6_country_sector_t.csv` | Emissions by country and IPCC source category, 1990–2025 | EDGAR_2026_GHG F-gases, European Commission JRC (Gg converted to t). Taken from the page, where it was prepared before this repository existed. |
| `unfccc_crt2025_sf6_t.csv` | Emissions reported in the 2025 national inventory submissions, 1990–2023, 42 parties | UNFCCC common reporting tables, Table 10 sheet 5, row SF₆ (kt converted to t). The US did not submit in 2025; Belarus reported "FX" (flexibility); the EU's own trend table is blank, so the page sums the 27 member states. |
| `gains_sf6_country_t.csv` | GAINS model emissions by country, 2005–2020 | Purohit and Lindl (2024), Gridded Global Emissions of SF₆, IIASA, [doi:10.5281/zenodo.12708771](https://doi.org/10.5281/zenodo.12708771), summed from the 0.5° grid. |
| `inversion_vojta_edgarrun_country_t.csv` | Atmospheric inversion by country, 2005–2021: posterior and the EDGAR v8 prior | Vojta (2025), [doi:10.5281/zenodo.18033046](https://doi.org/10.5281/zenodo.18033046): the run seeded with EDGAR v8, summed from the 1° grid. |
| `vojta2024_tables_A1_A4_t.csv` | Inversion average of three runs, with minimum and maximum, for the world, China, the US and the EU-27, 2005–2021 | Vojta et al. (2024), Atmos. Chem. Phys. 24, 12465–12493, [doi:10.5194/acp-24-12465-2024](https://doi.org/10.5194/acp-24-12465-2024), appendix tables A1–A4 (transcribed). |
| `region_definitions.csv`, `regional_totals_t.csv` | Country lists and regional sums of EDGAR, GAINS and the inversion | Built by `04_regions_and_tables.py` (see Methods). |
| `noaa_sf6_global_monthly_ppt.csv` | Global monthly mean concentration, July 1997 onward | NOAA Global Monitoring Laboratory, [sf6_mm_gl.txt](https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_mm_gl.txt). The latest year is preliminary. |
| `scenariomip_cmip7_sf6_emissions_t.csv` | Global emissions in the seven CMIP7 marker scenarios, 2023–2100 | ScenarioMIP-CMIP7 IAM quantification v0.2, harmonized and infilled emissions, [doi:10.5281/zenodo.19825038](https://doi.org/10.5281/zenodo.19825038). |
| `onebox_scenario_concentration_ppt.csv` | Concentrations implied by each scenario's emissions for lifetimes of 850, 1,278 and 3,200 years | One-box calculation (see Methods). |
| `cmip7_sf6_concentration_ppt.csv` | CMIP7 concentrations, 1950–2300: historical to 2021, then each scenario; plus emissions stopping in 2026 | Historical: CR-CMIP-1-0-0, [doi:10.5281/zenodo.14892947](https://doi.org/10.5281/zenodo.14892947). Scenarios: CMIP7 ScenarioMIP GHG forcing, [doi:10.5281/zenodo.19243739](https://doi.org/10.5281/zenodo.19243739). Values after 2100 are the stylised CMIP7 extensions. |
| `warming_sf6_degC.csv` | Warming caused by SF₆, 1950–2300, for equilibrium climate sensitivity 2.5, 3.0 and 4.0 K | Two-layer climate emulator (see Methods). |
| `countries_simplified.geojson` | Simplified country boundaries keyed by ISO3, used for all grid-to-country sums | Natural Earth via datasets/geo-countries, simplified. Taken from the page. |

## Methods

**Grid to country.** Each grid cell with emissions goes to the country whose polygon contains the cell centre; coastal cells whose centre falls in the sea go to the nearest country within 1.5°. The same simplified boundaries are used for GAINS and the inversion. Small countries and border regions can be misallocated, especially on the inversion's 1° grid. Checks against published totals: the GAINS global sum matches the file (2.39 kt in 2005, 9.55 kt in 2020); the inversion sums are within 1–3% of the paper's EDGAR-run tables (world 9,410 vs 9,500 t, US 602 vs 620 t, China 5,090 vs 5,210 t in 2021).

**Inversion uncertainty.** The inversion grid gives a standard deviation per cell but not the error covariance between cells, so country and regional uncertainty cannot be rebuilt from it; adding cell uncertainties gives about a third of the paper's ranges. The page therefore shows uncertainty bands only for the paper's tabulated regions.

**Regions.** Africa: UN M49 Africa. Middle East: Gulf states, Iran, Iraq, the Levant and Yemen (Turkey and Egypt excluded). Latin America and the Caribbean: UN M49. Asia: UN M49 Central, Eastern, South-eastern and Southern Asia, with Iran counted in the Middle East. Full lists are in `region_definitions.csv`.

**Concentration from emissions (one box).** Starting from NOAA's 2023 annual mean, each year adds that year's emissions (1 ppt ≈ 25,853 t, from 1.77 × 10²⁰ mol of dry air and 146.06 g/mol) and removes a fraction 1 − e^(−1/τ). The lifetimes are 850 years (Ray et al., 2017), 1,278 years (Kovács et al., 2017) and 3,200 years (IPCC AR6). At τ = 1,278 years the one-box values agree with the official CMIP7 concentrations to within about 0.5 ppt in 2100.

**Warming.** Radiative forcing = 0.567 W m⁻² ppb⁻¹ × concentration (IPCC AR6 Table 7.SM.7). Temperature follows the AR6 two-layer emulator used for its emission metrics (Chapter 7 Supplementary Material, 7.SM.5.2): C = 7.7 and C₀ = 147 W yr m⁻² K⁻¹, λ = 1.31 W m⁻² K⁻¹, efficacy ε = 1.03, κ = 0.88 W m⁻² K⁻¹, giving ECS 3.0 K and TCR 1.8 K (checked by the script). The likely range scales λ for ECS 2.5 to 4.0 K; it does not include uncertainty in radiative efficiency or emissions. The "emissions stop in 2026" case holds concentrations on the record to 2025 and then lets them decay with a 1,278-year lifetime.

**Known limitations.**
- EDGAR "world" totals are sums over the 76 countries in its file; countries it doesn't list are missing, and the latest years are preliminary.
- The emissions check in section 01 converts NOAA's surface growth rate with whole-atmosphere air mass. This overstates emissions because the stratosphere lags the surface; the page says so and points to the inversion instead.
- The country-level inversion data is a single run seeded with EDGAR, so it is partly anchored to EDGAR. At 1° resolution, emissions near borders can be assigned to the wrong country (for example South Korea or Taiwan next to China's coast).
- The GAINS country totals reflect how GAINS spread emissions across its grid, not GAINS's own national estimates.
- CO₂-equivalent figures use EDGAR's 100-year warming potential of 23,500 (IPCC AR5) unless stated; AR6's 25,200 raises them by about 7%.
- The avoidable-warming comparison (High scenario vs. emissions stopping in 2026) spans two extremes; the page also gives the smaller Medium-vs-Very-Low difference. Warming values are tabulated to four decimals only to separate scenarios.

**Other figures on the page.** Total human-caused forcing (3.10 W m⁻²) and warming (1.37 °C) in 2025: Indicators of Global Climate Change 2025. Fossil CO₂ (38.1 Gt in 2025) and the remaining 1.5 °C budget (170 Gt): Global Carbon Budget 2025. Warming per tonne of CO₂ (0.45 °C per 1,000 Gt) and 20-, 100- and 500-year warming potentials: IPCC AR6. Abatement costs: US EPA (2019). Further sources are listed at the foot of the page.

## Reproducing the data

```bash
pip install -r scripts/requirements.txt
./scripts/run_all.sh
```

`run_all.sh` ends with two checks that fail on any difference: `06_checks.py` compares the outputs with published values (for example the inversion's country sums against the paper's tables) and with figures quoted on the page, and `07_page_matches_data.py` confirms that the series embedded in `index.html` match the CSVs in `data/`.

Most inputs download automatically into `raw/`. Three need placing by hand:

- **UNFCCC 2025 CRT files:** one folder per party, `raw/unfccc-crt-2025/<ISO3>/<document id>/<file>.zip`, from the [UNFCCC 2025 submissions page](https://unfccc.int/ghg-inventories-annex-i-parties/2025). The site blocks automated downloads; the same set is mirrored at `https://data.industrydecarbonization.com/unfccc/2025-unfccc-crt.tar.xz` in this layout.
- **CMIP7 historical concentrations:** extract `output-bundles/v1.0.0/data/interim/sf6/sf6_global-mean_annual-mean.nc` from `data--interim.tar.gz` in [zenodo.14892947](https://doi.org/10.5281/zenodo.14892947) and save it as `raw/cmip7_historical_sf6_global-mean_annual-mean.nc`.
- **CMIP7 scenario concentrations:** extract `data/interim/annual-means/one-box_sf6_annual-mean.feather` from `data--interim--annual-means.tar.gz` in [zenodo.19243739](https://doi.org/10.5281/zenodo.19243739) and save it as `raw/cmip7_scenarios_sf6_annual-mean.feather`.

The scripts write `data/` only; the page itself (`index.html`) embeds the same series and is edited separately.
