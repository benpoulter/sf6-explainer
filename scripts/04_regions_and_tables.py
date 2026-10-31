"""Regional totals (EDGAR, GAINS, inversion), region definitions, and the Vojta et al. (2024) appendix tables.

Needs the outputs of scripts 00, 02 and 03. The appendix tables are transcribed from Vojta et al. (2024),
Atmospheric Chemistry and Physics 24, 12465-12493, tables A1-A4: the average of three inversion runs
(seeded with country reports, EDGAR and GAINS) and the minimum and maximum uncertainty limits, in tonnes."""
import csv

from common import DATA, EU27, REGIONS, write_wide


def read(path, key):
    rows = {}
    for r in csv.DictReader(open(DATA / path)):
        k = tuple(r[c] for c in key)
        rows[k] = {int(y): float(v) for y, v in r.items() if y.isdigit() and v != ""}
    return rows


edgar = {k[0]: v for k, v in read("edgar_sf6_country_sector_t.csv", ["iso3", "sector"]).items() if k[1] == "Total"}
gains = {k[0]: v for k, v in read("gains_sf6_country_t.csv", ["iso3"]).items()}
inv = read("inversion_vojta_edgarrun_country_t.csv", ["iso3", "field"])
post = {k[0]: v for k, v in inv.items() if k[1] == "posterior"}
prior = {k[0]: v for k, v in inv.items() if k[1] == "prior_edgar_v8"}

groups = dict(REGIONS)
groups["Asia, excluding China"] = [c for c in REGIONS["Asia"] if c != "CHN"]
groups["European Union (27)"] = EU27
sources = (("EDGAR", edgar, range(1990, 2026)), ("GAINS", gains, range(2005, 2021)),
           ("Inversion (EDGAR-seeded run)", post, range(2005, 2022)), ("Inversion starting guess (EDGAR v8)", prior, range(2005, 2022)))
rows = {}
for name, isos in groups.items():
    for src, data, yrs in sources:
        rows[(name, src)] = [sum(data[c][y] for c in isos if c in data and y in data[c]) if y in yrs else None for y in range(1990, 2026)]
write_wide(DATA / "regional_totals_t.csv", rows, range(1990, 2026), ["region", "source"])

with open(DATA / "region_definitions.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["region", "iso3"])
    for name, isos in groups.items():
        for c in isos:
            w.writerow([name, c])
print("wrote data/region_definitions.csv")

T = {  # Gg (kt): average, minimum, maximum for 2005..2021
    "World": ([5.51, 5.29, 6.72, 8.02, 7.78, 8.37, 7.90, 8.63, 9.18, 10.26, 9.70, 7.80, 8.72, 9.89, 8.06, 8.44, 9.67],
              [4.38, 4.32, 5.12, 6.32, 6.29, 6.47, 5.95, 6.45, 7.35, 8.23, 7.78, 6.20, 6.80, 7.59, 6.30, 6.45, 7.50],
              [6.74, 6.25, 8.53, 9.84, 9.19, 10.24, 9.74, 10.87, 11.06, 12.31, 11.67, 9.10, 10.52, 11.87, 9.52, 10.22, 11.53]),
    "China": ([1.56, 1.33, 2.52, 3.01, 3.42, 3.41, 3.22, 3.73, 4.59, 5.31, 5.03, 3.85, 4.49, 5.18, 4.28, 4.71, 5.58],
              [1.03, .92, 2.08, 2.55, 2.98, 2.91, 2.69, 3.20, 3.89, 4.63, 4.26, 3.26, 3.80, 4.40, 3.68, 4.03, 4.75],
              [2.27, 1.97, 3.22, 3.84, 4.23, 4.43, 4.26, 4.79, 5.99, 6.70, 6.58, 5.05, 5.87, 6.74, 5.56, 6.10, 7.31]),
    "United States": ([1.25, 1.38, 1.19, 1.28, 1.03, .93, .81, .70, .64, .53, .55, .77, .63, .61, .58, .49, .48],
                      [1.06, 1.20, 1.00, 1.06, .90, .77, .66, .55, .48, .42, .42, .60, .49, .46, .44, .36, .36],
                      [1.58, 1.70, 1.49, 1.61, 1.25, 1.22, 1.10, 1.00, .93, .72, .76, 1.05, .88, .89, .84, .73, .71]),
    "European Union (27)": ([.41, .38, .35, .36, .36, .39, .34, .38, .30, .34, .31, .36, .38, .26, .28, .33, .25],
                            [.35, .33, .31, .32, .31, .34, .27, .35, .26, .30, .28, .32, .34, .22, .25, .29, .22],
                            [.46, .42, .39, .40, .41, .43, .39, .43, .34, .38, .34, .39, .42, .30, .32, .36, .29]),
}
rows = {(r, s): [x * 1000 for x in v] for r, vals in T.items() for s, v in zip(("average", "minimum", "maximum"), vals)}
write_wide(DATA / "vojta2024_tables_A1_A4_t.csv", rows, range(2005, 2022), ["region", "statistic"])
