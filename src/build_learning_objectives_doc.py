from pathlib import Path
from urllib.parse import urljoin
import re
import requests
from bs4 import BeautifulSoup, Tag

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
}

PROGRAM_URLS = {
    "BITMAN Main Program": "https://www.bcit.ca/programs/business-information-technology-management-diploma-full-time-6235dipma/",
    "Analytics Data Management (ADM)": "https://www.bcit.ca/programs/business-information-technology-management-analytics-data-management-option-diploma-full-time-623cdipma/",
    "Artificial Intelligence Management (AIM)": "https://www.bcit.ca/programs/business-information-technology-management-artificial-intelligence-management-option-diploma-full-time-623adipma/",
    "Enterprise Systems Management (ESM)": "https://www.bcit.ca/programs/business-information-technology-management-enterprise-systems-management-option-diploma-full-time-623bdipma/",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def find_heading(soup: BeautifulSoup, needles):
    if isinstance(needles, str):
        needles = [needles]

    for tag in soup.find_all(["h2", "h3", "h4", "h5"]):
        text = clean_text(tag.get_text(" ", strip=True)).lower()
        for needle in needles:
            if needle.lower() in text:
                return tag
    return None


def section_nodes_until_next_h2(heading):
    nodes = []
    if not heading:
        return nodes

    node = heading.find_next_sibling()
    while node:
        if isinstance(node, Tag) and node.name == "h2":
            break
        if isinstance(node, Tag):
            nodes.append(node)
        node = node.find_next_sibling()
    return nodes


def extract_section_texts(heading):
    texts = []
    for node in section_nodes_until_next_h2(heading):
        text = clean_text(node.get_text(" ", strip=True))
        if text:
            texts.append(text)
    return texts


def extract_section_list_items(heading):
    items = []
    for node in section_nodes_until_next_h2(heading):
        if node.name == "ul":
            for li in node.find_all("li"):
                text = clean_text(li.get_text(" ", strip=True))
                if text:
                    items.append(text)
        elif node.name == "p":
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                items.append(text)
    return items


def extract_students_learn_to(soup: BeautifulSoup):
    for tag in soup.find_all(["p", "h3", "h4", "strong", "div"]):
        text = clean_text(tag.get_text(" ", strip=True)).lower()
        if "students learn to" in text:
            next_ul = tag.find_next(lambda t: isinstance(t, Tag) and t.name == "ul")
            if next_ul:
                items = []
                for li in next_ul.find_all("li"):
                    li_text = clean_text(li.get_text(" ", strip=True))
                    if li_text:
                        items.append(li_text)
                if items:
                    return items
    return []


def extract_course_links_from_program_page(soup: BeautifulSoup, base_url: str):
    links = []
    courses_heading = find_heading(soup, "Courses")

    # first try: only links inside the Courses section
    if courses_heading:
        for node in section_nodes_until_next_h2(courses_heading):
            for a in node.find_all("a", href=True):
                href = urljoin(base_url, a["href"]).split("#")[0]
                if "/courses/" in href:
                    links.append(href)

    # fallback: if nothing found, search the whole page
    if not links:
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"]).split("#")[0]
            if "/courses/" in href:
                links.append(href)

    # dedupe while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    return unique_links


def extract_overview(soup: BeautifulSoup):
    overview_heading = find_heading(soup, "Overview")
    texts = extract_section_texts(overview_heading)
    return texts[:3]


def extract_course_code(text: str) -> str:
    match = re.search(r"\b([A-Z]{4})[- ]?(\d{4})\b", text.upper())
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return ""


def extract_course_info(url: str) -> dict:
    soup = get_soup(url)

    title_tag = soup.find("h1")
    title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else url
    course_code = extract_course_code(title)

    prereq_heading = find_heading(soup, ["Prerequisite", "Prerequisites"])
    learning_heading = find_heading(soup, "Learning Outcomes")
    overview_heading = find_heading(soup, ["Course Overview", "Overview"])

    prereqs = extract_section_list_items(prereq_heading)
    learning_outcomes = extract_section_list_items(learning_heading)
    overview_texts = extract_section_texts(overview_heading)

    return {
        "course_code": course_code,
        "title": title,
        "url": url,
        "overview": overview_texts[:2],
        "prerequisites": prereqs,
        "learning_outcomes": learning_outcomes,
    }


def main():
    program_records = []
    course_to_programs = {}
    all_course_links = []

    print("Scraping program pages...")

    for program_name, url in PROGRAM_URLS.items():
        soup = get_soup(url)
        title_tag = soup.find("h1")
        title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else program_name

        overview = extract_overview(soup)
        goals = extract_students_learn_to(soup)
        course_links = extract_course_links_from_program_page(soup, url)

        program_records.append({
            "name": program_name,
            "title": title,
            "url": url,
            "overview": overview,
            "goals": goals,
            "course_links": course_links,
        })

        for link in course_links:
            all_course_links.append(link)
            course_to_programs.setdefault(link, set()).add(program_name)

        print(f"  {program_name}: found {len(course_links)} course links")

    # dedupe course links
    seen = set()
    unique_course_links = []
    for link in all_course_links:
        if link not in seen:
            seen.add(link)
            unique_course_links.append(link)

    print(f"\nScraping {len(unique_course_links)} unique course pages...")

    course_records = []
    for link in unique_course_links:
        try:
            record = extract_course_info(link)
            record["listed_in"] = sorted(course_to_programs.get(link, []))
            course_records.append(record)
            print(f"  OK: {record['course_code']} | {record['title']}")
        except Exception as e:
            print(f"  FAILED: {link} -> {e}")

    course_records.sort(key=lambda x: (x["course_code"] or "ZZZZ 9999", x["title"]))

    lines = []
    lines.append("# BITMAN Learning Objectives and Program / Option Goals")
    lines.append("")
    lines.append("This document was generated from official BCIT program and course pages.")
    lines.append("")

    lines.append("## Program Structure")
    lines.append("")
    lines.append("The main BITMAN program page describes a first-year foundation followed by second-year specialization options.")
    lines.append("")

    for record in program_records:
        lines.append(f"### {record['title']}")
        lines.append(f"- Source: {record['url']}")
        if record["overview"]:
            lines.append("- Overview:")
            for item in record["overview"]:
                lines.append(f"  - {item}")
        if record["course_links"]:
            lines.append(f"- Number of linked course pages found: {len(record['course_links'])}")
        else:
            lines.append("- Number of linked course pages found: 0")
        lines.append("")

    lines.append("## Program / Option Goals")
    lines.append("")
    lines.append("This section uses the official BCIT option-page outcome bullets where available.")
    lines.append("")

    for record in program_records:
        lines.append(f"### {record['title']}")
        lines.append(f"- Source: {record['url']}")
        if record["goals"]:
            for goal in record["goals"]:
                lines.append(f"- {goal}")
        else:
            lines.append("- No explicit 'Students learn to' bullets were found on this page.")
        lines.append("")

    lines.append("## Courses and Learning Objectives")
    lines.append("")

    if not course_records:
        lines.append("No course pages were successfully scraped.")
        lines.append("")
    else:
        for course in course_records:
            heading = course["course_code"] if course["course_code"] else course["title"]
            lines.append(f"### {heading} — {course['title']}")
            lines.append(f"- Course page: {course['url']}")

            if course["listed_in"]:
                lines.append(f"- Listed in: {', '.join(course['listed_in'])}")

            if course["prerequisites"]:
                lines.append("- Prerequisites:")
                for prereq in course["prerequisites"]:
                    lines.append(f"  - {prereq}")
            else:
                lines.append("- Prerequisites: none found on page")

            if course["learning_outcomes"]:
                lines.append("- Learning outcomes:")
                for outcome in course["learning_outcomes"]:
                    lines.append(f"  - {outcome}")
            else:
                lines.append("- Learning outcomes: none found on page")

            if course["overview"]:
                lines.append("- Overview excerpt:")
                for text in course["overview"]:
                    lines.append(f"  - {text}")

            lines.append("")

    out_path = OUTPUTS_DIR / "all_learning_objectives.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()