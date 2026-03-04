# BITMAN Map Scraping

## Project overview
This project explores BCIT's Business Information Technology Management (BITMAN) program by scraping official BCIT program and course pages and turning unstructured web content into structured outputs.

## Project goals
- identify how BITMAN options work
- capture course prerequisites from official course pages
- collect learning outcomes from course pages
- flag courses that currently show online or flexible offerings
- build a prerequisite map students can read

## Why this fits the assignment
The source data is non-tabular and unstructured because it comes from HTML program pages and course pages, not from a ready-made CSV file.

## Repository structure
- `src/` -> Python scripts
- `data/raw/` -> scraped JSON
- `data/processed/` -> cleaned CSV and summaries
- `outputs/` -> prerequisite map and flex summary
- `docs/` -> citations, AI use statement, reflection

## Extra Maps
- [BITMAN Option Path Map](outputs/bitman_option_map.md)
- [BITMAN Flex / Online Course Map](outputs/bitman_flex_map.md)

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 src/scrape_programs.py
python3 src/scrape_courses.py
python3 src/build_map.py# BITMAN Map Scraping

## Documentation
- `docs/CITATIONS.md`
- `docs/AI_USE_STATEMENT.md`
- `docs/REFLECTION.md`
