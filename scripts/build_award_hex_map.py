"""Build the PMLA publisher-contact hex map from cited award and location tables.

Each publisher is placed at its documented contact locality's OpenStreetMap
centroid, not at an author's home or a precise street address. Empty mainland cells
form a neutral grid so the occupied cells can be seen in national context.
"""

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import build_geography as geo


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RADIUS_KM = 115
geo.HEX_RADIUS_KM = RADIUS_KM


def make_bins():
    locations = {row["publisher_key"]: row for row in csv.DictReader(
        (DATA / "publisher_contact_locations.csv").open())}
    books = list(csv.DictReader((DATA / "pmla_2024_2026.csv").open()))
    books += list(csv.DictReader((DATA / "pmla_2022_2023_geography.csv").open()))
    publishers = defaultdict(set)
    metros = defaultdict(set)
    listed = Counter()
    wins = Counter()
    for book in books:
        location = locations.get(book["publisher_key"])
        if location is None:
            continue
        cell = geo.hex_cell(float(location["longitude"]), float(location["latitude"]))
        publishers[cell].add(book["publisher_key"])
        metros[cell].add(location["map_city"])
        listed[cell] += 1
        wins[cell] += book["outcome"].strip().lower() == "winner"

    states = json.loads((DATA / "abs_states_2021.geojson").read_text())["features"]
    rings = [polygon[0] for state in states
             for polygon in state["geometry"]["coordinates"]]
    edge_cells = [geo.hex_cell(lon, lat) for ring in rings for lon, lat in ring]
    min_q, max_q = min(q for q, _ in edge_cells) - 2, max(q for q, _ in edge_cells) + 2
    min_r, max_r = min(r for _, r in edge_cells) - 2, max(r for _, r in edge_cells) + 2
    features = []
    for q in range(min_q, max_q + 1):
        for r in range(min_r, max_r + 1):
            cell = (q, r)
            cx, cy = geo.cell_centre(q, r)
            longitude, latitude = geo.unproject(cx, cy)
            if cell not in listed and not any(
                    geo.point_in_ring(longitude, latitude, ring) for ring in rings):
                continue
            vertices = []
            for i in range(6, -1, -1):
                angle = math.radians(i * 60)
                vertices.append([round(value, 5) for value in geo.unproject(
                    cx + RADIUS_KM * math.cos(angle),
                    cy + RADIUS_KM * math.sin(angle))])
            features.append({
                "type": "Feature",
                "properties": {
                    "hex_id": f"{q}:{r}",
                    "publishers": len(publishers[cell]),
                    "listed_books": listed[cell],
                    "winning_books": wins[cell],
                    "metro_areas": ", ".join(sorted(metros[cell])),
                    "centre_lon": round(longitude, 5),
                    "centre_lat": round(latitude, 5),
                },
                "geometry": {"type": "Polygon", "coordinates": [vertices]},
            })

    assert len(books) == 144 and len(locations) == 33
    assert sum(wins.values()) == sum(book["outcome"].strip().lower() == "winner" for book in books)
    assert len({name for group in publishers.values() for name in group}) == len(
        {book["publisher_key"] for book in books if book["publisher_key"] in locations})
    (DATA / "pmla_publisher_contact_hex_bins.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features},
                   separators=(",", ":")) + "\n")
    print(f"{len(features)} land cells; {len(listed)} occupied cells; "
          f"{sum(listed.values())} books from {len({name for group in publishers.values() for name in group})} publishers")
    print("Occupied:", sorted((", ".join(metros[cell]), len(publishers[cell]), listed[cell])
                              for cell in listed))


if __name__ == "__main__":
    make_bins()
