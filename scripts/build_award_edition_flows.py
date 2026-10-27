"""Build sourced international publishing flows for selected Australian prize books.

Published foreign editions and rights-sale territories are preserved as separate
evidence types in tooltips and visual encodings; rights sales are not presented as
proof that an edition was published.
"""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITIONS = ROOT / "data/award_winning_book_editions.csv"
RIGHTS = ROOT / "data/award_winning_book_rights_sales.csv"
OUTPUT = ROOT / "data/award_winning_book_edition_flows.geojson"
MARKET_OUTPUT = ROOT / "data/award_winning_book_edition_markets.csv"

# Representative market cities, not publisher addresses. Label offsets are
# in screen pixels so the dense European labels can be spaced around their dots.
MARKETS = {
    "United States": {"city": "New York", "xy": (-74.0060, 40.7128), "label": "United States", "label_offset": (-18, -18)},
    "Canada": {"city": "Toronto", "xy": (-79.3832, 43.6532), "label": "Canada", "label_offset": (-55, -22)},
    "United Kingdom": {"city": "London", "xy": (-0.1276, 51.5072), "label": "United Kingdom", "label_xy": (12, 62)},
    "France": {"city": "Paris", "xy": (2.3522, 48.8566), "label": "France", "label_xy": (12, 47)},
    "Italy": {"city": "Rome", "xy": (12.4964, 41.9028), "label": "Italy", "label_offset": (28, 30)},
    "Poland": {"city": "Warsaw", "xy": (21.0122, 52.2297), "label": "Poland", "label_xy": (35, 47)},
    "Germany": {"city": "Berlin", "xy": (13.4050, 52.5200), "label": "Germany", "label_xy": (25, 63)},
    "China": {"city": "Beijing", "xy": (116.4074, 39.9042), "label": "China", "label_offset": (22, -25)},
    "Netherlands": {"city": "Amsterdam", "xy": (4.9041, 52.3676), "label": "Netherlands", "label_offset": (-76, -46)},
    "Serbia": {"city": "Belgrade", "xy": (20.4489, 44.7866), "label": "Serbia", "label_xy": (38, 27)},
    "Sweden": {"city": "Stockholm", "xy": (18.0686, 59.3293), "label": "Sweden", "label_offset": (35, -35)},
    "North America": {"city": "North American market", "xy": (-100.0, 39.0), "label": "N. America", "label_offset": (-24, 18)},
    "Spain": {"city": "Madrid", "xy": (-3.7038, 40.4168), "label": "Spain", "label_offset": (-48, 14)},
    "Portugal": {"city": "Lisbon", "xy": (-9.1393, 38.7223), "label": "Portugal", "label_offset": (-54, 40)},
    "Taiwan": {"city": "Taipei", "xy": (121.5654, 25.0330), "label": "Taiwan", "label_offset": (28, -17)},
    "Egypt": {"city": "Cairo", "xy": (31.2357, 30.0444), "label": "Egypt", "label_offset": (27, 14)},
    "Turkey": {"city": "Ankara", "xy": (32.8597, 39.9334), "label": "Turkey", "label_offset": (48, 27)},
    "Denmark": {"city": "Copenhagen", "xy": (12.5683, 55.6761), "label": "Denmark", "label_offset": (35, -55)},
    "Hungary": {"city": "Budapest", "xy": (19.0402, 47.4979), "label": "Hungary", "label_offset": (65, 0)},
    "Slovenia": {"city": "Ljubljana", "xy": (14.5058, 46.0569), "label": "Slovenia", "label_offset": (-56, 39)},
    "Russia": {"city": "Moscow", "xy": (37.6173, 55.7558), "label": "Russia", "label_offset": (55, -42)},
    "Norway": {"city": "Oslo", "xy": (10.7522, 59.9139), "label": "Norway", "label_offset": (-48, -61)},
    "Romania": {"city": "Bucharest", "xy": (26.1025, 44.4268), "label": "Romania", "label_offset": (75, 33)},
}
ORIGIN = (133.7751, -25.2744)  # Australia country centroid, used as a national anchor


def great_circle(start, end, steps=64):
    lon1, lat1 = map(math.radians, start)
    lon2, lat2 = map(math.radians, end)
    dot = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    delta = math.acos(max(-1.0, min(1.0, dot)))
    if delta == 0:
        return [list(start), list(end)]
    points = []
    for i in range(steps + 1):
        fraction = i / steps
        a = math.sin((1 - fraction) * delta) / math.sin(delta)
        b = math.sin(fraction * delta) / math.sin(delta)
        x = a * math.cos(lat1) * math.cos(lon1) + b * math.cos(lat2) * math.cos(lon2)
        y = a * math.cos(lat1) * math.sin(lon1) + b * math.cos(lat2) * math.sin(lon2)
        z = a * math.sin(lat1) + b * math.sin(lat2)
        points.append([math.degrees(math.atan2(y, x)), math.degrees(math.atan2(z, math.hypot(x, y)))])
    return points


