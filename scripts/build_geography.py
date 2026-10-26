"""Rebuild publisher-location summaries and simplified ABS boundaries.

Download the ABS GDA2020 2021 States and Territories shapefile ZIP from
https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files
and pass its path as the first argument. Uses only Python's standard library.
"""

import csv
import json
import math
import struct
import sys
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATE_NAMES = {
    "NSW": "New South Wales", "VIC": "Victoria", "QLD": "Queensland",
    "SA": "South Australia", "WA": "Western Australia", "TAS": "Tasmania",
    "NT": "Northern Territory", "ACT": "Australian Capital Territory",
}
EARTH_RADIUS_KM = 6371.0088
CENTRE_LON, CENTRE_LAT = math.radians(134), math.radians(-25)
HEX_RADIUS_KM = 170


def read_dbf(data):
    count = struct.unpack_from("<I", data, 4)[0]
    header_len, record_len = struct.unpack_from("<HH", data, 8)
    fields = []
    offset = 1
    for pos in range(32, header_len - 1, 32):
        field = data[pos:pos + 32]
        if field[0] == 13:
            break
        name = field[:11].split(b"\0")[0].decode("ascii")
        width = field[16]
        fields.append((name, offset, width))
        offset += width
    for index in range(count):
        record = data[header_len + index * record_len:header_len + (index + 1) * record_len]
        yield {name: record[start:start + width].decode("latin1").strip()
               for name, start, width in fields}


def area(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2)
                   in zip(ring, ring[1:]))) / 2


def signed_area(ring):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2)
               in zip(ring, ring[1:])) / 2


def simplify(points, tolerance=0.035):
    """Douglas-Peucker on one closed source ring; preserve its source vertices."""
    points = points[:-1] if points[0] == points[-1] else points
    if len(points) < 4:
        return points + [points[0]]
    # Start at a farthest vertex so a ring does not collapse at its closure.
    anchor = points[0]
    farthest = max(range(1, len(points)), key=lambda i:
                   (points[i][0] - anchor[0]) ** 2 + (points[i][1] - anchor[1]) ** 2)
    rotated = points[farthest:] + points[:farthest] + [points[farthest]]
    keep = {0, len(rotated) - 1}
    stack = [(0, len(rotated) - 1)]
    while stack:
        start, end = stack.pop()
        x1, y1 = rotated[start]
        x2, y2 = rotated[end]
        dx, dy = x2 - x1, y2 - y1
        length = dx * dx + dy * dy
        best, distance = -1, tolerance * tolerance
        for i in range(start + 1, end):
            x, y = rotated[i]
            fraction = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / length)) if length else 0
            squared = (x - x1 - fraction * dx) ** 2 + (y - y1 - fraction * dy) ** 2
            if squared > distance:
                best, distance = i, squared
        if best != -1:
            keep.add(best)
            stack.extend([(start, best), (best, end)])
    result = [rotated[i] for i in sorted(keep)]
    return result if len(result) >= 4 else rotated


def boundaries(zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        shp = archive.read("STE_2021_AUST_GDA2020.shp")
        rows = list(read_dbf(archive.read("STE_2021_AUST_GDA2020.dbf")))
    features = []
    pos = 100
    for row in rows:
        _, words = struct.unpack_from(">II", shp, pos)
        end = pos + 8 + words * 2
        body = pos + 8
        if row["STE_NAME21"] not in STATE_NAMES.values():
            pos = end
            continue
        assert struct.unpack_from("<I", shp, body)[0] == 5
        parts_n, points_n = struct.unpack_from("<II", shp, body + 36)
        parts = list(struct.unpack_from(f"<{parts_n}I", shp, body + 44))
        points_start = body + 44 + 4 * parts_n
        points = [struct.unpack_from("<dd", shp, points_start + 16 * i)
                  for i in range(points_n)]
        polygons = []
        for start, stop in zip(parts, parts[1:] + [points_n]):
            ring = list(points[start:stop])
            # ESRI exterior rings are clockwise. Vega's spherical geoshape
            # renderer uses this winding for the smaller enclosed region.
            # Interior rings have the opposite winding and must not be emitted
            # as independent polygons, which would fill the outside world.
            if signed_area(ring) >= 0:
                continue
            if area(ring) < 0.01 and row["STE_NAME21"] != "Australian Capital Territory":
                continue
            reduced = simplify(ring)
            if len(reduced) >= 4:
                polygons.append([[[round(x, 5), round(y, 5)] for x, y in reduced]])
        features.append({"type": "Feature",
                         "properties": {"state": row["STE_NAME21"], "state_code": row["STE_CODE21"]},
                         "geometry": {"type": "MultiPolygon", "coordinates": polygons}})
        pos = end
    assert len(features) == 8
    (DATA / "abs_states_2021.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")) + "\n")


