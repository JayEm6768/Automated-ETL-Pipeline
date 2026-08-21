"""
Transform step of the ETL pipeline.

Reads a raw JSON file produced by extract.py, cleans and normalizes
fields, extracts mentioned skills from each job description using the
skills dictionary in config.py, and dedupes postings.

Usage:
    python transform.py data/raw/jobs_raw_<timestamp>.json
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def extract_skills(description: str) -> list[str]:
    """
    Return the list of canonical skill names found in a job description,
    matched against config.SKILLS_DICTIONARY.
    """
    if not description:
        return []
    text = f" {description.lower()} "
    found = []
    for canonical_skill, surface_forms in config.SKILLS_DICTIONARY.items():
        for form in surface_forms:
            if form.lower() in text:
                found.append(canonical_skill)
                break
    return found


def parse_salary(job: dict) -> tuple[Optional[float], Optional[float], bool]:
    """Extract salary fields, flagging whether Adzuna predicted them."""
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    is_predicted = bool(job.get("salary_is_predicted", "0") in ("1", 1, True))
    return salary_min, salary_max, is_predicted


def clean_location(job: dict) -> str:
    """Adzuna nests location as {'display_name': ...}; flatten it."""
    loc = job.get("location", {})
    if isinstance(loc, dict):
        return loc.get("display_name", "unknown")
    return str(loc) if loc else "unknown"


def transform_records(raw_jobs: list[dict]) -> pd.DataFrame:
    """Turn a list of raw Adzuna job dicts into a clean DataFrame."""
    rows = []
    for job in raw_jobs:
        description = job.get("description", "") or ""
        salary_min, salary_max, salary_predicted = parse_salary(job)

        rows.append({
            "job_id": job.get("id"),
            "title": job.get("title", "").strip(),
            "company": (job.get("company") or {}).get("display_name", "unknown"),
            "location": clean_location(job),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_is_predicted": salary_predicted,
            "posted_date": job.get("created"),
            "description": description,
            "skills": ",".join(extract_skills(description)),
            "redirect_url": job.get("redirect_url"),
            "query_country": job.get("_query_country"),
            "query_keyword": job.get("_query_keyword"),
            "fetched_at": job.get("_fetched_at"),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        logger.warning("No rows to transform.")
        return df

    before = len(df)
    df = df.drop_duplicates(subset=["job_id"], keep="first")
    logger.info("Deduped %d -> %d rows (%d duplicates removed)",
                before, len(df), before - len(df))

    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")

    return df


def transform_file(raw_path: str) -> pd.DataFrame:
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_jobs = json.load(f)
    logger.info("Loaded %d raw postings from %s", len(raw_jobs), raw_path)
    return transform_records(raw_jobs)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transform.py <path_to_raw_json>")
        sys.exit(1)

    df = transform_file(sys.argv[1])
    out_path = Path(sys.argv[1]).with_suffix(".clean.csv")
    df.to_csv(out_path, index=False)
    logger.info("Wrote cleaned data to %s", out_path)
