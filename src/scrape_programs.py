from pathlib import Path
import json
import re
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

PROGRAM_URLS = {
    "BITMAN_MAIN": "https://www.bcit.ca/programs/business-information-technology-management-diploma-full-time-6235dipma/",
    "BITMAN_ADM": "https://www.bcit.ca/programs/business-information-technology-management-analytics-data-management-option-diploma-full-time-623cdipma/",
    "BITMAN_AIM": "https://www.bcit.ca/programs/business-information-technology-management-artificial-intelligence-management-option-diploma-full-time-623adipma/",
    "BITMAN_ESM": "https://www.bcit.ca/programs/business-information-technology-management-enterprise-systems-management-option-diploma-full-time-623bdipma/",
}

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")

def find_heading(soup: BeautifulSoup, needle: str):
    for tag in soup.find_all(["h2", "h3", "h4"]):
        if needle.lower() in clean_text(tag.get_text(" ", strip=True)).lower():
            return tag
    return None

def section_paragraphs(heading, stop_tags=("h2",)):
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

def scrape_program(name: str, url: str) -> dict:
    soup = get_soup(url)

    title_tag = soup.find("h1")
    title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else name

    overview_heading = find_heading(soup, "Overview")
    overview = section_paragraphs(overview_heading, stop_tags=("h2",))[:5]

    continuation_heading = find_heading(soup, "Continuation requirements")
    continuation = section_paragraphs(continuation_heading, stop_tags=("h2",))[:10]

    courses_heading = find_heading(soup, "Courses")
    courses_section = section_paragraphs(courses_heading, stop_tags=("h2",))[:10]

    return {
        "name": name,
        "title": title,
        "url": url,
        "overview": overview,
        "continuation_requirements": continuation,
        "courses_section": courses_section,
    }

def main():
    records = [scrape_program(name, url) for name, url in PROGRAM_URLS.items()]

    raw_path = RAW_DIR / "program_pages.json"
    raw_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_lines = [
        "# BITMAN Program Page Summary",
        "",
        "This file is generated from official BCIT program pages.",
        "",
    ]

    for record in records:
        summary_lines.append(f"## {record['title']}")
        summary_lines.append(f"Source: {record['url']}")
        summary_lines.append("")
        summary_lines.append("### Overview")
        for item in record["overview"]:
            summary_lines.append(f"- {item}")
        summary_lines.append("")

        if record["continuation_requirements"]:
            summary_lines.append("### Continuation requirements")
            for item in record["continuation_requirements"]:
                summary_lines.append(f"- {item}")
            summary_lines.append("")

        if record["courses_section"]:
            summary_lines.append("### Courses section")
            for item in record["courses_section"]:
                summary_lines.append(f"- {item}")
            summary_lines.append("")

    summary_path = PROCESSED_DIR / "program_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Wrote {raw_path}")
    print(f"Wrote {summary_path}")

if __name__ == "__main__":
    main()
