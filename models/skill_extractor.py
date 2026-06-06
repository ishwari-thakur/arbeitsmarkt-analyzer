"""
Arbeitsmarkt Analyzer - Phase 3
NLP Skill Extractor
Author: Ishwari Thakur
"""

import spacy
import pandas as pd
from collections import Counter
import json

# Load German spaCy model
nlp = spacy.load("de_core_news_sm")

# ─── German Tech Skills Taxonomy ──────────────────────────
SKILLS_TAXONOMY = {
    "Programming Languages": [
        "python", "r", "scala", "java", "javascript", "sql",
        "c++", "julia", "matlab", "sas"
    ],
    "ML & AI Frameworks": [
        "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost",
        "lightgbm", "huggingface", "spacy", "nltk", "transformers"
    ],
    "Data & Analytics": [
        "pandas", "numpy", "spark", "hadoop", "hive", "kafka",
        "airflow", "dbt", "tableau", "power bi", "excel"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "mlflow",
        "git", "fastapi", "flask", "rest api"
    ],
    "Data Science Skills": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "statistik", "regression", "clustering", "neural network",
        "time series", "data mining", "feature engineering"
    ],
    "Soft Skills (German)": [
        "teamarbeit", "kommunikation", "projektmanagement",
        "analytisches denken", "selbstständig", "agile", "scrum"
    ]
}

# Flatten all skills for quick lookup
ALL_SKILLS = {
    skill.lower(): category
    for category, skills in SKILLS_TAXONOMY.items()
    for skill in skills
}


# ─── Extract skills from text ─────────────────────────────
def extract_skills(text):
    """
    Extracts skills from a text string using spaCy + taxonomy matching.
    Returns dict of found skills by category.
    """
    if not text or pd.isna(text):
        return {}

    text_lower = text.lower()
    doc = nlp(text_lower)

    found_skills = {}

    # Method 1: Direct keyword matching from taxonomy
    for skill, category in ALL_SKILLS.items():
        if skill in text_lower:
            if category not in found_skills:
                found_skills[category] = []
            if skill not in found_skills[category]:
                found_skills[category].append(skill)

    # Method 2: spaCy Named Entity Recognition
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "MISC"]:
            ent_text = ent.text.lower()
            if ent_text in ALL_SKILLS:
                category = ALL_SKILLS[ent_text]
                if category not in found_skills:
                    found_skills[category] = []
                if ent_text not in found_skills[category]:
                    found_skills[category].append(ent_text)

    return found_skills


# ─── Predict skills from job title ────────────────────────
def predict_skills_from_title(title):
    """
    Predicts likely skills based on job title.
    Uses rule-based logic for common German job titles.
    """
    title_lower = title.lower() if title else ""

    predicted = {}

    if "data scientist" in title_lower:
        predicted = {
            "Programming Languages": ["python", "r", "sql"],
            "ML & AI Frameworks": ["scikit-learn", "tensorflow", "pytorch"],
            "Data & Analytics": ["pandas", "numpy", "tableau"],
            "Data Science Skills": ["machine learning", "statistik", "deep learning"]
        }
    elif "data engineer" in title_lower:
        predicted = {
            "Programming Languages": ["python", "sql", "scala"],
            "Data & Analytics": ["spark", "kafka", "airflow", "hadoop"],
            "Cloud & DevOps": ["aws", "docker", "git"]
        }
    elif "ml engineer" in title_lower or "machine learning" in title_lower:
        predicted = {
            "Programming Languages": ["python", "scala"],
            "ML & AI Frameworks": ["tensorflow", "pytorch", "mlflow"],
            "Cloud & DevOps": ["docker", "kubernetes", "aws"]
        }
    elif "informatiker" in title_lower or "softwareentwickler" in title_lower:
        predicted = {
            "Programming Languages": ["java", "python", "sql"],
            "Cloud & DevOps": ["git", "docker", "rest api"]
        }
    elif "statistiker" in title_lower or "statistik" in title_lower:
        predicted = {
            "Programming Languages": ["r", "python", "sas"],
            "Data Science Skills": ["statistik", "regression", "time series"]
        }
    elif "datenbankentwickler" in title_lower:
        predicted = {
            "Programming Languages": ["sql"],
            "Data & Analytics": ["power bi", "tableau"]
        }

    return predicted


# ─── Process full dataset ─────────────────────────────────
def process_dataset(input_file="data/jobs_raw.csv",
                    output_file="data/jobs_with_skills.csv"):
    """
    Processes all jobs and adds predicted skills column.
    """
    df = pd.read_csv(input_file)
    print(f"Processing {len(df)} jobs...\n")

    all_skills_list = []
    skill_counts = Counter()

    for _, row in df.iterrows():
        # Combine title for analysis
        text = f"{row.get('title', '')} {row.get('company', '')}"

        # Extract from text + predict from title
        extracted = extract_skills(text)
        predicted = predict_skills_from_title(row.get('title', ''))

        # Merge both
        combined = {}
        for d in [extracted, predicted]:
            for category, skills in d.items():
                if category not in combined:
                    combined[category] = []
                for s in skills:
                    if s not in combined[category]:
                        combined[category].append(s)

        all_skills_list.append(json.dumps(combined, ensure_ascii=False))

        # Count individual skills for analysis
        for skills in combined.values():
            for skill in skills:
                skill_counts[skill] += 1

    df['skills'] = all_skills_list
    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"✅ Saved to {output_file}")
    print(f"\n🔝 Top 15 most demanded skills in Germany:")
    for skill, count in skill_counts.most_common(15):
        bar = "█" * count
        print(f"  {skill:<25} {bar} ({count})")

    return df, skill_counts


if __name__ == "__main__":
    print("🧠 Arbeitsmarkt Analyzer — NLP Skill Extractor\n")
    df, skill_counts = process_dataset()