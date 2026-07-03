"""
Arbeitsmarkt Analyzer - Language Reality Score
Detects real German language requirement from job title and company context
Unlike job board filters, this gives the REAL language level required
Author: Ishwari Thakur
"""

# ─── Language Level Indicators ────────────────────────────

# Companies known to work primarily in English
ENGLISH_FRIENDLY_COMPANIES = [
    "zalando", "n26", "delivery hero", "hellofresh", "auto1",
    "idealo", "wework", "twitter", "google", "amazon", "microsoft",
    "apple", "meta", "linkedin", "booking", "airbnb", "spotify",
    "vodafone", "sap", "siemens", "bmw", "mercedes", "bosch",
    "bayer", "basf", "adidas", "puma", "wirecard", "teamviewer",
    "celonis", "personio", "forto", "hays", "akkodis", "constaff"
]

# Companies/sectors that strongly require German
GERMAN_REQUIRED_INDICATORS = [
    "krankenhaus", "klinik", "pflege", "behörde", "amt", "stadtwerk",
    "sparkasse", "volksbank", "versicherung", "steuer", "rechts",
    "öffentlich", "bundesamt", "landesamt", "kommunal", "sozial",
    "handwerk", "bäcker", "metzger", "friseur", "einzelhandel"
]

# Job title language indicators
ENGLISH_OK_TITLES = [
    "data scientist", "data engineer", "machine learning",
    "software engineer", "developer", "devops", "cloud",
    "ai engineer", "nlp engineer", "research scientist",
    "data analyst", "business intelligence", "bi analyst"
]

GERMAN_REQUIRED_TITLES = [
    "krankenpfleger", "altenpfleger", "erzieher", "lehrer",
    "buchhalter", "steuerberater", "rechtsanwalt", "notar",
    "beamter", "verwaltung", "sozialarbeiter", "kundendienst",
    "verkäufer", "einzelhandel", "handwerker", "elektriker"
]

# Language level definitions
LANGUAGE_LEVELS = {
    "A1": {
        "label": "A1 — Beginner",
        "description": "No German required — English fully sufficient",
        "color": "#2ecc71",
        "emoji": "🟢"
    },
    "A2": {
        "label": "A2 — Elementary",
        "description": "Basic German helpful but not required",
        "color": "#27ae60",
        "emoji": "🟢"
    },
    "B1": {
        "label": "B1 — Intermediate",
        "description": "Basic German needed for daily communication",
        "color": "#f39c12",
        "emoji": "🟡"
    },
    "B2": {
        "label": "B2 — Upper Intermediate",
        "description": "Good German required for professional communication",
        "color": "#e67e22",
        "emoji": "🟠"
    },
    "C1": {
        "label": "C1 — Advanced",
        "description": "Fluent German essential for this role",
        "color": "#e74c3c",
        "emoji": "🔴"
    },
    "C2": {
        "label": "C2 — Native Level",
        "description": "Native or near-native German required",
        "color": "#c0392b",
        "emoji": "🔴"
    }
}


def detect_language_requirement(title, company, region=None):
    """
    Detects real German language requirement based on:
    1. Job title
    2. Company name
    3. Region (some regions more English-friendly)
    Returns language level with explanation.
    """
    title_lower = title.lower() if title else ""
    company_lower = company.lower() if company else ""
    region = region or "Unknown"

    score = 0  # Higher = more German required
    reasons = []

    # Check company
    is_english_company = any(
        c in company_lower for c in ENGLISH_FRIENDLY_COMPANIES
    )
    is_german_sector = any(
        g in company_lower for g in GERMAN_REQUIRED_INDICATORS
    )

    if is_english_company:
        score -= 2
        reasons.append(f"Company ({company}) is known to work in English")
    if is_german_sector:
        score += 3
        reasons.append(f"Company sector typically requires German")

    # Check job title
    is_english_title = any(t in title_lower for t in ENGLISH_OK_TITLES)
    is_german_title = any(t in title_lower for t in GERMAN_REQUIRED_TITLES)

    if is_english_title:
        score -= 1
        reasons.append(f"Role type ({title}) commonly uses English internationally")
    if is_german_title:
        score += 3
        reasons.append(f"Role type typically requires German")

    # Region factor
    if region in ["Berlin", "Hamburg", "Bayern"]:
        score -= 1
        reasons.append(f"{region} has high concentration of English-speaking workplaces")
    elif region in ["Sachsen", "Thüringen", "Brandenburg"]:
        score += 1
        reasons.append(f"{region} workplaces tend to use German more")

    # Determine level based on score
    if score <= -3:
        level = "A1"
    elif score <= -1:
        level = "A2"
    elif score <= 1:
        level = "B1"
    elif score <= 3:
        level = "B2"
    elif score <= 5:
        level = "C1"
    else:
        level = "C2"

    level_info = LANGUAGE_LEVELS[level]

    return {
        "title": title,
        "company": company,
        "region": region,
        "language_level": level,
        "label": level_info["label"],
        "description": level_info["description"],
        "emoji": level_info["emoji"],
        "score": score,
        "reasons": reasons,
        "international_friendly": score <= 0
    }


def process_dataset(input_file="data/jobs_complete.csv",
                    output_file="data/jobs_complete.csv"):
    """
    Adds language requirement scores to all jobs.
    """
    import pandas as pd
    import json

    df = pd.read_csv(input_file)
    print(f"Detecting language requirements for {len(df)} jobs...\n")

    language_results = []
    level_counts = {}

    for _, row in df.iterrows():
        result = detect_language_requirement(
            row.get('title', ''),
            row.get('company', ''),
            row.get('region', 'Unknown')
        )
        language_results.append(json.dumps(result, ensure_ascii=False))

        level = result['language_level']
        level_counts[level] = level_counts.get(level, 0) + 1

    df['language_info'] = language_results
    df['language_level'] = [
        json.loads(r)['language_level'] for r in language_results
    ]
    df['international_friendly'] = [
        json.loads(r)['international_friendly'] for r in language_results
    ]

    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"✅ Saved to {output_file}")
    print(f"\n🇩🇪 Language Requirements Summary:")
    for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        count = level_counts.get(level, 0)
        info = LANGUAGE_LEVELS[level]
        bar = "█" * count
        print(f"  {info['emoji']} {level}: {bar} ({count} jobs)")

    international = sum(
        1 for r in language_results
        if json.loads(r)['international_friendly']
    )
    print(f"\n  🌍 International friendly jobs: {international}/{len(df)} ({international/len(df)*100:.1f}%)")

    return df


if __name__ == "__main__":
    print("🇩🇪 Arbeitsmarkt Analyzer — Language Reality Score\n")

    # Test cases
    test_jobs = [
        ("Data Scientist", "BMW Group", "Bayern"),
        ("Data Scientist", "Zalando SE", "Berlin"),
        ("Krankenpfleger", "Städtisches Klinikum", "Nordrhein-Westfalen"),
        ("Software Engineer", "SAP", "Baden-Württemberg"),
        ("Buchhalter", "Sparkasse", "Sachsen"),
        ("Data Engineer", "Vodafone GmbH", "Nordrhein-Westfalen"),
    ]

    print("Sample language requirement checks:")
    for title, company, region in test_jobs:
        result = detect_language_requirement(title, company, region)
        print(f"\n  {title} @ {company} ({region})")
        print(f"  {result['emoji']} {result['label']}")
        print(f"  → {result['description']}")
        if result['reasons']:
            print(f"  Why: {result['reasons'][0]}")

    print("\n" + "="*50)
    process_dataset()