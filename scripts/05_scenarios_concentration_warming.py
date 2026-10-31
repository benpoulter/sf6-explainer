"""ScenarioMIP-CMIP7 SF6 emissions, NOAA concentrations, one-box scenario concentrations, and warming.

Inputs (downloaded to raw/ if missing):
  - ScenarioMIP-CMIP7 marker scenarios v0.2, doi:10.5281/zenodo.19825038 (harmonized and infilled emissions)
  - NOAA GML global monthly mean SF6, https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_mm_gl.txt
  - CMIP7 historical SF6 concentrations (CR-CMIP-1-0-0), doi:10.5281/zenodo.14892947,
    file output-bundles/v1.0.0/data/interim/sf6/sf6_global-mean_annual-mean.nc from data--interim.tar.gz
  - CMIP7 ScenarioMIP SF6 concentrations, doi:10.5281/zenodo.19243739,
    file data/interim/annual-means/one-box_sf6_annual-mean.feather from data--interim--annual-means.tar.gz

Warming uses the IPCC AR6 two-layer emulator (Chapter 7 SM 7.SM.5.2: C=7.7, C0=147 W yr m-2 K-1,
lambda=1.31 W m-2 K-1, efficacy 1.03, kappa=0.88 W m-2 K-1; ECS 3.0 K, TCR 1.8 K with F2x=3.93 W m-2),
driven by SF6 forcing = 0.567 W m-2 ppb-1 x concentration. The 'likely' range scales lambda for ECS 2.5-4 K.
'Stop 2026': concentrations follow history and the scenarios to 2025, then decay with a 1,278-year lifetime."""
import netCDF4
import numpy as np
import pandas as pd

from common import DATA, RAW, RE_SF6, T_PER_PPT, fetch, write_wide

SCEN = {"High": "h", "High-to-Low": "hl", "Medium": "m", "Medium-to-Low": "ml", "Low": "l", "Low-to-Negative": "ln", "Very Low": "vl"}

# --- ScenarioMIP emissions (kt -> t), 2023-2100
xlsx = fetch("https://zenodo.org/records/19825038/files/ScenarioMIP_emissions_marker_scenarios_v0.2.xlsx?download=1",
             "ScenarioMIP_emissions_marker_scenarios_v0.2.xlsx")
df = pd.read_excel(xlsx, sheet_name="data")
df = df[df["variable"] == "Climate Assessment|Harmonized and Infilled|Emissions|SF6"]
df.columns = [int(c) if str(c).strip().isdigit() else c for c in df.columns]
yrs = list(range(2023, 2101))
emis = {}
for _, r in df.iterrows():
    name = r["scenario"].split(" - ")[0]
    emis[(name, r["model"])] = [r[y] * 1000 for y in yrs]
write_wide(DATA / "scenariomip_cmip7_sf6_emissions_t.csv", emis, yrs, ["scenario", "model"])

# --- NOAA monthly global mean
noaa_path = fetch("https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_mm_gl.txt", "sf6_mm_gl.txt")
noaa = pd.read_csv(noaa_path, comment="#", sep=r"\s+", header=None, usecols=[0, 1, 3], names=["year", "month", "sf6_ppt"])
noaa.to_csv(DATA / "noaa_sf6_global_monthly_ppt.csv", index=False)
print(f"wrote data/noaa_sf6_global_monthly_ppt.csv ({len(noaa)} rows)")
c2023 = noaa[noaa.year == 2023].sf6_ppt.mean()

# --- One-box concentrations from scenario emissions (the page's section 07 and top-right chart)
rows = {}
for (name, model), e in emis.items():
    for tau in (850, 1278, 3200):
        f, c = np.exp(-1 / tau), [c2023]
        for v in e[:-1]:
            c.append(c[-1] * f + v / T_PER_PPT * tau * (1 - f))
        rows[(name, tau)] = c
write_wide(DATA / "onebox_scenario_concentration_ppt.csv", rows, yrs, ["scenario", "lifetime_years"])

# --- CMIP7 concentrations: historical to 2021, scenarios from 2022 (to 2500)
hist_nc = RAW / "cmip7_historical_sf6_global-mean_annual-mean.nc"
scen_fe = RAW / "cmip7_scenarios_sf6_annual-mean.feather"
for p in (hist_nc, scen_fe):
    if not p.exists():
        raise SystemExit(f"missing {p}: extract it from the CMIP7 archive named in this script's docstring")
h = netCDF4.Dataset(hist_nc)
hist = dict(zip(np.asarray(h["year"][:]).astype(int), np.asarray(h["sf6"][:])))
sc = pd.read_feather(scen_fe)
scen = {s[1]: {int(y): float(sc.loc[s][y]) for y in sc.columns} for s in sc.index}
Y = list(range(1950, 2301))
conc = {name: np.array([hist[y] if y < 2022 else scen[k][y] for y in Y]) for name, k in SCEN.items()}
stop = [hist[y] if y < 2022 else scen["m"][y] for y in range(1950, 2026)]
while len(stop) < len(Y):
    stop.append(stop[-1] * np.exp(-1 / 1278))
conc["Emissions stop in 2026"] = np.array(stop)
write_wide(DATA / "cmip7_sf6_concentration_ppt.csv", conc, Y, ["scenario"])


def two_layer(F, ecs=3.0, dt=0.05):
    C, C0, eps, kap, lam = 7.7, 147.0, 1.03, 0.88, 3.93 / ecs
    T = T0 = 0.0
    out = []
    for f in F:
        for _ in range(int(round(1 / dt))):
            T, T0 = T + dt * (f - lam * T - eps * kap * (T - T0)) / C, T0 + dt * kap * (T - T0) / C0
        out.append(T)
    return np.array(out)


rows = {(name, ecs): two_layer(RE_SF6 * c, ecs) for name, c in conc.items() for ecs in (2.5, 3.0, 4.0)}
write_wide(DATA / "warming_sf6_degC.csv", rows, Y, ["scenario", "ecs_K"], digits=6)
F = np.linspace(3.93 / 70, 3.93, 70)
print("check: transient response to 1%/yr CO2 at doubling =", round(two_layer(F)[-1], 2), "K (AR6: 1.8)")
