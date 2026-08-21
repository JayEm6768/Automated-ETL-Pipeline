"""
Load step of the ETL pipeline.

Writes a cleaned DataFrame (from transform.py) into a SQLite database.
Uses an upsert-style approach keyed on job_id so re-running the pipeline
doesn't create duplicate rows.

Usage:
    python load.py data/raw/jobs_raw_<timestamp>.clean.csv
"""

import logging
import sqlite3
import sys
from pathlib import Path

import pandas as pd

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id              TEXT PRIMARY KEY,
    title               TEXT,
    company             TEXT,
    location            TEXT,
    salary_min          REAL,
    salary_max          REAL,
    salary_is_predicted INTEGER,
    posted_date         TEXT,
    description         TEXT,
    skills              TEXT,
    redirect_url        TEXT,
    query_country       TEXT,
    query_keyword       TEXT,
    fetched_at          TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_query_keyword ON jobs(query_keyword);
"""


def get_connection() -> sqlite3.Connection:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.executescript(SCHEMA)
    return conn


def load_dataframe(df: pd.DataFrame) -> int:
    """
    Upsert rows into the jobs table. Returns the number of rows written.
    """
    if df.empty:
        logger.warning("Nothing to load, DataFrame is empty.")
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    rows_written = 0
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO jobs (
                job_id, title, company, location, salary_min, salary_max,
                salary_is_predicted, posted_date, description, skills,
                redirect_url, query_country, query_keyword, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                salary_min=excluded.salary_min,
                salary_max=excluded.salary_max,
                salary_is_predicted=excluded.salary_is_predicted,
                posted_date=excluded.posted_date,
                description=excluded.description,
                skills=excluded.skills,
                redirect_url=excluded.redirect_url,
                query_country=excluded.query_country,
                query_keyword=excluded.query_keyword,
                fetched_at=excluded.fetched_at
            """,
            (
                row["job_id"], row["title"], row["company"], row["location"],
                row["salary_min"], row["salary_max"],
                int(bool(row["salary_is_predicted"])),
                str(row["posted_date"]) if pd.notna(row["posted_date"]) else None,
                row["description"], row["skills"], row["redirect_url"],
                row["query_country"], row["query_keyword"], row["fetched_at"],
            ),
        )
        rows_written += 1

    conn.commit()
    conn.close()
    logger.info("Upserted %d rows into %s", rows_written, config.DB_PATH)
    return rows_written


def load_csv(csv_path: str) -> int:
    df = pd.read_csv(csv_path)
    return load_dataframe(df)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python load.py <path_to_clean_csv>")
        sys.exit(1)

    load_csv(sys.argv[1])
