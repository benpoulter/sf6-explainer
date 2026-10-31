"""Extract the EDGAR country/sector series and the country boundaries embedded in index.html.

The EDGAR data (EDGAR_2026_GHG F-gases, JRC, converted from Gg to tonnes) and the simplified
boundaries were prepared before this repository existed, so they are taken from the page itself."""
import json

from common import ROOT, DATA, write_wide

SECTORS = {"2.G": "Electrical equipment & other product use", "2.C": "Metal industry",
           "2.E": "Electronics industry", "2.B": "Chemical industry (production)"}

html = (ROOT / "index.html").read_text()
line = next(l for l in html.split("\n") if l.startswith("const W="))
dec = json.JSONDecoder()
W, end = dec.raw_decode(line, len("const W="))
D, _ = dec.raw_decode(line, line.index("D=", end) + 2)

(DATA / "countries_simplified.geojson").write_text(json.dumps(W, separators=(",", ":")))
print(f"wrote data/countries_simplified.geojson ({len(W['features'])} features)")

years = D["years"]
rows = {(iso, D["names"].get(iso, iso), "Total"): D["data"][iso] for iso in sorted(D["data"])}
for iso in sorted(D["sec"]):
    for code, vals in D["sec"][iso].items():
        rows[(iso, D["names"].get(iso, iso), f"{code} {SECTORS.get(code, code)}")] = vals
write_wide(DATA / "edgar_sf6_country_sector_t.csv", dict(sorted(rows.items())), years, ["iso3", "name", "sector"])
