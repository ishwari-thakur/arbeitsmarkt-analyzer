"""
Arbeitsmarkt Analyzer - Streamlit Dashboard
Author: Ishwari Thakur
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Arbeitsmarkt Analyzer 🇩🇪",
    page_icon="🇩🇪",
    layout="wide"
)

# ─── Load Data ────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data/jobs_raw.csv")
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

# ─── Job Listings Table ───────────────────────────────────
st.markdown("---")
st.subheader("📋 Job Listings")
st.dataframe(
    filtered_df[['title', 'company', 'location', 'region', 'posted_date', 'apply_url']],
    use_container_width=True,
    hide_index=True
)