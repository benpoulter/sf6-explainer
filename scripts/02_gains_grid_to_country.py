"""GAINS SF6 emissions by country, 2005-2020, summed from IIASA's 0.5 degree global grid.

Source: Purohit and Lindl (2024), Gridded Global Emissions of SF6, IIASA, Zenodo,
doi:10.5281/zenodo.12708771 (kt per cell per year; all SF6 is on one 'A_PublicPower' layer)."""
import netCDF4
import numpy as np

from common import DATA, fetch, grid_to_country, write_wide

URL = "https://zenodo.org/records/12708771/files/MOD_SF6_FLUX_GAINS_IIASA_ALL_GBL_YEAR_V1_20231031.nc?download=1"
nc = netCDF4.Dataset(fetch(URL, "MOD_SF6_FLUX_GAINS_IIASA_ALL_GBL_YEAR_V1_20231031.nc"))
years = [int(y) for y in nc["year"][:]]
field = np.nan_to_num(np.ma.filled(nc["A_PublicPower"][:], 0.0)) * 1000.0   # kt -> t
by_country, lost = grid_to_country(field, nc["lat"][:], nc["lon"][:])
print("global total, first/last year (t):", round(field[0].sum()), round(field[-1].sum()), "| unassigned:", round(lost.max(), 3))
rows = {iso: v for iso, v in sorted(by_country.items()) if v.max() >= 0.05}
write_wide(DATA / "gains_sf6_country_t.csv", rows, years, ["iso3"])
