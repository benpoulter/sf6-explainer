"""Shared paths, constants, region definitions and the grid-to-country aggregation
used by the processing scripts. Raw inputs go in raw/ (not committed); outputs go in data/."""
from pathlib import Path
import json
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
DATA = ROOT / "data"
RAW.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

M_SF6 = 146.055            # g/mol
T_PER_PPT = 25853.0        # tonnes SF6 per ppt of global mean mole fraction (1.77e20 mol of dry air)
RE_SF6 = 0.567e-3          # W m-2 per ppt (IPCC AR6 Table 7.SM.7: 0.567 W m-2 ppb-1)

EU27 = "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE".split()
ANNEX_I = ("AUS AUT BLR BEL BGR CAN HRV CYP CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ITA JPN LVA LIE LTU "
           "LUX MLT MCO NLD NZL NOR POL PRT ROU RUS SVK SVN ESP SWE CHE TUR UKR GBR USA").split()

# Regions used in the "Africa, the Middle East, Latin America and Asia" section.
REGIONS = {
    "Africa": ("DZA AGO BEN BWA BFA BDI CPV CMR CAF TCD COM COG COD CIV DJI EGY GNQ ERI SWZ ETH GAB GMB GHA GIN "
               "GNB KEN LSO LBR LBY MDG MWI MLI MRT MUS MAR MOZ NAM NER NGA RWA STP SEN SYC SLE SOM ZAF SSD SDN "
               "TZA TGO TUN UGA ZMB ZWE ESH").split(),
    # Gulf states, Iran, Iraq, the Levant and Yemen; Turkey and Egypt excluded.
    "Middle East": "BHR IRN IRQ ISR JOR KWT LBN OMN PSE QAT SAU SYR ARE YEM".split(),
    # UN M49 Latin America and the Caribbean (French overseas departments are part of France here).
    "Latin America and the Caribbean": ("ATG ARG ABW BHS BRB BLZ BOL BRA VGB CYM CHL COL CRI CUB CUW DMA DOM ECU "
                                        "SLV FLK GUF GRD GLP GTM GUY HTI HND JAM MTQ MEX MSR NIC PAN PRY PER PRI "
                                        "BLM KNA LCA MAF VCT SXM SUR TTO TCA VIR URY VEN").split(),
    # UN M49 Central, Eastern, South-eastern and Southern Asia, with Iran counted in the Middle East.
    "Asia": ("KAZ KGZ TJK TKM UZB CHN HKG MAC MNG PRK KOR JPN TWN BRN KHM IDN LAO MYS MMR PHL SGP THA TLS VNM "
             "AFG BGD BTN IND MDV NPL PAK LKA").split(),
}


def fetch(url, dest):
    """Download url to raw/dest unless it is already there."""
    path = RAW / dest
    if not path.exists():
        print(f"downloading {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (sf6-explainer scripts)"})
        with urllib.request.urlopen(req) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def load_boundaries():
    """Simplified country polygons (Natural Earth via datasets/geo-countries) keyed by ISO3."""
    from shapely.geometry import shape
    gj = json.loads((DATA / "countries_simplified.geojson").read_text())
    ids = [f["properties"]["i"] for f in gj["features"]]
    geoms = [shape(f["geometry"]).buffer(0) for f in gj["features"]]
    return ids, geoms


def grid_to_country(field, lat, lon, max_dist=1.5):
    """Sum a gridded field (time, lat, lon) into countries.

    Each cell with a non-zero value in any year goes to the country polygon containing its centre,
    or, for coastal cells whose centre falls in the sea, to the nearest country within max_dist
    degrees. Returns {iso: array(time)} and the per-year total that could not be assigned."""
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    ids, geoms = load_boundaries()
    tree = STRtree(geoms)
    out, lost = {}, np.zeros(field.shape[0])
    for a, b in np.argwhere(np.abs(field).sum(0) > 0):
        p = Point(float(lon[b]), float(lat[a]))
        hits = tree.query(p, predicate="within")
        if len(hits):
            j = hits[0]
        else:
            j = tree.nearest(p)
            if geoms[j].distance(p) > max_dist:
                lost += field[:, a, b]
                continue
        out.setdefault(ids[j], np.zeros(field.shape[0]))
        out[ids[j]] += field[:, a, b]
    return out, lost


def write_wide(path, rows, years, index_names, digits=3):
    """Write {key tuple: values} as a wide CSV with one column per year."""
    import csv
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(list(index_names) + [str(y) for y in years])
        for key, vals in rows.items():
            key = key if isinstance(key, tuple) else (key,)
            w.writerow(list(key) + ["" if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), digits) for v in vals])
    print(f"wrote {path.relative_to(ROOT)} ({len(rows)} rows)")
