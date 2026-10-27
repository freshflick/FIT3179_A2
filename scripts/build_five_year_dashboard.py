"""Build comparable five-year award tables from checked-in source lists.

The older Prime Minister's Literary Awards pages omit publisher names for six
shortlisted books. Those records are not fabricated or assigned to a publisher;
the publisher charts use the 144 rows with a published publisher attribution.
"""

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

STELLA_2022_URL = "https://stellacanyon.com/2022/02/the-2022-stella-prize-judges-report/"
STELLA_2023_URL = "https://stellacanyon.com/2023/02/2023-stella-prize-longlist/"
STELLA_2022_WINNER_URL = "https://stellacanyon.com/2022/04/announcing-the-winner-of-the-2022-stella-prize/"
STELLA_2023_WINNER_URL = "https://stellacanyon.com/2023/04/announcing-the-winner-of-the-2023-stella-prize/"

# Genre groups follow the dashboard's broad comparative scheme. They describe
# book form, not official Stella categories.
STELLA_2022 = [
    ("Coming of Age in the War on Terror", "Randa Abdel-Fattah", "NewSouth Books", "Nonfiction", "longlisted"),
    ("TAKE CARE", "Eunice Andrada", "Giramondo Publishing", "Poetry", "shortlisted"),
    ("Dropbear", "Evelyn Araluen", "University of Queensland Press", "Poetry", "winner"),
    ("She Is Haunted", "Paige Clark", "Allen & Unwin", "Fiction", "longlisted"),
    ("No Document", "Anwen Crawford", "Giramondo Publishing", "Nonfiction", "shortlisted"),
    ("Bodies of Light", "Jennifer Down", "Text Publishing", "Fiction", "shortlisted"),
    ("Bila Yarrudhanggalangdhuray", "Anita Heiss", "Simon & Schuster Australia", "Fiction", "longlisted"),
    ("Stone Fruit", "Lee Lai", "Fantagraphics", "Graphic Novel", "shortlisted"),
    ("Permafrost", "S. J. Norman", "University of Queensland Press", "Fiction", "longlisted"),
    ("Homecoming", "Elfie Shiosaki", "Magabala Books", "Poetry", "shortlisted"),
    ("The Open", "Lucy Van", "Cordite Books", "Poetry", "longlisted"),
    ("Another Day in the Colony", "Chelsea Watego", "University of Queensland Press", "Nonfiction", "longlisted"),
]

STELLA_2023 = [
    ("The Furies", "Mandy Beaumont", "Hachette Australia", "Fiction", "longlisted"),
    ("Every Version of You", "Grace Chan", "Affirm Press", "Fiction", "longlisted"),
    ("We Come With This Place", "Debra Dank", "Echo Publishing", "Nonfiction/Memoir", "shortlisted"),
    ("big beautiful female theory", "Eloise Grills", "Affirm Press", "Nonfiction", "shortlisted"),
    ("The Jaguar", "Sarah Holland-Batt", "University of Queensland Press", "Poetry", "winner"),
    ("Hydra", "Adriane Howell", "Transit Lounge", "Fiction", "shortlisted"),
    ("Jack of Hearts: QX11594", "Jackie Huggins and Ngaire Jarro", "Magabala Books", "Nonfiction/Memoir", "longlisted"),
    ("All That’s Left Unsaid", "Tracey Lien", "HarperCollins Publishers", "Fiction", "longlisted"),
    ("Indelible City: Dispossession and Defiance in Hong Kong", "Louisa Lim", "Text Publishing", "Nonfiction/Memoir", "shortlisted"),
    ("Iris", "Fiona Kelly McGregor", "Pan Macmillan Australia", "Fiction", "longlisted"),
    ("Decadence", "Thuy On", "UWA Publishing", "Nonfiction", "longlisted"),
    ("Bad Art Mother", "Edwina Preston", "Wakefield Press", "Fiction", "shortlisted"),
]

