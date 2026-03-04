from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUTS_DIR = BASE_DIR / "outputs"

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def clean_label(text: str) -> str:
    return text.replace('"', "'").strip()


def node_id(text: str) -> str:
    return (
        text.replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "")
        .replace(".", "")
    )


def write_mermaid_files(stem: str, title: str, mermaid_text: str):
    mmd_path = OUTPUTS_DIR / f"{stem}.mmd"
    md_path = OUTPUTS_DIR / f"{stem}.md"

    mmd_path.write_text(mermaid_text, encoding="utf-8")

    md_content = f"# {title}\n\n```mermaid\n{mermaid_text}\n```\n"
    md_path.write_text(md_content, encoding="utf-8")

    print(f"Wrote {mmd_path}")
    print(f"Wrote {md_path}")


def build_option_map():
    mermaid_lines = [
        "flowchart TD",
        '    BITMAN["BITMAN Diploma"]',
        '    YEAR1["Common First Year"]',
        '    ADM["Analytics Data Management"]',
        '    AIM["Artificial Intelligence Management"]',
        '    ESM["Enterprise Systems Management"]',
        '    NOTE["Option placement may depend on Year 1 GPA if seats are limited"]',
        "",
        "    BITMAN --> YEAR1",
        "    YEAR1 --> ADM",
        "    YEAR1 --> AIM",
        "    YEAR1 --> ESM",
        "    YEAR1 -.-> NOTE",
    ]

    write_mermaid_files(
        "bitman_option_map",
        "BITMAN Option Path Map",
        "\n".join(mermaid_lines),
    )


def build_flex_map():
    course_path = RAW_DIR / "course_pages.json"

    if not course_path.exists():
        print("Missing data/raw/course_pages.json")
        print("Run scrape_courses.py first.")
        return

    records = json.loads(course_path.read_text(encoding="utf-8"))

    mermaid_lines = [
        "flowchart LR",
        '    ONLINE["Shows Online / Flexible Offering"]',
        '    NOONLINE["No Online Offering Found in Current Scrape"]',
        "",
    ]

    for record in records:
        code = record.get("course_code", "").strip()
        title = record.get("title", "").strip()

        if not code:
            continue

        label = clean_label(f"{code}\\n{title}")
        nid = node_id(code)

        mermaid_lines.append(f'    {nid}["{label}"]')

        if record.get("has_online"):
            mermaid_lines.append(f"    ONLINE --> {nid}")
        else:
            mermaid_lines.append(f"    NOONLINE --> {nid}")

    write_mermaid_files(
        "bitman_flex_map",
        "BITMAN Flex / Online Course Map",
        "\n".join(mermaid_lines),
    )


def main():
    build_option_map()
    build_flex_map()


if __name__ == "__main__":
    main()