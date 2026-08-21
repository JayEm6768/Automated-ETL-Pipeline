"""
Extract step of the ETL pipeline.

Pulls job postings from the Adzuna API for each (keyword, country) pair
defined in config.py, and saves the raw JSON responses to disk, one file
per run. Raw storage lets you re-run the transform step later without
re-hitting the API (important given the 1,000 calls/month free-tier cap).

Usage:
    python extract.py
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_page(country: str, keyword: str, page: int) -> dict:
    """Fetch a single page of results from the Adzuna API."""
    url = f"{config.ADZUNA_BASE_URL}/{country}/search/{page}"
    params = {
        "app_id": config.ADZUNA_APP_ID,
        "app_key": config.ADZUNA_APP_KEY,
        "what": keyword,
        "results_per_page": config.RESULTS_PER_PAGE,
        "content-type": "application/json",
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def extract_all() -> Path:
    """
    Loop over configured countries/keywords/pages, fetch results, and
    write them to a single timestamped raw JSON file.

    Returns the path to the file written.
    """
    if not config.ADZUNA_APP_ID or not config.ADZUNA_APP_KEY:
        raise RuntimeError(
            "Missing Adzuna credentials. Set ADZUNA_APP_ID and ADZUNA_APP_KEY "
            "in a .env file (see .env.example)."
        )

    Path(config.RAW_DATA_DIR).mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    all_results = []
    call_count = 0

    for country in config.COUNTRIES:
        for keyword in config.KEYWORDS:
            for page in range(1, config.MAX_PAGES_PER_KEYWORD + 1):
                logger.info(
                    "Fetching country=%s keyword=%r page=%d", country, keyword, page
                )
                try:
                    payload = fetch_page(country, keyword, page)
                except requests.exceptions.HTTPError as e:
                    logger.error(
                        "Request failed (country=%s, keyword=%r, page=%d): %s",
                        country, keyword, page, e,
                    )
                    continue
                call_count += 1

                results = payload.get("results", [])
                if not results:
                    logger.info("No more results, stopping pagination for this keyword.")
                    break

                for job in results:
                    job["_query_country"] = country
                    job["_query_keyword"] = keyword
                    job["_fetched_at"] = run_timestamp
                all_results.extend(results)

                # Be polite to the API even though the free tier is
                # low-volume enough that this rarely matters.
                time.sleep(0.5)

    out_path = Path(config.RAW_DATA_DIR) / f"jobs_raw_{run_timestamp}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    logger.info(
        "Done. %d postings fetched across %d API calls. Saved to %s",
        len(all_results), call_count, out_path,
    )
    return out_path


if __name__ == "__main__":
    extract_all()