ALIASES = {
    "UQP": "University of Queensland Press",
    "University of Queensland Press": "University of Queensland Press",
    "S&S": "Simon & Schuster Australia",
    "Simon & Schuster": "Simon & Schuster Australia",
    "S&S Bundyi": "Simon & Schuster Australia",
    "A&U": "Allen & Unwin",
    "Allen & Unwin": "Allen & Unwin",
    "NewSouth": "NewSouth Publishing",
    "Giramondo": "Giramondo Publishing",
    "Cordite": "Cordite Books",
    "Cordite Books": "Cordite Books",
    "Magabala": "Magabala Books",
    "Text": "Text Publishing",
    "Fantagraphics": "Fantagraphics",
    "HQ Fiction/HarperCollins Publishers": "HarperCollins Publishers",
    "Pan Macmillan Australia": "Pan Macmillan Australia",
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_stella():
    old = []
    for year, entries, source in ((2022, STELLA_2022, STELLA_2022_URL),
                                  (2023, STELLA_2023, STELLA_2023_URL)):
        winner_url = STELLA_2022_WINNER_URL if year == 2022 else STELLA_2023_WINNER_URL
        for title, author, publisher, genre, outcome in entries:
            old.append({
                "award_year": str(year), "award": "Stella Prize", "category": "Overall",
                "title": title, "author": author, "publisher": publisher,
                "publisher_key": ALIASES.get(publisher, publisher), "genre": genre,
                "outcome": outcome, "source_url": source, "winner_source_url": winner_url if outcome == "winner" else "",
            })
    current = read_csv(DATA / "stella_2024_2026.csv")
    rows = old + current
    assert len(rows) == 60
    assert Counter(r["award_year"] for r in rows) == {str(y): 12 for y in range(2022, 2027)}
    assert Counter(r["outcome"] for r in rows) == {"longlisted": 30, "shortlisted": 25, "winner": 5}
    write_csv(DATA / "stella_2022_2026.csv", rows, list(rows[0]))
    return rows


def build_pmla():
    earlier = read_csv(DATA / "pmla_2022_2023_geography.csv")
    current = read_csv(DATA / "pmla_2024_2026.csv")
    rows = []
    for source_rows in (earlier, current):
        for row in source_rows:
            category = row["category"].replace("Children’s Literature", "Children’s literature")
            category = category.replace("Children's literature", "Children’s literature")
            publisher = row.get("publisher", row.get("publisher_raw", ""))
            rows.append({
                "award_year": row["award_year"], "award": "Prime Minister's Literary Awards",
                "category": category, "title": row["title"], "author": row.get("author", ""),
                "publisher": publisher, "publisher_key": row["publisher_key"],
                "genre": row.get("genre", category), "outcome": row["outcome"],
                "source_url": row["source_url"],
            })
    assert len(rows) == 144
    assert Counter(r["award_year"] for r in rows) == {str(y): 30 for y in range(2024, 2027)} | {"2022": 25, "2023": 29}
    write_csv(DATA / "pmla_2022_2026.csv", rows, list(rows[0]))
    return rows


def build_comparison(pmla, stella):
    pmla_counts = Counter(r["publisher_key"] for r in pmla if r["publisher_key"])
    stella_counts = Counter(r["publisher_key"] for r in stella if r["publisher_key"])
    publishers = set(pmla_counts) | set(stella_counts)
    rows = [{"publisher_key": key, "pmla_books": pmla_counts[key], "stella_books": stella_counts[key]}
            for key in publishers if pmla_counts[key] + stella_counts[key] >= 4]
    rows.sort(key=lambda row: (-(row["pmla_books"] + row["stella_books"]), row["publisher_key"]))
    rows = rows[:12]
    write_csv(DATA / "publisher_award_comparison.csv", rows,
              ["publisher_key", "pmla_books", "stella_books"])
    return rows


def main():
    stella = build_stella()
    pmla = build_pmla()
    comparison = build_comparison(pmla, stella)
    print(f"PMLA publisher-attributed rows: {len(pmla)}; Stella longlist rows: {len(stella)}")
    print("PMLA publishers by count:", Counter(r["publisher_key"] for r in pmla).most_common(12))
    print("Stella genre groups:", Counter(r["genre"] for r in stella))
    print("Comparison publishers:", comparison)


if __name__ == "__main__":
    main()
