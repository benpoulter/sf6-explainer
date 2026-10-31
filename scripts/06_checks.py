"""Sanity checks on data/: processed series against published values and against figures quoted on the page.
Run after scripts 00-05; exits with an error if any check fails."""
import csv
import sys

from common import DATA, EU27, REGIONS

failures = []


def check(name, value, target, tol):
    ok = abs(value - target) <= tol
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {value:,.4g} (expected {target:,.4g} ± {tol:,.4g})")
    if not ok:
        failures.append(name)


def table(path, *key):
    out = {}
    for r in csv.DictReader(open(DATA / path)):
        out[tuple(r[k] for k in key) if len(key) > 1 else r[key[0]]] = {int(y): float(v) for y, v in r.items() if y.isdigit() and v != ""}
    return out


edgar = {k[0]: v for k, v in table("edgar_sf6_country_sector_t.csv", "iso3", "sector").items() if k[1] == "Total"}
unfccc = table("unfccc_crt2025_sf6_t.csv", "iso3")
gains = table("gains_sf6_country_t.csv", "iso3")
inv = {k[0]: v for k, v in table("inversion_vojta_edgarrun_country_t.csv", "iso3", "field").items() if k[1] == "posterior"}
warm = table("warming_sf6_degC.csv", "scenario", "ecs_K")
box = table("onebox_scenario_concentration_ppt.csv", "scenario", "lifetime_years")
cmip = table("cmip7_sf6_concentration_ppt.csv", "scenario")
s = lambda d, isos, y: sum(d[c][y] for c in isos if c in d and y in d[c])

# Inputs
check("EDGAR countries", len(edgar), 76, 0)
check("EDGAR world 2025 (t)", s(edgar, edgar, 2025), 9770, 5)
check("UNFCCC parties with SF6 data", len(unfccc), 42, 0)
check("UNFCCC EU-27 sum 2021 (t)", s(unfccc, EU27, 2021), 209, 1)
check("GAINS world 2020 (t, file total 9,549)", s(gains, gains, 2020), 9549, 10)
# Inversion sums against Vojta et al. (2024) EDGAR-run tables, 2021 (expect within ~3%)
check("Inversion US 2021 vs paper (t)", inv["USA"][2021], 620, 0.04 * 620)
check("Inversion China 2021 vs paper (t)", inv["CHN"][2021], 5210, 0.04 * 5210)
check("Inversion EU-27 2021 vs paper (t)", s(inv, EU27, 2021), 250, 0.04 * 250)
# Regional figures quoted on the page
check("Africa EDGAR 2021 (t)", s(edgar, REGIONS["Africa"], 2021), 246, 1)
check("Middle East inversion 2021 (t)", s(inv, REGIONS["Middle East"], 2021), 833, 2)
check("Asia GAINS 2020 (t)", s(gains, REGIONS["Asia"], 2020), 8710, 10)
# Concentrations and warming
check("One-box High 2100 vs CMIP7 (ppt)", box[("High", "1278")][2100], cmip["High"][2100], 0.6)
check("Warming 2025, ECS 3 (degC)", warm[("Medium", "3.0")][2025], 0.0029, 0.0001)
check("Warming High 2100 (degC)", warm[("High", "3.0")][2100], 0.0115, 0.0001)
check("Warming, stop in 2026, 2100 (degC)", warm[("Emissions stop in 2026", "3.0")][2100], 0.0035, 0.0001)
check("Avoided, High vs stop, 2200 (degC)", warm[("High", "3.0")][2200] - warm[("Emissions stop in 2026", "3.0")][2200], 0.0174, 0.0002)

check("Avoided, Medium vs Very Low, 2100 (degC, page: < 0.001)", warm[("Medium", "3.0")][2100] - warm[("Very Low", "3.0")][2100], 0.0009, 0.0001)
check("Avoided, Medium vs Very Low, 2200 (degC)", warm[("Medium", "3.0")][2200] - warm[("Very Low", "3.0")][2200], 0.0035, 0.0001)
emis = table("scenariomip_cmip7_sf6_emissions_t.csv", "scenario", "model")
high = next(v for k, v in emis.items() if k[0] == "High")
check("High 2026-2100 at GWP 23,500 (Gt CO2e)", sum(high[y] for y in range(2026, 2101)) * 23500 / 1e9, 19.4, 0.1)

# Figures from the "Where the emissions come from" and "What the map shows" sections
sectors = table("edgar_sf6_country_sector_t.csv", "iso3", "sector")
world25 = s(edgar, edgar, 2025)
share = lambda code: 100 * sum(v[2025] for k, v in sectors.items() if k[1].startswith(code)) / world25
check("Electrical equipment share 2025 (%, page: 92)", share("2.G"), 92, 0.5)
check("Metal industry share 2025 (%, page: 5)", share("2.C"), 5, 0.5)
check("Electronics share 2025 (%, page: 3)", share("2.E"), 3, 0.5)
check("Chemical production share 2025 (%, page: 1)", share("2.B"), 1, 0.5)
check("Countries with production emissions (page: 8)", sum(1 for k, v in sectors.items() if k[1].startswith("2.B") and max(v.values()) > 0), 8, 0)
check("China share of EDGAR 2025 (%, page: 74)", 100 * edgar["CHN"][2025] / world25, 74, 0.5)
check("First year China is the largest emitter (page: 2008)", min(y for y in range(1990, 2026) if max(edgar, key=lambda c: edgar[c][y]) == "CHN"), 2008, 0)

if failures:
    sys.exit(f"{len(failures)} check(s) failed: {', '.join(failures)}")
print("all checks passed")
