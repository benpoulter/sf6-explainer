#!/usr/bin/env bash
# Regenerate everything in data/ from the raw inputs (see README for what goes in raw/).
set -euo pipefail
cd "$(dirname "$0")"
for s in 00_extract_from_page.py 01_unfccc_crt2025.py 02_gains_grid_to_country.py \
         03_vojta_inversion_to_country.py 04_regions_and_tables.py 05_scenarios_concentration_warming.py \
         06_checks.py; do
  echo "== $s"; python3 "$s"
done
