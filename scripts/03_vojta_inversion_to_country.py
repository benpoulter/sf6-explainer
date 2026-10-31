"""Atmospheric inversion of SF6 emissions by country, 2005-2021, summed from Vojta et al.'s 1 degree grid.

Source: Vojta (2025), Annual global SF6 emissions quantified by inverse modeling using FLEXPART and
FLEXINVERT, Zenodo, doi:10.5281/zenodo.18033046. The file holds a single inversion run, the one seeded
with EDGAR v8 (prior and posterior fluxes in mol m-2 s-1). Vojta et al. (2024, ACP 24, 12465) report three
runs; their appendix tables (data/vojta2024_tables_A1_A4.csv) give the three-run averages used on the page
for the world, China, the US and the EU-27.

Per-cell standard deviations are in the file but are not summed here: without the error covariance,
adding them gives ranges about a third as wide as the paper's."""
import calendar

import netCDF4
import numpy as np

from common import DATA, M_SF6, fetch, grid_to_country, write_wide

URL = ("https://zenodo.org/records/18033046/files/"
       "SF6_FLUX_ALL_GBL_INV_YEAR_20050101_20211231_FLEXINVERT_UNIVIE_V01.nc?download=1")
nc = netCDF4.Dataset(fetch(URL, "SF6_FLUX_ALL_GBL_INV_YEAR_20050101_20211231_FLEXINVERT_UNIVIE_V01.nc"))
lat, lon = np.asarray(nc["latitude"][:]), np.asarray(nc["longitude"][:])
bounds = netCDF4.num2date(nc["time_bnds"][:], nc["time_bnds"].units)
years = [b[0].year for b in bounds]

R = 6371008.8
area = (R**2 * np.radians(1.0) * (np.sin(np.radians(lat + 0.5)) - np.sin(np.radians(lat - 0.5))))[:, None] * np.ones((1, len(lon)))


def tonnes(var):
    """mol m-2 s-1 -> tonnes per cell per year."""
    out = []
    for i, y in enumerate(years):
        sec = (366 if calendar.isleap(y) else 365) * 86400
        out.append(np.asarray(np.ma.filled(nc[var][i], 0.0)) * area * sec * M_SF6 / 1e6)
    return np.stack(out)


post, prior = tonnes("flux_total_posterior"), tonnes("flux_total_prior")
print("global posterior, first/last year (t):", round(post[0].sum()), round(post[-1].sum()),
      "(paper, EDGAR-seeded run: 5,590 and 9,500)")
rows = {}
for kind, field in (("posterior", post), ("prior_edgar_v8", prior)):
    by_country, _ = grid_to_country(field, lat, lon)
    for iso, v in by_country.items():
        if v.max() >= 0.05:
            rows[(iso, kind)] = v
write_wide(DATA / "inversion_vojta_edgarrun_country_t.csv", dict(sorted(rows.items())), years, ["iso3", "field"])
