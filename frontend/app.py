"""
Arbeitsmarkt Analyzer - Streamlit Dashboard
Author: Ishwari Thakur
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import json
from collections import Counter
sys.path.append('.')
from models.salary_predictor import predict_salary
import warnings
warnings.filterwarnings('ignore')

REGION_MULTIPLIER = {
    "Bayern": 1.15,
    "Baden-Württemberg": 1.12,
    "Hamburg": 1.10,
    "Berlin": 1.05,
    "Hessen": 1.08,
    "Nordrhein-Westfalen": 1.02,
    "Niedersachsen": 0.97,
    "Rheinland-Pfalz": 0.96,
    "Schleswig-Holstein": 0.95,
    "Sachsen": 0.90,
    "Thüringen": 0.88,
    "Unknown": 1.00
}

# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Arbeitsmarkt Analyzer 🇩🇪",
    page_icon="🇩🇪",
    layout="wide"
)

# ─── Load Data ────────────────────────────────────────────
@st.cache_resource
def load_data():
    df = pd.read_csv("data/jobs_final.csv")
    df['location'] = df['location'].fillna('Unknown')
    df['region'] = df['region'].fillna('Unknown')
    df['posted_date'] = pd.to_datetime(df['posted_date'], errors='coerce')
    return df

df = load_data()

# ─── Header ───────────────────────────────────────────────
st.title("🇩🇪 Arbeitsmarkt Analyzer")
st.markdown("**German Job Market Intelligence Tool** — Real data from Bundesagentur für Arbeit")
st.markdown("---")

# ─── KPI Row ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs", len(df))
col2.metric("Unique Companies", df['company'].nunique())
col3.metric("Cities Covered", df['location'].nunique())
col4.metric("Regions Covered", df['region'].nunique())

st.markdown("---")

# ─── Sidebar Filters ──────────────────────────────────────
st.sidebar.title("🔍 Filters")
selected_region = st.sidebar.multiselect(
    "Filter by Region",
    options=sorted(df['region'].unique()),
    default=[]
)

search_company = st.sidebar.text_input("Search Company", "")

# Apply filters
filtered_df = df.copy()
if selected_region:
    filtered_df = filtered_df[filtered_df['region'].isin(selected_region)]
if search_company:
    filtered_df = filtered_df[
        filtered_df['company'].str.contains(search_company, case=False, na=False)
    ]

st.sidebar.markdown(f"**Showing {len(filtered_df)} jobs**")

# ─── Charts Row ───────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Top Cities")
    fig, ax = plt.subplots(figsize=(8, 5))
    top_cities = filtered_df['location'].value_counts().head(10)
    sns.barplot(x=top_cities.values, y=top_cities.index, palette='Blues_r', ax=ax)
    ax.set_xlabel("Number of Jobs")
    ax.set_ylabel("")
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("🏢 Top Companies")
    fig, ax = plt.subplots(figsize=(8, 5))
    top_companies = filtered_df['company'].value_counts().head(10)
    sns.barplot(x=top_companies.values, y=top_companies.index, palette='Greens_r', ax=ax)
    ax.set_xlabel("Number of Jobs")
    ax.set_ylabel("")
    plt.tight_layout()
    st.pyplot(fig)

# ─── Region Chart ─────────────────────────────────────────
st.subheader("🗺️ Jobs by Region")
fig, ax = plt.subplots(figsize=(12, 4))
top_regions = filtered_df['region'].value_counts().head(10)
sns.barplot(x=top_regions.index, y=top_regions.values, palette='Blues_r', ax=ax)
ax.set_xlabel("Region")
ax.set_ylabel("Number of Jobs")
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)


# ─── Salary Predictions ───────────────────────────────────
st.markdown("---")
st.subheader("💰 Predicted Salary Ranges by Region")

salary_df = filtered_df.groupby('region').agg(
    avg_min=('predicted_min', 'mean'),
    avg_max=('predicted_max', 'mean'),
    job_count=('title', 'count')
).reset_index().sort_values('avg_min', ascending=False).head(10)

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.barh(salary_df['region'],
               salary_df['avg_max'] - salary_df['avg_min'],
               left=salary_df['avg_min'],
               color='#2ecc71', alpha=0.7, height=0.5)

ax.set_xlabel("Salary Range (€)")
ax.set_ylabel("Region")
ax.xaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f"€{x/1000:.0f}k")
)

for i, row in salary_df.iterrows():
    ax.text(row['avg_max'] + 500, 
            list(salary_df['region']).index(row['region']),
            f"€{row['avg_min']/1000:.0f}k-€{row['avg_max']/1000:.0f}k",
            va='center', fontsize=9)

plt.tight_layout()
st.pyplot(fig)

# Salary calculator
st.markdown("#### 🔮 Salary Calculator")
col1, col2, col3 = st.columns(3)
with col1:
    calc_title = st.selectbox("Job Title", [
        "Data Scientist", "Data Engineer", "ML Engineer",
        "Informatiker/in", "Statistiker/in"
    ])
with col2:
    calc_region = st.selectbox("Region", list(REGION_MULTIPLIER.keys()))
with col3:
    calc_company = st.text_input("Company (optional)", "")

result = predict_salary(calc_title, calc_region, calc_company)
st.success(f"**Predicted Salary: {result['label']}** (mid: €{result['mid']:,}/year)")
st.caption(f"Region factor: {result['region_factor']}x · Company factor: {result['company_factor']}x")


# ─── Skills Analysis ──────────────────────────────────────
st.markdown("---")
st.subheader("🧠 Most Demanded Skills in Germany")

import json
from collections import Counter

skill_counts = Counter()
for skills_json in df['skills'].dropna():
    try:
        skills_dict = json.loads(skills_json)
        for category, skills in skills_dict.items():
            for skill in skills:
                skill_counts[skill] += 1
    except:
        pass

if skill_counts:
    top_skills = pd.DataFrame(
        skill_counts.most_common(15),
        columns=['Skill', 'Count']
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(x='Count', y='Skill', data=top_skills, palette='Purples_r', ax=ax)
    ax.set_xlabel("Number of Jobs Requiring This Skill")
    ax.set_ylabel("")
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("**💡 Insight:** These are the skills German companies are actively hiring for right now.")


# ─── Job Listings Table ───────────────────────────────────
st.markdown("---")
st.subheader("📋 Job Listings")
st.dataframe(
    filtered_df[['title', 'company', 'location', 'region', 'posted_date', 'apply_url']],
    use_container_width=True,
    hide_index=True
)