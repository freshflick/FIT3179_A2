"""Build an alluvial that keeps Stella's shortlisted and longlisted exits visible."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENRES = ("Fiction", "Non-fiction & memoir", "Poetry", "Graphic novel")
COLOURS = ("#63336f", "#9584bf", "#d78e64", "#648b97")


def group_genre(value):
    if value == "Fiction":
        return "Fiction"
    if value == "Poetry":
        return "Poetry"
    if value == "Graphic Novel":
        return "Graphic novel"
    return "Non-fiction & memoir"


def records():
    books = list(csv.DictReader((ROOT / "data/stella_2024_2026.csv").open()))
    counts = {genre: [0, 0, 0] for genre in GENRES}
    for book in books:
        entry = counts[group_genre(book["genre"])]
        entry[0] += 1
        entry[1] += book["outcome"] != "longlisted"
        entry[2] += book["outcome"] == "winner"
    assert [sum(x[i] for x in counts.values()) for i in range(3)] == [36, 18, 3]
    return counts


def make_data(counts):
    lpos = apos = epos = wpos = fpos = qpos = 0
    epos, fpos, qpos = 18, 3, 18
    nodes, links = [], []

    def node(stage, genre, phase, start, size, opacity):
        if size:
            nodes.append(dict(stage=stage, genre=genre, phase=phase,
                              y0=start, y1=start + size, count=size, opacity=opacity))

    def link(src, dst, genre, phase, src_start, dst_start, size, opacity):
        if size:
            links.append(dict(src=src, dst=dst, genre=genre, phase=phase,
                              sy0=src_start, sy1=src_start + size,
                              ty0=dst_start, ty1=dst_start + size,
                              count=size, opacity=opacity))

    for genre in GENRES:
        longlisted, shortlisted, winners = counts[genre]
        lost_early = longlisted - shortlisted
        lost_late = shortlisted - winners
        node("longlist", genre, "longlisted", lpos, longlisted, 0.94)
        node("shortlist", genre, "advanced", apos, shortlisted, 0.94)
        node("shortlist", genre, "stopped at longlist", epos, lost_early, 0.45)
        node("outcome", genre, "winner", wpos, winners, 0.98)
        node("outcome", genre, "stopped at shortlist", fpos, lost_late, 0.42)
        node("outcome", genre, "stopped at longlist", qpos, lost_early, 0.25)
        link("longlist", "shortlist", genre, "advanced", lpos, apos, shortlisted, 0.68)
        link("longlist", "shortlist", genre, "stopped at longlist",
             lpos + shortlisted, epos, lost_early, 0.21)
        link("shortlist", "outcome", genre, "winner", apos, wpos, winners, 0.75)
        link("shortlist", "outcome", genre, "stopped at shortlist",
             apos + winners, fpos, lost_late, 0.27)
        link("shortlist", "outcome", genre, "stopped at longlist",
             epos, qpos, lost_early, 0.13)
        lpos += longlisted
        apos += shortlisted
        epos += lost_early
        wpos += winners
        fpos += lost_late
        qpos += lost_early
    assert (lpos, apos, epos, wpos, fpos, qpos) == (36, 18, 36, 3, 18, 36)
    return nodes, links


def make_spec(nodes, links):
    path = (
        "'M' + (scale('stageX', datum.src) + nodeWidth/2) + ',' + scale('booksY', datum.sy0)"
        " + ' C' + ((scale('stageX', datum.src) + scale('stageX', datum.dst))/2) + ',' + scale('booksY', datum.sy0)"
        " + ' ' + ((scale('stageX', datum.src) + scale('stageX', datum.dst))/2) + ',' + scale('booksY', datum.ty0)"
        " + ' ' + (scale('stageX', datum.dst) - nodeWidth/2) + ',' + scale('booksY', datum.ty0)"
        " + ' L' + (scale('stageX', datum.dst) - nodeWidth/2) + ',' + scale('booksY', datum.ty1)"
        " + ' C' + ((scale('stageX', datum.src) + scale('stageX', datum.dst))/2) + ',' + scale('booksY', datum.ty1)"
        " + ' ' + ((scale('stageX', datum.src) + scale('stageX', datum.dst))/2) + ',' + scale('booksY', datum.sy1)"
        " + ' ' + (scale('stageX', datum.src) + nodeWidth/2) + ',' + scale('booksY', datum.sy1) + ' Z'"
    )
    return {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "description": "Alluvial of 36 Stella longlisted books in 2024–2026, retaining the 18 books that stopped at the longlist and the 15 that stopped after the shortlist.",
        "height": 435,
        "padding": {"left": 18, "right": 18, "top": 8, "bottom": 48},
        "autosize": "pad", "background": "#ffffff",
        "signals": [
            {"name": "width", "update": "min(1100, max(290, windowSize()[0] - (windowSize()[0] <= 600 ? 96 : windowSize()[0] <= 1000 ? 144 : 190)))",
             "on": [{"events": "window:resize", "update": "min(1100, max(290, windowSize()[0] - (windowSize()[0] <= 600 ? 96 : windowSize()[0] <= 1000 ? 144 : 190)))"}]},
            {"name": "nodeWidth", "value": 15}
        ],
        "data": [
            {"name": "nodes", "values": nodes},
            {"name": "links", "values": links},
            {"name": "stageLabels", "values": [
                {"stage": "longlist", "heading": "LONGLIST · 36"},
                {"stage": "shortlist", "heading": "SHORTLIST · 18"},
                {"stage": "outcome", "heading": "WINNERS · 3"}]},
            {"name": "outcomeLabels", "values": [
                {"label": "3 winners", "y": 1.5, "weight": "bold"},
                {"label": "15 stopped after shortlist", "y": 10.5, "weight": "normal"},
                {"label": "18 stopped at longlist", "y": 27, "weight": "normal"}]}
        ],
        "scales": [
            {"name": "stageX", "type": "ordinal", "domain": ["longlist", "shortlist", "outcome"],
             "range": [{"signal": "width < 600 ? 32 : 68"}, {"signal": "width * 0.48"},
                       {"signal": "width - (width < 600 ? 32 : 195)"}]},
            {"name": "booksY", "type": "linear", "domain": [0, 36], "range": [68, 388], "zero": True},
            {"name": "genreColour", "type": "ordinal", "domain": list(GENRES), "range": list(COLOURS)}
        ],
        "legends": [{"fill": "genreColour", "orient": "bottom", "direction": "horizontal",
                     "title": None, "symbolType": "square", "symbolSize": 115,
                     "labelFont": "Arial", "labelFontSize": 11, "labelColor": "#3c4c56",
                     "columns": 2, "offset": 10}],
        "marks": [
            {"type": "path", "from": {"data": "links"},
             "encode": {"update": {
                 "path": {"signal": path},
                 "fill": {"scale": "genreColour", "field": "genre"},
                 "fillOpacity": {"field": "opacity"},
                 "tooltip": {"signal": "datum.genre + ': ' + datum.count + ' books ' + datum.phase"}
             }, "hover": {"fillOpacity": {"value": 0.88}}}},
            {"type": "rect", "from": {"data": "nodes"},
             "encode": {"update": {
                 "x": {"signal": "scale('stageX', datum.stage) - nodeWidth/2"},
                 "x2": {"signal": "scale('stageX', datum.stage) + nodeWidth/2"},
                 "y": {"scale": "booksY", "field": "y0"},
                 "y2": {"scale": "booksY", "field": "y1"},
                 "fill": {"scale": "genreColour", "field": "genre"},
                 "fillOpacity": {"field": "opacity"},
                 "stroke": {"value": "#ffffff"}, "strokeWidth": {"value": 1},
                 "tooltip": {"signal": "datum.genre + ': ' + datum.count + ' books ' + datum.phase"}
             }}},
            {"type": "rule", "encode": {"update": {
                "x": {"signal": "scale('stageX', 'shortlist') + 14"},
                "x2": {"signal": "scale('stageX', 'outcome') - 18"},
                "y": {"scale": "booksY", "value": 18},
                "stroke": {"value": "#d7e1e4"}, "strokeDash": {"value": [3, 4]},
                "strokeWidth": {"value": 1}}}},
            {"type": "text", "from": {"data": "stageLabels"},
             "encode": {"update": {
                 "x": {"scale": "stageX", "field": "stage"},
                 "y": {"value": 22}, "align": {"value": "center"},
                 "baseline": {"value": "middle"}, "text": {"field": "heading"},
                 "font": {"value": "Arial"}, "fontSize": {"value": 12},
                 "fontWeight": {"value": "bold"}, "fill": {"value": "#233441"}}}},
            {"type": "text", "from": {"data": "outcomeLabels"},
             "encode": {"update": {
                 "x": {"signal": "scale('stageX', 'outcome') + 22"},
                 "y": {"scale": "booksY", "field": "y"},
                 "text": {"field": "label"}, "baseline": {"value": "middle"},
                 "font": {"value": "Arial"}, "fontSize": {"value": 12},
                 "fontWeight": {"field": "weight"}, "fill": {"value": "#3c4c56"},
                 "opacity": {"signal": "width >= 620 ? 1 : 0"}}}}
        ]
    }


def main():
    nodes, links = make_data(records())
    path = ROOT / "charts/section3/stella_genre_progression.vg.json"
    path.write_text(json.dumps(make_spec(nodes, links), indent=2) + "\n")
    print(f"{len(nodes)} nodes, {len(links)} ribbons")


if __name__ == "__main__":
    main()
