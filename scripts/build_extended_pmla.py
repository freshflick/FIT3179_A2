"""Create the map-only 2022–2026 PMLA book table from verified source extracts.

The 2022 and 2023 source pages must first be saved as plain text in /private/tmp
using pandoc. This deliberately keeps missing publisher fields out of the map.
The published CSV is checked into the repository, so the site needs no scraper.
"""

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = {
    2022: "https://creative.gov.au/2022-prime-ministers-literary-awards-winners-shortlistees-and-judges",
    2023: "https://creative.gov.au/2023-prime-ministers-literary-awards-winners-shortlistees-and-judges",
}
TITLES_2022 = [
    "Red Heaven", "Devotion", "Night Blue", "The Hands of Pianists",
    "Dark as Last Night", "Mina and the Whole Wide World", "The Gaps",
    "100 Remarkable Feats by Xander Maze", "Tell Me Why for Young Adults",
    "Tiger Daughter", "Another Day in the Colony", "Rogue Forces",
    "Title Fight", "The Case that Stopped a Nation", "Puff Piece", "Semut",
    "Farmers or Hunter Gatherers? The Dark Emu Debate", "Return to Uluru",
    "White Russians, Red Peril", "Harlem Nights", "Human Looking",
    "Homecoming", "Dancing with Stephen Hawking", "Fish Work", "Fifteeners",
]
ALIASES = {
    "University of Queensland Press": "University of Queensland Press",
    "UQP": "University of Queensland Press",
    "Giramondo": "Giramondo Publishing",
    "Giramondo Publishing": "Giramondo Publishing",
    "Giramondo Publishing Company": "Giramondo Publishing",
    "Penguin Books Australia": "Penguin Random House Australia",
    "Penguin Random House": "Penguin Random House Australia",
    "Penguin Random House Australia: Hamish Hamilton": "Penguin Random House Australia",
    "Penguin Random House Australia: Michael Joseph": "Penguin Random House Australia",
    "Black Inc Books": "Black Inc.",
    "Schwartz Books: Black Inc.": "Black Inc.",
    "La Trobe University Press in conjunction with Black Inc.": "La Trobe University Press",
    "Melbourne University Press": "Melbourne University Publishing",
    "Melbourne University Publishing": "Melbourne University Publishing",
    "HarperCollins Publishers: Angus & Robertson": "HarperCollins Publishers",
    "Pan Macmillan Australia: Picador": "Pan Macmillan Australia",
    "Simon & Schuster Australia": "Simon & Schuster Australia",
    "Puncher & Wattmann": "Puncher and Wattmann",
    "Ultimo Press": "Ultimo Press",
}


def older_rows(year):
    lines = Path(f"/private/tmp/pmla{year}.txt").read_text().splitlines()
    last_publisher = 0
    category = ""
    categories = {"Fiction", "Children's literature", "Young adult literature",
                  "Non-fiction", "Australian history", "Poetry"}
    found = []
    for i, line in enumerate(lines):
        if line.strip() in categories:
            category = line.strip()
        match = re.match(r"^(?:Published by|Publisher):\s*(.+)$", line)
        if not match:
            continue
        segment = lines[last_publisher:i]
        last_publisher = i + 1
        raw_publisher = " ".join(match.group(1).split())
        if year == 2023:
            year_line = max(j for j in range(max(0, i - 10), i)
                            if lines[j].strip().startswith("Shortlist year:"))
            before = [v.strip() for v in lines[max(0, year_line - 10):year_line]
                      if v.strip()]
            title = before[-2]
            category = next((re.sub(r"^Shortlist category:\s*", "", lines[j]).strip()
                             for j in range(year_line + 1, min(i, year_line + 6))
                             if lines[j].strip().startswith("Shortlist category:")),
                            category)
        else:
            title = TITLES_2022[len(found)]
        outcome = "winner" if any(v.strip().startswith("WINNER:") for v in segment) else "shortlisted"
        if year == 2023 and title == "Unmaking Angas Downs: Myth and History on a Central Australian Pastoral Station":
            outcome = "winner"  # Creative Australia's 2023 winner announcement.
        found.append({"award_year": year, "award": "Prime Minister's Literary Awards",
                      "category": category, "title": title,
                      "publisher_raw": raw_publisher,
                      "publisher_key": ALIASES.get(raw_publisher, raw_publisher),
                      "outcome": outcome, "source_url": SOURCE[year]})
    assert len(found) == {2022: 25, 2023: 29}[year]
    assert sum(r["outcome"] == "winner" for r in found) == 6
    return found


def main():
    rows = older_rows(2022) + older_rows(2023)
    with (ROOT / "data/pmla_2022_2023_geography.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} sourced older shortlist records")


if __name__ == "__main__":
    main()
