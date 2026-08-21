"""
Streamlit dashboard for the job market ETL project.

Run with:
    streamlit run dashboard.py
"""

import sqlite3
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

import config

st.set_page_config(page_title="Data Analyst Job Market Tracker", layout="wide")


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(config.DB_PATH)
    df = pd.read_sql("SELECT * FROM jobs", conn)
    conn.close()
    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
    return df


st.title("Data Analyst Job Market Tracker")
st.caption(
    "Automated ETL pipeline pulling live postings from the Adzuna API — "
    "tracking in-demand skills, salary ranges, and posting trends so job "
    "seekers don't have to manually scan job boards."
)

df = load_data()

if df.empty:
    st.warning(
        "No data yet. Run `python pipeline.py` at least once to populate "
        "the database."
    )
    st.stop()

# --- Top-level metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total postings tracked", len(df))
col2.metric("Companies", df["company"].nunique())
col3.metric("Countries", df["query_country"].nunique())

st.divider()

# --- Skills demand ---
st.subheader("Most requested skills")
all_skills = []
for skills_str in df["skills"].dropna():
    all_skills.extend([s for s in skills_str.split(",") if s])
skill_counts = Counter(all_skills)

if skill_counts:
    skills_df = pd.DataFrame(
        skill_counts.most_common(15), columns=["skill", "count"]
    )
    fig = px.bar(skills_df, x="count", y="skill", orientation="h",
                 title="Top 15 skills mentioned in postings")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No skills extracted yet.")

st.divider()

# --- Salary distribution ---
st.subheader("Salary distribution")
salary_df = df.dropna(subset=["salary_min", "salary_max"])
if not salary_df.empty:
    salary_df = salary_df.assign(
        salary_mid=(salary_df["salary_min"] + salary_df["salary_max"]) / 2
    )
    fig = px.histogram(salary_df, x="salary_mid", nbins=30,
                        title="Distribution of estimated midpoint salary")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"{salary_df['salary_is_predicted'].mean() * 100:.0f}% of shown "
        "salaries are Adzuna-predicted rather than employer-stated."
    )
else:
    st.info("No salary data available yet.")

st.divider()

# --- Posting volume over time ---
st.subheader("Posting volume over time")
volume_df = df.dropna(subset=["posted_date"]).copy()
if not volume_df.empty:
    volume_df["date"] = volume_df["posted_date"].dt.date
    daily_counts = volume_df.groupby("date").size().reset_index(name="postings")
    fig = px.line(daily_counts, x="date", y="postings",
                  title="Postings per day")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No dated postings available yet.")

st.divider()

# --- Raw table ---
with st.expander("Browse raw postings"):
    st.dataframe(
        df[["title", "company", "location", "salary_min", "salary_max",
            "skills", "posted_date", "redirect_url"]],
        use_container_width=True,
    )
