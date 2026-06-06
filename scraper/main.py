"""
Arbeitsmarkt Analyzer - Phase 1
Job Scraper using Bundesagentur für Arbeit Official API
Author: Ishwari Thakur
"""

import requests
import pandas as pd
from datetime import datetime
import time

# ─── Configuration ────────────────────────────────────────
BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"

HEADERS = {
    "X-API-Key": "jobboerse-jobsuche",
    "Content-Type": "application/json"
}

SEARCH_KEYWORD = "Data Scientist"
MAX_PAGES = 5

# ─── Step 1: Fetch jobs from official API ─────────────────
def fetch_jobs(keyword, max_pages=5):
    """
    Fetches job listings from Bundesagentur für Arbeit API.
    Returns a list of raw job dictionaries.
    """
    all_jobs = []

    for page in range(1, max_pages + 1):
        params = {
            "was": keyword,
            "wo": "Deutschland",
            "page": page,
            "size": 25
        }

        print(f"Fetching page {page}...")

        response = requests.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code != 200:
            print(f"Error on page {page}. Status: {response.status_code}")
            break

        data = response.json()
        jobs = data.get("stellenangebote", [])

        if not jobs:
            print(f"No more jobs found at page {page}")
            break

        print(f"Found {len(jobs)} jobs on page {page}")

        for job in jobs:
            parsed = parse_job(job)
            all_jobs.append(parsed)

        time.sleep(1)

    return all_jobs


# ─── Step 2: Parse each job ───────────────────────────────
def parse_job(job):
    """
    Extracts relevant fields from a single job listing.
    """
    return {
        "title": job.get("beruf", "N/A"),
        "company": job.get("arbeitgeber", "N/A"),
        "location": job.get("arbeitsort", {}).get("ort", "N/A"),
        "region": job.get("arbeitsort", {}).get("region", "N/A"),
        "employment_type": job.get("arbeitszeitmodelle", "N/A"),
        "posted_date": job.get("eintrittsdatum", "N/A"),
        "job_id": job.get("hashId", "N/A"),
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# ─── Step 3: Save to CSV ──────────────────────────────────
def save_to_csv(jobs, filename="data/jobs_raw.csv"):
    """
    Saves the list of jobs to a CSV file using pandas.
    """
    if not jobs:
        print("No jobs to save.")
        return

    df = pd.DataFrame(jobs)
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"\n✅ Saved {len(df)} jobs to {filename}")
    print(f"\nFirst 5 jobs:")
    print(df.head())
    print(f"\nColumns: {list(df.columns)}")
    print(f"Total records: {len(df)}")


# ─── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("🇩🇪 Arbeitsmarkt Analyzer — Starting job scraper...\n")
    jobs = fetch_jobs(SEARCH_KEYWORD, MAX_PAGES)
    print(f"\nTotal jobs fetched: {len(jobs)}")
    save_to_csv(jobs)