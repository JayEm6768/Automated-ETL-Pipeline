# Data Analyst Job Market ETL Pipeline

An automated ETL pipeline that tracks the data analyst job market in
real time — pulling live postings from the Adzuna API, extracting
in-demand skills from job descriptions, and surfacing salary/location
trends on a live dashboard.

**The pitch:** job seekers (or a recruiting team) shouldn't have to
manually scan job boards to know what skills are in demand right now.
This pipeline does it for them, on a schedule, automatically.

**Portfolio note:** the pipeline shape here (scheduled extract →
clean/enrich → load → dashboard) is deliberately generic. Swap the
Adzuna extractor for a social media or review API and the same
architecture becomes a real-time brand sentiment tracker for a
marketing team — same skeleton, different source and scoring step.

## Architecture

```
extract.py     -> pulls raw postings from Adzuna API, saves JSON
transform.py   -> cleans fields, extracts skills, dedupes
load.py        -> upserts into SQLite
pipeline.py    -> runs the three steps in sequence
dashboard.py   -> Streamlit dashboard on top of the SQLite DB
config.py      -> API settings, search scope, skills dictionary
```

## Setup

1. **Get a free Adzuna API key** (instant, no approval wait):
   https://developer.adzuna.com/signup — you'll get an `app_id` and
   `app_key`.

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure credentials:**

   ```bash
   cp env.example .env
   # then edit .env and paste in your app_id / app_key
   ```

4. **Run the pipeline once:**

   ```bash
   python pipeline.py
   ```

   This fetches postings, cleans them, extracts skills, and loads
   everything into `data/job_market.db`.

5. **View the dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

## Scheduling it (making it "automated")

For a portfolio demo, running `pipeline.py` via cron is enough to
show automation:

```cron
# Run daily at 7am
0 7 * * * cd /path/to/job_market_etl && /path/to/venv/bin/python pipeline.py >> logs/pipeline.log 2>&1
```

**To level this up for interviews:** wrap `pipeline.py`'s three steps
(`extract_all`, `transform_file`, `load_dataframe`) as individual
Airflow tasks in a DAG. The functions are already separated for this —
you would not need to rewrite the logic, just add an Airflow DAG file
that imports and calls them in order with retry/alerting configured.

## API quota management

Adzuna's free tier is ~1,000 calls/month. With the default config
(2 countries × 3 keywords × 2 pages = 12 calls per run), running
daily uses ~360 calls/month — comfortably under the cap. Adjust
`COUNTRIES`, `KEYWORDS`, and `MAX_PAGES_PER_KEYWORD` in `config.py`
if you want broader coverage, but watch the math.

## Extending this project

- Add a second job source (USAJOBS, Remotive) and a `source` column
  to compare postings across boards
- Track skill trends over time (skills gaining/losing frequency
  week over week) instead of just a current snapshot
- Add alerting (email/Slack) when a new high-salary posting matching
  your target role appears
- Swap in the sentiment-analysis use case described above by pointing
  `extract.py` at a review or social API instead of Adzuna
