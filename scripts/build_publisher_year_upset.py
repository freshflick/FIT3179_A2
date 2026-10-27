"""Rebuild the five-year publisher intersection view from attributed records."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEARS = [str(year) for year in range(2022, 2027)]


def make_spec():
    rows = list(csv.DictReader((ROOT / "data/pmla_2022_2026.csv").open()))
    by_publisher = defaultdict(set)
    for row in rows:
        by_publisher[row["publisher_key"]].add(row["award_year"])
    buckets = defaultdict(list)
    for publisher, years in by_publisher.items():
        mask = "".join("1" if year in years else "0" for year in YEARS)
        buckets[mask].append(publisher)
    patterns = []
    dots = []
    connectors = []
    for mask, members in buckets.items():
        pattern = {
            "pattern": mask,
            "publishers": len(members),
            "yearList": ", ".join(year for year, active in zip(YEARS, mask) if active == "1"),
            "members": sorted(members),
        }
        patterns.append(pattern)
        active_indices = []
        for year_index, active in enumerate(mask):
            dots.append({"pattern": mask, "yearIndex": year_index,
                         "active": active == "1", "publishers": len(members),
                         "year": YEARS[year_index]})
            if active == "1":
                active_indices.append(year_index)
        if len(active_indices) > 1:
            connectors.append({"pattern": mask, "firstYear": min(active_indices),
                               "lastYear": max(active_indices), "allFive": mask == "11111"})
    patterns.sort(key=lambda item: (-item["publishers"], item["pattern"]))
    count_frequency = Counter(item["publishers"] for item in patterns)
    all_five_count = next(item["publishers"] for item in patterns if item["pattern"] == "11111")
    labelled_counts = set()
    for item in patterns:
        count = item["publishers"]
        # Keep the all-five-year highlight explicit, then label one bar per
        # repeated count so the bars remain comparable without repeating text.
        is_all_five = item["pattern"] == "11111"
        reserve_for_highlight = count == all_five_count and count_frequency[count] > 1
        item["showLabel"] = is_all_five or (
            count not in labelled_counts and not reserve_for_highlight
        )
        labelled_counts.add(count)
    order = [item["pattern"] for item in patterns]
    dots.sort(key=lambda item: (order.index(item["pattern"]), item["yearIndex"]))
    connectors.sort(key=lambda item: order.index(item["pattern"]))
    year_rows = [{"year": year, "yearIndex": index} for index, year in enumerate(YEARS)]
    counts = Counter(len(years) for years in by_publisher.values())
    total = len(by_publisher)
    return {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "description": "UpSet plot of publisher appearances across publisher-attributed Prime Minister’s Literary Awards shortlist records, 2022–2026.",
        "width": {"signal": "width"}, "height": 470,
        "padding": {"left": 4, "right": 4, "top": 8, "bottom": 4},
        "autosize": {"type": "fit-x", "contains": "padding", "resize": True},
        "background": "#ffffff",
        "signals": [{"name": "width", "update": "max(280, min(1120, windowSize()[0] - (windowSize()[0] < 650 ? 92 : 128)))",
                     "on": [{"events": "window:resize", "update": "max(280, min(1120, windowSize()[0] - (windowSize()[0] < 650 ? 92 : 128)))"}]}],
        "data": [{"name": "patterns", "values": patterns}, {"name": "dots", "values": dots},
                 {"name": "connectors", "values": connectors}, {"name": "years", "values": year_rows}],
        "scales": [
            {"name": "x", "type": "band", "domain": order, "range": [94, {"signal": "width - 20"}], "paddingInner": 0.2, "paddingOuter": 0.08},
            {"name": "barY", "type": "linear", "domain": {"data": "patterns", "field": "publishers"}, "zero": True, "nice": True, "range": [218, 56]},
            {"name": "yearY", "type": "linear", "domain": [0, 4], "range": [300, 420]}
        ],
        "marks": [
            {"type": "symbol", "encode": {"update": {"x": {"signal": "width - 226"}, "y": {"value": 21}, "size": {"value": 80}, "fill": {"value": "#B36E21"}}}},
            {"type": "text", "encode": {"update": {"x": {"signal": "width - 214"}, "y": {"value": 24}, "text": {"value": "Appears in all five years"}, "font": {"value": "Arial"}, "fontSize": {"value": 11}, "fill": {"value": "#50616b"}}}},
            {"type": "rule", "encode": {"update": {"x": {"value": 92}, "x2": {"signal": "width - 18"}, "y": {"value": 218}, "stroke": {"value": "#C9D7DD"}}}},
            {"type": "rect", "from": {"data": "patterns"}, "encode": {"update": {
                "x": {"scale": "x", "field": "pattern"}, "width": {"scale": "x", "band": 1},
                "y": {"scale": "barY", "field": "publishers"}, "y2": {"value": 218},
                "fill": {"signal": "datum.pattern === '11111' ? '#B36E21' : '#3B7693'"},
                "cornerRadiusTopLeft": {"value": 2}, "cornerRadiusTopRight": {"value": 2},
                "tooltip": {"signal": "datum.publishers + (datum.publishers === 1 ? ' publisher' : ' publishers') + ' appeared in ' + datum.yearList + ': ' + join(datum.members, ', ')"}
            }}},
            {"type": "text", "from": {"data": "patterns"}, "encode": {"update": {
                "x": {"scale": "x", "field": "pattern", "band": 0.5}, "y": {"signal": "scale('barY', datum.publishers) - 7"},
                "align": {"value": "center"}, "text": {"signal": "datum.showLabel ? datum.publishers : ''"}, "font": {"value": "Arial"},
                "fontSize": {"value": 12}, "fontWeight": {"value": "bold"}, "fill": {"value": "#233441"}
            }}},
            {"type": "text", "encode": {"update": {"x": {"value": 94}, "y": {"value": 260}, "text": {"value": "Years represented"}, "font": {"value": "Arial"}, "fontSize": {"value": 12}, "fontWeight": {"value": "bold"}, "fill": {"value": "#50616b"}}}},
            {"type": "rule", "from": {"data": "years"}, "encode": {"update": {
                "x": {"value": 92}, "x2": {"signal": "width - 18"}, "y": {"scale": "yearY", "field": "yearIndex"},
                "stroke": {"value": "#EEF2F4"}, "strokeWidth": {"value": 1}
            }}},
            {"type": "text", "from": {"data": "years"}, "encode": {"update": {
                "x": {"value": 86}, "y": {"scale": "yearY", "field": "yearIndex"}, "align": {"value": "right"}, "baseline": {"value": "middle"},
                "text": {"field": "year"}, "font": {"value": "Arial"}, "fontSize": {"value": 12}, "fontWeight": {"value": "bold"}, "fill": {"value": "#50616b"}
            }}},
            {"type": "rule", "from": {"data": "connectors"}, "encode": {"update": {
                "x": {"scale": "x", "field": "pattern", "band": 0.5}, "y": {"scale": "yearY", "field": "firstYear"},
                "y2": {"scale": "yearY", "field": "lastYear"}, "stroke": {"signal": "datum.allFive ? '#B36E21' : '#35566B'"}, "strokeWidth": {"value": 2}
            }}},
            {"type": "symbol", "from": {"data": "dots"}, "encode": {"update": {
                "x": {"scale": "x", "field": "pattern", "band": 0.5}, "y": {"scale": "yearY", "field": "yearIndex"},
                "size": {"value": 100}, "shape": {"value": "circle"},
                "fill": {"signal": "datum.active ? (datum.pattern === '11111' ? '#B36E21' : '#35566B') : '#DFE8EC'"},
                "stroke": {"value": "#ffffff"}, "strokeWidth": {"value": 1},
                "tooltip": {"signal": "datum.year + ': ' + (datum.active ? 'present' : 'not present') + '; ' + datum.publishers + ' publishers share this pattern'"}
            }}}
        ],
        "usermeta": {"source_rows": len(rows), "publishers": total, "appeared_once": counts[1], "appeared_all_five": counts[5]}
    }


def main():
    out = ROOT / "charts/section3/publisher_year_upset.vg.json"
    out.write_text(json.dumps(make_spec(), indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote five-year publisher presence matrix to {out}")


if __name__ == "__main__":
    main()
