"""
Arbeitsmarkt Analyzer - CV Match Score
Free alternative to LinkedIn Premium job matching
Uses sentence-transformers for semantic similarity
Author: Ishwari Thakur
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import json
import os

# Load sentence transformer model
print("Loading sentence transformer model...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("✅ Model loaded!")

# ─── Extract text from CV PDF ─────────────────────────────
def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a CV PDF file.
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + " "
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def extract_text_from_string(text):
    """
    Cleans and returns text directly.
    """
    return text.strip()


# ─── Build job descriptions from our data ─────────────────
def build_job_text(row):
    """
    Creates a rich text representation of a job for embedding.
    """
    parts = []

    title = row.get('title', '')
    company = row.get('company', '')
    location = row.get('location', '')
    region = row.get('region', '')

    if title:
        parts.append(f"Job Title: {title}")
    if company:
        parts.append(f"Company: {company}")
    if location:
        parts.append(f"Location: {location}, {region}")

    # Add skills if available
    skills_json = row.get('skills', '{}')
    try:
        skills_dict = json.loads(skills_json)
        all_skills = []
        for category, skills in skills_dict.items():
            all_skills.extend(skills)
        if all_skills:
            parts.append(f"Required Skills: {', '.join(all_skills)}")
    except:
        pass

    return " | ".join(parts)


# ─── Match CV against jobs ─────────────────────────────────
def match_cv_to_jobs(cv_text, df, top_n=10):
    """
    Matches CV text against all job listings.
    Returns top N matches with similarity scores.
    """
    print(f"\nMatching your CV against {len(df)} jobs...")

    # Build job texts
    job_texts = [build_job_text(row) for _, row in df.iterrows()]

    # Generate embeddings
    print("Generating CV embedding...")
    cv_embedding = model.encode([cv_text])

    print("Generating job embeddings...")
    job_embeddings = model.encode(job_texts, show_progress_bar=True)

    # Calculate cosine similarity
    similarities = cosine_similarity(cv_embedding, job_embeddings)[0]

    # Add scores to dataframe
    df_results = df.copy()
    df_results['match_score'] = similarities
    df_results['match_percentage'] = (similarities * 100).round(1)

    # Sort by match score
    df_results = df_results.sort_values(
        'match_score', ascending=False
    ).head(top_n)

    return df_results


# ─── Display results ──────────────────────────────────────
def display_matches(matches):
    """
    Displays match results in a clean format.
    """
    print(f"\n{'='*60}")
    print("🎯 TOP JOB MATCHES FOR YOUR CV")
    print(f"{'='*60}\n")

    for i, (_, row) in enumerate(matches.iterrows(), 1):
        score = row['match_percentage']

        # Score emoji
        if score >= 70:
            emoji = "🟢"
        elif score >= 50:
            emoji = "🟡"
        else:
            emoji = "🔴"

        print(f"{i}. {emoji} {score}% match")
        print(f"   {row['title']} @ {row['company']}")
        print(f"   📍 {row['location']}, {row['region']}")
        print(f"   💰 {row.get('salary_label', 'N/A')}")
        print(f"   🔗 {row.get('apply_url', 'N/A')}")
        print()


# ─── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("📄 Arbeitsmarkt Analyzer — CV Match Score\n")

    # Load jobs
    df = pd.read_csv("data/jobs_complete.csv")
    df['location'] = df['location'].fillna('Unknown')
    df['region'] = df['region'].fillna('Unknown')

    # Sample CV text — replace with your own or load from PDF
    sample_cv = """
    Ishwari Thakur - Data Science & AI Engineer
    Master's student in Applied Data Science and AI at SRH Heidelberg.
    4+ years of software engineering experience.

    Skills: Python, Machine Learning, NLP, Deep Learning, TensorFlow,
    PyTorch, scikit-learn, XGBoost, spaCy, pandas, NumPy, SQL,
    FastAPI, Docker, Git, Streamlit, REST APIs, Node.js

    Experience:
    - Built end-to-end ML pipelines and NLP models
    - Developed data pipelines processing large datasets
    - Deployed AI-powered tools using FastAPI and Docker
    - Designed REST APIs with Node.js reducing processing time by 75%

    Projects:
    - Arbeitsmarkt Analyzer: German job market intelligence tool
      using NLP, XGBoost, spaCy German model
    - AI CEO Strategic Intelligence Agent: RAG system using
      Qwen3, ChromaDB, sentence transformers

    Education: M.Sc. Applied Data Science & AI, SRH Heidelberg
    Languages: English (Fluent), German (A1, improving)
    Location: Mannheim, Germany
    """

    # Match CV
    matches = match_cv_to_jobs(sample_cv, df, top_n=10)

    # Display results
    display_matches(matches)

    # Save results
    matches[['title', 'company', 'location', 'region',
             'match_percentage', 'salary_label', 'apply_url']].to_csv(
        "data/cv_matches.csv", index=False
    )
    print("✅ Results saved to data/cv_matches.csv")