"""
Orchestrates the full ETL run: extract -> transform -> load.

This is what you'd point a scheduler (cron, Airflow, Prefect) at to run
daily. Kept as a plain script for now; see README.md for how to wrap it
in Airflow later without changing this logic.

Usage:
    python pipeline.py
"""

import logging

from extract import extract_all
from transform import transform_file
from load import load_dataframe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("=== ETL run started ===")

    raw_path = extract_all()
    df = transform_file(str(raw_path))
    rows_loaded = load_dataframe(df)

    logger.info(
        "=== ETL run complete: %d postings loaded into the database ===",
        rows_loaded,
    )


if __name__ == "__main__":
    run_pipeline()