with EDITIONS.open(newline="", encoding="utf-8") as stream:
    editions = list(csv.DictReader(stream))
with RIGHTS.open(newline="", encoding="utf-8") as stream:
    rights_sales = list(csv.DictReader(stream))

markets = defaultdict(lambda: {"editions": [], "rights": []})
for row in editions:
    markets[row["edition_country"]]["editions"].append(row)
for row in rights_sales:
    markets[row["rights_market"]]["rights"].append(row)

# Focus the map on eight well-documented destination markets. The full source
# edition and rights tables remain available for auditing.
SELECTED_MARKETS = {"United States", "United Kingdom", "France", "Germany", "Poland", "China", "Taiwan", "Serbia"}
markets = {market: evidence for market, evidence in markets.items() if market in SELECTED_MARKETS}

features = []
for market, evidence in markets.items():
    location = MARKETS[market]
    edition_rows = evidence["editions"]
    rights_rows = evidence["rights"]
    edition_titles = sorted({row["book"] for row in edition_rows})
    rights_titles = sorted({row["book"] for row in rights_rows})
    all_titles = sorted(set(edition_titles) | set(rights_titles))
    evidence_type = "both" if edition_rows and rights_rows else "edition" if edition_rows else "rights"
    edition_details = [
        f'{row["book"]} ({row["edition_year"] or "year not stated"}; {row["publisher"]})'
        for row in edition_rows
    ]
    rights_details = [f'{row["book"]} — rights sold to {row["rights_publisher"]}' for row in rights_rows]
    properties = {
        "destination_market": market,
        "destination_city": location["city"],
        "title_count": len(all_titles),
        "edition_title_count": len(edition_titles),
        "rights_title_count": len(rights_titles),
        "evidence_type": evidence_type,
        "books": "; ".join(all_titles),
        "edition_books": "; ".join(edition_titles),
        "rights_books": "; ".join(rights_titles),
        "edition_details": "; ".join(edition_details) or "No published-edition record in this dataset",
        "rights_details": "; ".join(rights_details) or "No rights-sale record in this dataset",
        "awards": "; ".join(sorted({row["award"] for row in edition_rows + rights_rows})),
        "edition_sources": "; ".join(sorted({row["edition_source"] for row in edition_rows})),
        "rights_sources": "; ".join(sorted({row["rights_source"] for row in rights_rows})),
    }
    features.append({
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "LineString", "coordinates": great_circle(ORIGIN, location["xy"])},
    })

feature_collection = {
    "type": "FeatureCollection",
    "name": "award_winning_book_international_publishing_flows",
    "metadata": {
        "origin": "Australia country centroid used as a national anchor, not a publisher address",
        "destination": "Representative market-city coordinates, not specific publisher addresses",
        "measure": "Unique selected award-winning titles with either a documented foreign edition or a documented sale of publishing rights in each market",
        "edition_titles": "Carpentaria (2007 Miles Franklin winner); The Yield (2020 Miles Franklin winner); Cold Enough for Snow (winner of The Novel Prize and other Australian literary prizes)",
        "rights_title": "No Friend But the Mountains (2019 Victorian Premier's Prize for Literature winner); 19 publishing-rights territories listed by its rights agent",
        "limitation": "Rights sold are not evidence that a translation or edition was subsequently published. This curated sample is not a complete translation or rights census.",
    },
    "features": features,
}
OUTPUT.write_text(json.dumps(feature_collection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

with MARKET_OUTPUT.open("w", newline="", encoding="utf-8") as stream:
    columns = ["place", "longitude", "latitude", "label", "label_longitude", "label_latitude", "title_count", "evidence_type", "kind"]
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    edition_titles = {row["book"] for row in editions}
    rights_titles = {row["book"] for row in rights_sales}
    writer.writerow({"place": "Australia", "longitude": ORIGIN[0], "latitude": ORIGIN[1], "label": "Australia", "label_longitude": ORIGIN[0], "label_latitude": ORIGIN[1], "title_count": len(edition_titles | rights_titles), "evidence_type": "origin", "kind": "origin"})
    for market, evidence in markets.items():
        location = MARKETS[market]
        title_count = len({row["book"] for row in evidence["editions"] + evidence["rights"]})
        evidence_type = "both" if evidence["editions"] and evidence["rights"] else "edition" if evidence["editions"] else "rights"
        # Geographic projection marks cannot use data-driven pixel offsets.
        # Approximate the intended screen offsets as lon/lat displacement.
        if "label_xy" in location:
            label_lon, label_lat = location["label_xy"]
        else:
            dx, dy = location["label_offset"]
            label_lon = location["xy"][0] + dx / 2.8
            label_lat = location["xy"][1] - dy / 2.8
        writer.writerow({"place": market, "longitude": location["xy"][0], "latitude": location["xy"][1], "label": location["label"], "label_longitude": round(label_lon, 4), "label_latitude": round(label_lat, 4), "title_count": title_count, "evidence_type": evidence_type, "kind": "market"})
