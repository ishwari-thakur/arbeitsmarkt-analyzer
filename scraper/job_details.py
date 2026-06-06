"""
Arbeitsmarkt Analyzer - Phase 3
Job Details Fetcher — gets full description for each job
Author: Ishwari Thakur
"""

import requests
import pandas as pd
import time

HEADERS = {"X-API-Key": "jobboerse-jobsuche"}
DETAIL_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails"

def fetch_job_description(job_id):
    """
    Fetches full job description for a single job using its ID.
    """
    try:
        url = f"{DETAIL_URL}/{job_id}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            # Extract description text
            description = data.get("stellenbeschreibung", "")
            return description
        else:
            return ""
    except Exception as e:
        print(f"Error fetching {job_id}: {e}")
        return ""


def enrich_with_descriptions(input_file="data/jobs_raw.csv",
                              output_file="data/jobs_enriched.csv",
                              limit=50):
    """
    Loads existing jobs CSV and adds full description for each job.
    Limit controls how many jobs to enrich (API calls take time).
    """
    df = pd.read_csv(input_file)

    # Only process jobs with valid job_id
    df_valid = df[df['job_id'].notna()].head(limit).copy()

    print(f"Fetching descriptions for {len(df_valid)} jobs...\n")

    descriptions = []
    for i, (_, row) in enumerate(df_valid.iterrows()):
        job_id = row['job_id']
        print(f"[{i+1}/{len(df_valid)}] Fetching: {row['company']} — {row['title']}")

        desc = fetch_job_description(job_id)
        descriptions.append(desc)
        time.sleep(0.5)

    df_valid['description'] = descriptions

    # Save enriched data
    df_valid.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n✅ Saved enriched data to {output_file}")
    print(f"Jobs with descriptions: {sum(1 for d in descriptions if d)}")

    return df_valid


if __name__ == "__main__":
    enrich_with_descriptions(limit=50)