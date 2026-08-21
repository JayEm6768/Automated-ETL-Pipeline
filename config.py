"""
Central configuration for the job market ETL pipeline.
Keeps API settings, search parameters, and the skills dictionary
in one place so extract/transform scripts stay clean.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Adzuna API credentials ---
# Get these free at https://developer.adzuna.com/signup
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"

# --- Search scope ---
# Free tier = ~1,000 calls/month. Each (keyword, country, page) combo = 1 call.
# Keep this list small and run once daily to stay well under quota.
COUNTRIES = ["us", "gb"]  # Adzuna country codes: us, gb, au, ca, de, fr, in, etc.

KEYWORDS = [
    "data analyst",
    "data analytics",
    "business intelligence analyst",
]

RESULTS_PER_PAGE = 50   # max allowed by Adzuna
MAX_PAGES_PER_KEYWORD = 2  # 2 pages x 50 = 100 postings per keyword/country/run

# --- Storage paths ---
RAW_DATA_DIR = "data/raw"
DB_PATH = "data/job_market.db"

# --- Skills dictionary for text extraction ---
# Keys are the canonical skill name stored in the DB.
# Values are alternate surface forms to match in the description text.
# Matching is case-insensitive, word-boundary aware (see transform.py).
SKILLS_DICTIONARY = {
    "sql": ["sql", "mysql", "postgresql", "postgres", "t-sql", "pl/sql"],
    "python": ["python"],
    "r": ["r programming", " r,", " r)", " r "],  # 'r' alone is noisy, kept narrow
    "excel": ["excel", "vlookup", "pivot table"],
    "tableau": ["tableau"],
    "power_bi": ["power bi", "powerbi"],
    "looker": ["looker"],
    "spark": ["spark", "pyspark"],
    "hadoop": ["hadoop"],
    "airflow": ["airflow"],
    "dbt": ["dbt"],
    "snowflake": ["snowflake"],
    "bigquery": ["bigquery", "big query"],
    "aws": ["aws", "amazon web services", "redshift", "s3"],
    "azure": ["azure"],
    "gcp": ["gcp", "google cloud"],
    "statistics": ["statistics", "statistical analysis"],
    "machine_learning": ["machine learning", "ml model", "scikit-learn", "sklearn"],
    "etl": ["etl", "data pipeline", "elt"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "git": ["git", "github", "version control"],
    "a_b_testing": ["a/b testing", "ab testing", "experimentation"],
    "data_visualization": ["data visualization", "dashboarding", "dashboards"],
}
