from pathlib import Path
import json
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
}

COURSE_URLS = [
    "https://www.bcit.ca/courses/business-information-systems-1-microsoft-365-for-windows-bsys-1001/",
    "https://www.bcit.ca/courses/introduction-to-business-data-analytics-with-ms-excel-ms-365-for-windows-bsys-2051/",
    "https://www.bcit.ca/courses/business-data-management-with-ms-access-microsoft-365-for-windows-bsys-2061/",
]

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def standardize_code(text: str) -> str:
    match = re.search(r"\b([A-Z]{4})\s?(\d{4})\b", text.upper())
    if not match:
        return ""
    return f"{match.group(1)} {match.group(2)}"

def extract_codes(text: str) -> list[str]:
    matches = re.findall(r"\b([A-Z]{4})\s?(\d{4})\b", text.upper())
    codes = {f"{a} {b}" for a, b in matches}
    return sorted(codes)

def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")

def find_heading(soup: BeautifulSoup, needle: str):
    for tag in soup.find_all(["h2", "h3", "h4", "h5"]):
        if needle.lower() in clean_text(tag.get_text(" ", strip=True)).lower():
            return tag
    return None

def section_texts(heading, stop_tags=("h2",)):
    results = []
    node = heading.find_next_sibling() if heading else None

    while node:
        if isinstance(node, Tag) and node.name in stop_tags:
            break
        if isinstance(node, Tag):
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                results.append(text)
        node = node.find_next_sibling()

    return results

def section_list_items(heading, stop_tags=("h2",)):
    items = []
    node = heading.find_next_sibling() if heading else None

    while node:
        if isinstance(node, Tag) and node.name in stop_tags:
            break
        if isinstance(node, Tag):
            if node.name == "ul":
                for li in node.find_all("li"):
                    text = clean_text(li.get_text(" ", strip=True))
                    if text:
                        items.append(text)
            elif node.name == "p":
                text = clean_text(node.get_text(" ", strip=True))
                if text:
                    items.append(text)
        node = node.find_next_sibling()

    return items

def scrape_course(url: str) -> dict:
    soup = get_soup(url)

    title_tag = soup.find("h1")
    title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else url
    course_code = standardize_code(title)

    overview_heading = find_heading(soup, "Course Overview")
    prereq_heading = find_heading(soup, "Prerequisite")
    outcomes_heading = find_heading(soup, "Learning Outcomes")
    offerings_heading = find_heading(soup, "Course Offerings")

    overview_texts = section_texts(overview_heading, stop_tags=("h2", "h3"))
    overview_excerpt = " ".join(overview_texts[:2])

    prereq_items = section_list_items(prereq_heading, stop_tags=("h2",))
    prereq_text = " | ".join(prereq_items)
    prereq_codes = extract_codes(prereq_text)

    learning_outcomes = section_list_items(outcomes_heading, stop_tags=("h2",))

    offerings_text = " ".join(section_texts(offerings_heading, stop_tags=("h2",)))
    has_online = "online" in offerings_text.lower()

    return {
        "course_code": course_code,
        "title": title,
        "url": url,
        "overview_excerpt": overview_excerpt,
        "prerequisite_text": prereq_text,
        "prereq_codes": prereq_codes,
        "learning_outcomes": learning_outcomes,
        "learning_outcomes_count": len(learning_outcomes),
        "has_online": has_online,
        "offerings_excerpt": offerings_text[:1000],
    }

def main():
    records = [scrape_course(url) for url in COURSE_URLS]

    raw_path = RAW_DIR / "course_pages.json"
    raw_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = []
    for record in records:
        rows.append({
            "course_code": record["course_code"],
            "title": record["title"],
            "url": record["url"],
            "prerequisite_text": record["prerequisite_text"],
            "prereq_codes": "; ".join(record["prereq_codes"]),
            "learning_outcomes_count": record["learning_outcomes_count"],
            "has_online": record["has_online"],
            "overview_excerpt": record["overview_excerpt"],
        })

    df = pd.DataFrame(rows)
    csv_path = PROCESSED_DIR / "courses.csv"
    df.to_csv(csv_path, index=False)

    print(f"Wrote {raw_path}")
    print(f"Wrote {csv_path}")

if __name__ == "__main__":
    main()
