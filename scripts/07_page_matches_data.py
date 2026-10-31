"""Check that the series embedded in index.html match the CSVs in data/, so the page and the repository
cannot drift apart. Run after scripts 00-05; exits with an error on any mismatch."""
import csv
import json
import re
import sys

from common import DATA, ROOT

html = (ROOT / "index.html").read_text()
dec = json.JSONDecoder()


def const(name):
    """Value of a data constant, declared either as 'const X=' or as ',X=' in a multi-name declaration."""
    m = re.search(r"(?:const |,)" + name + r"=(?=[\[{])", html)
    return dec.raw_decode(html, m.end())[0]


def table(path, *key):
    out = {}
    for r in csv.DictReader(open(DATA / path)):
        out[tuple(r[k] for k in key) if len(key) > 1 else r[key[0]]] = {int(y): float(v) for y, v in r.items() if y.isdigit() and v != ""}
    return out


failures = []


def compare(label, page_series, data_series, y0, tol, scale=1.0):
    worst = 0.0
    for i, v in enumerate(page_series):
        y = y0 + i
        if v is None and y not in data_series:
            continue
        if v is None or y not in data_series:
            failures.append(f"{label} {y}: page {v}, data {data_series.get(y)}")
            return
        worst = max(worst, abs(v * scale - data_series[y]))
    if worst > tol:
        failures.append(f"{label}: max difference {worst:.4g} > {tol}")


U, G, VI, VR, SC, WD, WL, V = (const(n) for n in ("U", "G", "VI", "VR", "SC", "WD", "WL", "V"))
unfccc = table("unfccc_crt2025_sf6_t.csv", "iso3")
gains = table("gains_sf6_country_t.csv", "iso3")
inv = table("inversion_vojta_edgarrun_country_t.csv", "iso3", "field")
reg = table("regional_totals_t.csv", "region", "source")
emis = {k[0]: v for k, v in table("scenariomip_cmip7_sf6_emissions_t.csv", "scenario", "model").items()}
warm = table("warming_sf6_degC.csv", "scenario", "ecs_K")
vt = table("vojta2024_tables_A1_A4_t.csv", "region", "statistic")

if set(U) != set(unfccc): failures.append(f"UNFCCC parties differ: {set(U) ^ set(unfccc)}")
for iso, s in U.items(): compare(f"UNFCCC {iso}", s, unfccc.get(iso, {}), 1990, 0.006)
if set(G) != set(gains): failures.append(f"GAINS countries differ: {set(G) ^ set(gains)}")
for iso, s in G.items(): compare(f"GAINS {iso}", s, gains.get(iso, {}), 2005, 0.06)
for iso, s in VI.items(): compare(f"Inversion {iso}", s, inv.get((iso, "posterior"), {}), 2005, 0.06)
# The page's regional sums are whole tonnes built from country values rounded to 0.1 t, so allow 1 t.
for region, d in VR.items():
    compare(f"Region {region} inversion", d["m"], reg[(region, "Inversion (EDGAR-seeded run)")], 2005, 1.0)
    compare(f"Region {region} prior", d["p"], reg[(region, "Inversion starting guess (EDGAR v8)")], 2005, 1.0)
names = {"H": "High", "HL": "High-to-Low", "M": "Medium", "ML": "Medium-to-Low", "L": "Low", "LN": "Low-to-Negative", "VL": "Very Low", "Z": "Emissions stop in 2026"}
for s in SC: compare(f"Scenario emissions {s['n']}", s["v"], emis[s["n"]], 2023, 0.6)
for k, d in WD.items():
    for field, ecs in (("c", "3.0"), ("lo", "2.5"), ("hi", "4.0")):
        compare(f"Warming {names[k]} ECS {ecs}", d[field], warm[(names[k], ecs)], 1950, 6e-6, scale=1e-3)
for k, label in (("h", "High"), ("m", "Medium"), ("vl", "Very Low"), ("z", "Emissions stop in 2026")):
    compare(f"Long-run warming {label}", WL[k], warm[(label, "3.0")], 1950, 6e-6, scale=1e-3)
for key, region in (("WLD", "World"), ("CHN", "China"), ("USA", "United States"), ("EU", "European Union (27)")):
    for field, stat in (("m", "average"), ("lo", "minimum"), ("hi", "maximum")):
        compare(f"Vojta table {region} {stat}", V[key][field], vt[(region, stat)], 2005, 0.6)

if failures:
    print("\n".join(failures))
    sys.exit(f"{len(failures)} mismatch(es) between index.html and data/")
print("page data matches data/ (UNFCCC, GAINS, inversion, regions, scenarios, warming, Vojta tables)")
