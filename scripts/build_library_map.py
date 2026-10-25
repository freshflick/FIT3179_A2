"""Prepare the historical RMIT public-library locations and equal-area hex bins.

Source: Carl Higgs, Australian public lending library locations (2016–2018),
RMIT Research Repository, https://doi.org/10.25439/rmt.21944840.v1.
Download its CSV and pass it as the first argument. The included prepared CSV
can also be used to rebuild only the hex map: --bins-only.
"""

import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

import build_geography as geo


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RADIUS_KM = 115
geo.HEX_RADIUS_KM = RADIUS_KM


def prepare(source):
    rows = []
    with source.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            lat, lon = float(row["latitude"]), float(row["longitude"])
            # The three external-island records lie outside the ABS mainland
            # and Tasmania boundary used on this dashboard.
            if not (110 < lon < 155 and -45 < lat < -9):
                continue
            rows.append({
                "library": row["Library"].strip(),
                "state": row["State"],
                "year": row["year"],
                "latitude": lat,
                "longitude": lon,
                "source_publisher": row["source_publisher"],
            })
    assert len(rows) == 1440
    with (DATA / "public_libraries_2016_2018.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_bins():
    rows = list(csv.DictReader((DATA / "public_libraries_2016_2018.csv").open()))
    bins = Counter(geo.hex_cell(float(row["longitude"]), float(row["latitude"])) for row in rows)
    states = json.loads((DATA / "abs_states_2021.geojson").read_text())["features"]
    rings = [poly[0] for state in states for poly in state["geometry"]["coordinates"]]
    features = []
    for (q, r), count in sorted(bins.items()):
        cx, cy = geo.cell_centre(q, r)
        centre_lon, centre_lat = geo.unproject(cx, cy)
        vertices = []
        for i in range(6, -1, -1):
            angle = math.radians(i * 60)
            vertices.append([round(n, 5) for n in geo.unproject(
                cx + RADIUS_KM * math.cos(angle), cy + RADIUS_KM * math.sin(angle))])
        features.append({
            "type": "Feature",
            "properties": {
                "hex_id": f"{q}:{r}", "libraries": count,
                "centre_lon": round(centre_lon, 5),
                "centre_lat": round(centre_lat, 5),
            },
            "geometry": {"type": "Polygon", "coordinates": [vertices]},
        })
    assert sum(f["properties"]["libraries"] for f in features) == 1440
    (DATA / "public_library_hex_bins_2018.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")) + "\n")
    print(f"{len(rows)} library coordinates in {len(features)} occupied hexagons; largest bin has {max(bins.values())}")
    print("State totals:", dict(Counter(row["state"] for row in rows)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/build_library_map.py RMIT_CSV | --bins-only")
    if sys.argv[1] != "--bins-only":
        prepare(Path(sys.argv[1]))
    make_bins()
