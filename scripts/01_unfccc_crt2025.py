"""SF6 emissions reported to the UNFCCC in the 2025 national inventory submissions (CRT, 1990-2023).

Input: one folder per party under raw/unfccc-crt-2025/, each holding the party's CRT zip as downloaded
from https://unfccc.int/ghg-inventories-annex-i-parties/2025 (the page uses a mirror of the full set,
https://data.industrydecarbonization.com/unfccc/2025-unfccc-crt.tar.xz, after checking that its
document IDs match the latest versions on the UNFCCC site).

SF6 is read from the trend table (Table10s5, row "SF6", kt) in the workbook for the latest inventory year,
which lists every year from 1990. Canada and the EU nest their workbooks one zip deeper. The EU's own
trend table is blank in its 2025 file, so the EU is left out here; the page sums the 27 member states.
Notation keys (e.g. Belarus's "FX", omitted under the Paris flexibility provision) become blanks."""
import io
import re
import zipfile

from common import RAW, DATA, write_wide

YEARS = list(range(1990, 2024))
SRC = RAW / "unfccc-crt-2025"


def label(row):
    return next((str(c).strip() for c in row[:3] if c is not None and str(c).strip()), "")


def sf6_from_workbook(xbytes):
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(xbytes), read_only=True, data_only=True)["Table10s5"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = next(r for r in rows if label(r).startswith("GREENHOUSE"))
    cols = {int(str(c).strip()): i for i, c in enumerate(hdr) if c is not None and re.fullmatch(r"(19|20)\d\d", str(c).strip())}
    sf6 = next(r for r in rows if label(r) == "SF6")
    return {y: (sf6[i] * 1000 if isinstance(sf6[i], (int, float)) else None) for y, i in cols.items()}


def latest_year_workbook(names):
    """Pick the workbook for the latest inventory year from a list of file names."""
    def yr(n):
        m = [int(x) for x in re.findall(r"(?<!\d)(19\d\d|20[0-2]\d)(?!\d)", n.rsplit("/", 1)[-1]) if int(x) <= 2024]
        return max(m) if m else 0
    return max((n for n in names if n.lower().endswith(".xlsx")), key=yr)


def party_series(zpath):
    z = zipfile.ZipFile(zpath)
    xlsx = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
    if xlsx:
        return sf6_from_workbook(z.read(latest_year_workbook(xlsx)))
    inner = sorted(n for n in z.namelist() if n.lower().endswith(".zip"))
    pick = [n for n in inner if "2023" in n] or inner     # Canada: ..._2008_2023_...zip; EU: zipped/2023.zip
    z2 = zipfile.ZipFile(io.BytesIO(z.read(pick[-1])))
    return sf6_from_workbook(z2.read(latest_year_workbook(z2.namelist())))


rows = {}
for zpath in sorted(SRC.glob("*/*/*.zip")):
    iso = zpath.parts[-3]
    if iso == "EUA":
        continue
    s = party_series(zpath)
    vals = [s.get(y) for y in YEARS]
    if any(v is not None for v in vals):
        rows[iso] = vals
    else:
        print(f"{iso}: no numeric SF6 values (notation keys only)")
write_wide(DATA / "unfccc_crt2025_sf6_t.csv", rows, YEARS, ["iso3"])
