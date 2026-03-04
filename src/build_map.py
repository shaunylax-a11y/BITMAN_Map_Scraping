from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUTS_DIR = BASE_DIR / "outputs"

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

def node_id(course_code: str) -> str:
    return course_code.replace(" ", "_").replace("-", "_")

def main():
    course_path = RAW_DIR / "course_pages.json"
    records = json.loads(course_path.read_text(encoding="utf-8"))

    all_codes = set()
    for record in records:
        if record["course_code"]:
            all_codes.add(record["course_code"])
        for prereq in record["prereq_codes"]:
            all_codes.add(prereq)

    title_lookup = {r["course_code"]: r["title"] for r in records if r["course_code"]}

    mermaid_lines = ["flowchart LR"]

    for code in sorted(all_codes):
        label = title_lookup.get(code, code)
        safe_label = label.replace('"', "'")
        mermaid_lines.append(f'    {node_id(code)}["{safe_label}"]')

    for record in records:
        current = record["course_code"]
        if not current:
            continue
        for prereq in record["prereq_codes"]:
            mermaid_lines.append(f"    {node_id(prereq)} --> {node_id(current)}")

    mermaid_path = OUTPUTS_DIR / "bitman_prereq_map.mmd"
    mermaid_path.write_text("\n".join(mermaid_lines), encoding="utf-8")

    flex_lines = [
        "# Flexible / Online Offering Snapshot",
        "",
        "Generated from the current BCIT course pages scraped by this project.",
        "",
    ]

    for record in records:
        if record["has_online"]:
            flex_lines.append(f"- {record['course_code']}: {record['title']}")
            flex_lines.append(f"  - Source: {record['url']}")
            if record["offerings_excerpt"]:
                flex_lines.append(f"  - Offering excerpt: {record['offerings_excerpt'][:250]}...")
            flex_lines.append("")

    flex_path = OUTPUTS_DIR / "flex_courses.md"
    flex_path.write_text("\n".join(flex_lines), encoding="utf-8")

    print(f"Wrote {mermaid_path}")
    print(f"Wrote {flex_path}")

if __name__ == "__main__":
    main()