def project(lon, lat):
    lam, phi = math.radians(lon), math.radians(lat)
    delta = lam - CENTRE_LON
    k = math.sqrt(2 / (1 + math.sin(CENTRE_LAT) * math.sin(phi)
                       + math.cos(CENTRE_LAT) * math.cos(phi) * math.cos(delta)))
    return (EARTH_RADIUS_KM * k * math.cos(phi) * math.sin(delta),
            EARTH_RADIUS_KM * k * (math.cos(CENTRE_LAT) * math.sin(phi)
                                - math.sin(CENTRE_LAT) * math.cos(phi) * math.cos(delta)))


def unproject(x, y):
    rho = math.hypot(x, y)
    if rho == 0:
        return math.degrees(CENTRE_LON), math.degrees(CENTRE_LAT)
    c = 2 * math.asin(min(1, rho / (2 * EARTH_RADIUS_KM)))
    phi = math.asin(math.cos(c) * math.sin(CENTRE_LAT)
                    + y * math.sin(c) * math.cos(CENTRE_LAT) / rho)
    lam = CENTRE_LON + math.atan2(x * math.sin(c),
                                   rho * math.cos(CENTRE_LAT) * math.cos(c)
                                   - y * math.sin(CENTRE_LAT) * math.sin(c))
    return math.degrees(lam), math.degrees(phi)


def hex_cell(lon, lat):
    x, y = project(lon, lat)
    q = (2 / 3 * x) / HEX_RADIUS_KM
    r = (-x / 3 + math.sqrt(3) * y / 3) / HEX_RADIUS_KM
    cube = [q, -q - r, r]
    rounded = [round(value) for value in cube]
    delta = [abs(a - b) for a, b in zip(cube, rounded)]
    rounded[delta.index(max(delta))] = -sum(rounded[i] for i in range(3)
                                             if i != delta.index(max(delta)))
    return rounded[0], rounded[2]


def cell_centre(q, r):
    return (HEX_RADIUS_KM * 1.5 * q,
            HEX_RADIUS_KM * math.sqrt(3) * (r + q / 2))


def point_in_ring(lon, lat, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def counts():
    locations = {row["publisher_key"]: row for row in csv.DictReader(
        (DATA / "publisher_contact_locations.csv").open())}
    listed, wins, city_listed, city_wins = Counter(), Counter(), Counter(), Counter()
    city_publishers = {}
    books = list(csv.DictReader((DATA / "pmla_2024_2026.csv").open()))
    for row in books:
        location = locations.get(row["publisher_key"])
        if not location:
            continue
        state = location["state"]
        city = location["map_city"]
        listed[state] += 1
        wins[state] += row["outcome"].strip().lower() == "winner"
        city_listed[city] += 1
        city_wins[city] += row["outcome"].strip().lower() == "winner"
        city_publishers.setdefault(city, set()).add(row["publisher_key"])
    assert len(books) == 90 and len(locations) == 26
    assert sum(listed.values()) == 86
    assert sum(wins.values()) == sum(row["outcome"].strip().lower() == "winner" for row in books)
    with (DATA / "publisher_contact_state_summary.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["state", "state_name", "listed_books", "winning_books", "winner_share_pct"])
        for state, name in STATE_NAMES.items():
            n = listed[state]
            writer.writerow([state, name, n, wins[state], round(100 * wins[state] / n, 1) if n else ""])
    with (DATA / "publisher_contact_city_summary.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["map_city", "state", "longitude", "latitude", "listed_books", "winning_books", "publishers", "publisher_names"])
        for city, n in city_listed.most_common():
            location = next(item for item in locations.values() if item["map_city"] == city)
            names = sorted(city_publishers[city])
            writer.writerow([city, location["state"], location["longitude"], location["latitude"], n, city_wins[city], len(names), "; ".join(names)])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/build_geography.py ABS_STE_2021.zip | --counts-only")
    if sys.argv[1] != "--counts-only":
        boundaries(Path(sys.argv[1]))
    counts()
