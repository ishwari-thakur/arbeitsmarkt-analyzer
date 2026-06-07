"""
Arbeitsmarkt Analyzer - Phase 4
Salary Predictor Model using XGBoost
Author: Ishwari Thakur
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import pickle
import os

# ─── German Salary Benchmarks ─────────────────────────────
# Based on publicly available German salary data (Gehalt.de, StepStone Gehaltsreport)
ROLE_SALARY_MAP = {
    "data scientist": {"min": 55000, "mid": 72000, "max": 95000},
    "data engineer": {"min": 58000, "mid": 75000, "max": 98000},
    "ml engineer": {"min": 60000, "mid": 78000, "max": 105000},
    "machine learning": {"min": 60000, "mid": 78000, "max": 105000},
    "informatiker": {"min": 45000, "mid": 58000, "max": 78000},
    "softwareentwickler": {"min": 48000, "mid": 62000, "max": 82000},
    "statistiker": {"min": 42000, "mid": 55000, "max": 72000},
    "datenbankentwickler": {"min": 44000, "mid": 57000, "max": 74000},
    "ozeanograf": {"min": 38000, "mid": 48000, "max": 62000},
    "mathematiker": {"min": 45000, "mid": 58000, "max": 76000},
    "physiker": {"min": 48000, "mid": 62000, "max": 82000},
    "betriebswirt": {"min": 40000, "mid": 52000, "max": 68000},
    "default": {"min": 42000, "mid": 55000, "max": 72000}
}

# Regional salary multipliers (based on cost of living)
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

# Company tier multipliers
COMPANY_TIERS = {
    "tier1": {  # DAX companies
        "companies": ["bmw", "siemens", "volkswagen", "sap", "deutsche telekom",
                     "allianz", "basf", "bayer", "bosch", "mercedes"],
        "multiplier": 1.20
    },
    "tier2": {  # Large German companies
        "companies": ["vodafone", "rewe", "deichmann", "huk-coburg",
                     "zalando", "dhl", "lufthansa", "commerzbank"],
        "multiplier": 1.10
    },
    "tier3": {  # Consulting/Staffing
        "companies": ["hays", "ferchau", "akkodis", "constaff", "dis ag"],
        "multiplier": 0.95
    }
}


# ─── Feature Engineering ──────────────────────────────────
def get_role_salary(title):
    """Maps job title to base salary range."""
    title_lower = title.lower() if title else ""
    for role, salary in ROLE_SALARY_MAP.items():
        if role in title_lower:
            return salary
    return ROLE_SALARY_MAP["default"]

def get_region_multiplier(region):
    """Returns salary multiplier for a German region."""
    return REGION_MULTIPLIER.get(region, 1.00)

def get_company_multiplier(company):
    """Returns salary multiplier based on company tier."""
    company_lower = company.lower() if company else ""
    for tier, data in COMPANY_TIERS.items():
        for c in data["companies"]:
            if c in company_lower:
                return data["multiplier"]
    return 1.00

def engineer_features(df):
    """
    Creates feature matrix from job listings.
    This is the core ML feature engineering step.
    """
    features = []

    for _, row in df.iterrows():
        title = row.get('title', '')
        region = row.get('region', 'Unknown')
        company = row.get('company', '')

        # Get base salary for this role
        base_salary = get_role_salary(title)
        region_mult = get_region_multiplier(region)
        company_mult = get_company_multiplier(company)

        # Calculate predicted salary
        predicted_mid = base_salary["mid"] * region_mult * company_mult
        predicted_min = base_salary["min"] * region_mult * company_mult
        predicted_max = base_salary["max"] * region_mult * company_mult

        features.append({
            "title": title,
            "company": company,
            "region": region,
            "base_mid_salary": base_salary["mid"],
            "region_multiplier": region_mult,
            "company_multiplier": company_mult,
            "predicted_min": round(predicted_min),
            "predicted_mid": round(predicted_mid),
            "predicted_max": round(predicted_max),
            "salary_label": f"€{round(predicted_min/1000)}k - €{round(predicted_max/1000)}k"
        })

    return pd.DataFrame(features)


# ─── Train XGBoost Model ──────────────────────────────────
def train_model(df_features):
    """
    Trains an XGBoost regression model on engineered features.
    """
    print("Training XGBoost salary prediction model...")

    # Encode categorical features
    le_region = LabelEncoder()
    le_title = LabelEncoder()

    df_features['region_encoded'] = le_region.fit_transform(
        df_features['region'].fillna('Unknown')
    )
    df_features['title_encoded'] = le_title.fit_transform(
        df_features['title'].fillna('Unknown')
    )

    # Feature matrix
    X = df_features[[
        'region_encoded',
        'title_encoded',
        'region_multiplier',
        'company_multiplier',
        'base_mid_salary'
    ]]
    y = df_features['predicted_mid']

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train XGBoost
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\n📊 Model Performance:")
    print(f"   MAE (Mean Absolute Error): €{mae:,.0f}")
    print(f"   R² Score: {r2:.3f}")

    # Save model and encoders
    os.makedirs("models", exist_ok=True)
    with open("models/salary_model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open("models/label_encoders.pkl", "wb") as f:
        pickle.dump({"region": le_region, "title": le_title}, f)

    print(f"\n✅ Model saved to models/salary_model.pkl")
    return model, le_region, le_title


# ─── Predict salary for a single job ──────────────────────
def predict_salary(title, region, company="Unknown"):
    """
    Predicts salary range for a given job.
    """
    base = get_role_salary(title)
    region_mult = get_region_multiplier(region)
    company_mult = get_company_multiplier(company)

    predicted_min = round(base["min"] * region_mult * company_mult)
    predicted_max = round(base["max"] * region_mult * company_mult)
    predicted_mid = round(base["mid"] * region_mult * company_mult)

    return {
        "min": predicted_min,
        "mid": predicted_mid,
        "max": predicted_max,
        "label": f"€{round(predicted_min/1000)}k - €{round(predicted_max/1000)}k",
        "region_factor": region_mult,
        "company_factor": company_mult
    }


# ─── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("💰 Arbeitsmarkt Analyzer — Salary Predictor\n")

    # Load data
    df = pd.read_csv("data/jobs_with_skills.csv")
    df['region'] = df['region'].fillna('Unknown')

    # Engineer features
    print("Engineering features...")
    df_features = engineer_features(df)

    # Add salary predictions back to main dataframe
    df['predicted_min'] = df_features['predicted_min'].values
    df['predicted_max'] = df_features['predicted_max'].values
    df['salary_label'] = df_features['salary_label'].values

    # Train model
    model, le_region, le_title = train_model(df_features)

    # Save enriched dataset
    df.to_csv("data/jobs_final.csv", index=False)
    print(f"\n✅ Final dataset saved to data/jobs_final.csv")

    # Sample predictions
    print("\n🔮 Sample Salary Predictions:")
    test_cases = [
        ("Data Scientist", "Bayern", "BMW Group"),
        ("Data Scientist", "Berlin", "Zalando SE"),
        ("Data Scientist", "Baden-Württemberg", "SAP"),
        ("Data Engineer", "Hamburg", "Unknown"),
        ("Informatiker/in", "Nordrhein-Westfalen", "Unknown"),
    ]

    for title, region, company in test_cases:
        result = predict_salary(title, region, company)
        print(f"  {title} | {region} | {company}")
        print(f"  → {result['label']} (mid: €{result['mid']:,})\n")