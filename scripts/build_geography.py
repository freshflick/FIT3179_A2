"""Rebuild the two map tables and simplified ABS state boundaries.

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


def hex_bins(city_year):
    states = json.loads((DATA / "abs_states_2021.geojson").read_text())["features"]
    rings = [polygon[0] for state in states for polygon in state["geometry"]["coordinates"]]
    projected = [project(lon, lat) for ring in rings for lon, lat in ring]
    xs, ys = [p[0] for p in projected], [p[1] for p in projected]
    occupied = {}
    for (lon, lat, city, year), count in city_year.items():
        q, r = hex_cell(lon, lat)
        entry = occupied.setdefault((q, r), {"cities": set(), "counts": Counter()})
        entry["cities"].add(city)
        entry["counts"][year] += count
    features = []
    q_min, q_max = math.floor(min(xs) / (1.5 * HEX_RADIUS_KM)) - 1, math.ceil(max(xs) / (1.5 * HEX_RADIUS_KM)) + 1
    r_min, r_max = -25, 25
    for q in range(q_min, q_max + 1):
        for r in range(r_min, r_max + 1):
            cx, cy = cell_centre(q, r)
            if not (min(ys) - HEX_RADIUS_KM <= cy <= max(ys) + HEX_RADIUS_KM):
                continue
            lon, lat = unproject(cx, cy)
            is_land = any(point_in_ring(lon, lat, ring) for ring in rings)
            if not is_land and (q, r) not in occupied:
                continue
            entry = occupied.get((q, r), {"cities": set(), "counts": Counter()})
            vertices = []
            for i in range(6, -1, -1):
                angle = math.radians(i * 60)
                vx = cx + HEX_RADIUS_KM * math.cos(angle)
                vy = cy + HEX_RADIUS_KM * math.sin(angle)
                vertices.append([round(value, 5) for value in unproject(vx, vy)])
            counts = entry["counts"]
            features.append({
                "type": "Feature",
                "properties": {
                    "hex_id": f"{q}:{r}", "office_metros": ", ".join(sorted(entry["cities"])),
                    "centre_lon": round(lon, 5), "centre_lat": round(lat, 5),
                    "y2024": counts["2024"], "y2025": counts["2025"], "y2026": counts["2026"]
                },
                "geometry": {"type": "Polygon", "coordinates": [vertices]}
            })
    assert sum(f["properties"]["y2024"] + f["properties"]["y2025"]
               + f["properties"]["y2026"] for f in features) == 65
    (DATA / "publisher_office_hex_year.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")) + "\n")


def counts():
    offices = {row["publisher_key"]: row for row in csv.DictReader(
        (DATA / "publisher_office_locations_top10.csv").open())}
    listed, wins, by_year, city_year = Counter(), Counter(), Counter(), Counter()
    for row in csv.DictReader((DATA / "pmla_2024_2026.csv").open()):
        office = offices.get(row["publisher_key"])
        if not office:
            continue
        state = office["state"]
        listed[state] += 1
        wins[state] += row["outcome"].strip().lower() == "winner"
        by_year[(state, row["award_year"])] += 1
        city_year[(float(office["longitude"]), float(office["latitude"]),
                   office["map_city"], row["award_year"])] += 1
    assert sum(listed.values()) == 65
    with (DATA / "publisher_office_state_summary.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["state", "state_name", "listed_books", "winning_books", "winner_share_pct"])
        for state, name in STATE_NAMES.items():
            n = listed[state]
            writer.writerow([state, name, n, wins[state], round(100 * wins[state] / n, 1) if n else ""])
    hex_bins(city_year)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/build_geography.py ABS_STE_2021.zip | --counts-only")
    if sys.argv[1] != "--counts-only":
        boundaries(Path(sys.argv[1]))
    counts()
