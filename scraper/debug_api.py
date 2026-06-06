"""
Debug script - inspect what the job details API actually returns
"""
import requests
import pandas as pd
import json

HEADERS = {"X-API-Key": "jobboerse-jobsuche"}

# Load a real job ID from our data
df = pd.read_csv("data/jobs_raw.csv")
sample_id = df['job_id'].dropna().iloc[0]
print(f"Testing with job ID: {sample_id}")

# Hit the API
url = f"https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/{sample_id}"
response = requests.get(url, headers=HEADERS)

print(f"Status: {response.status_code}")
print(f"\nAll available fields:")
data = response.json()
for key, value in data.items():
    preview = str(value)[:80] if value else "empty"
    print(f"  {key}: {preview}")

print(f"\nFull response (first 2000 chars):")
print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])