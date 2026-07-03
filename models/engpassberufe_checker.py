"""
Arbeitsmarkt Analyzer - Engpassberufe Checker
Checks if a job role is on Germany's official shortage occupation list
Source: Bundesagentur für Arbeit - Engpassanalyse 2024
Author: Ishwari Thakur
"""

# ─── Official German Shortage Occupations ─────────────────
# Source: BA Engpassanalyse 2024
# https://statistik.arbeitsagentur.de/engpassanalyse

ENGPASSBERUFE = {
    "IT & Data": [
        "data scientist",
        "data engineer",
        "machine learning engineer",
        "software engineer",
        "softwareentwickler",
        "informatiker",
        "it-sicherheit",
        "cybersecurity",
        "fachinformatiker",
        "systemintegration",
        "anwendungsentwicklung",
        "it-projektleiter",
        "devops",
        "cloud architect",
        "data analyst",
    ],
    "Engineering": [
        "maschinenbauingenieur",
        "elektroingenieur",
        "mechatroniker",
        "verfahrenstechniker",
        "bauingenieur",
        "umweltingenieur",
        "energietechniker",
        "automatisierungstechniker",
    ],
    "Healthcare": [
        "krankenpfleger",
        "altenpfleger",
        "arzt",
        "physiotherapeut",
        "ergotherapeut",
        "hebamme",
        "medizinischer fachangestellter",
        "rettungssanitäter",
    ],
    "Skilled Trades": [
        "elektriker",
        "klempner",
        "sanitär",
        "heizungstechniker",
        "kfz-mechatroniker",
        "zimmermann",
        "dachdecker",
        "anlagenmechaniker",
    ],
    "Mathematics & Science": [
        "mathematiker",
        "statistiker",
        "physiker",
        "chemiker",
        "biologe",
        "ozeanograf",
    ]
}

# Visa thresholds (2024 values)
EU_BLUE_CARD_SALARY = 45300  # EUR/year minimum for shortage occupations
STANDARD_BLUE_CARD_SALARY = 58400  # EUR/year for non-shortage

# Flatten for quick lookup
ALL_ENGPASSBERUFE = {
    role.lower(): category
    for category, roles in ENGPASSBERUFE.items()
    for role in roles
}


def check_engpassberuf(title, salary=None):
    """
    Checks if a job title is a shortage occupation.
    Returns detailed eligibility information.
    """
    title_lower = title.lower() if title else ""

    # Check direct match
    matched_category = None
    matched_role = None

    for role, category in ALL_ENGPASSBERUFE.items():
        if role in title_lower:
            matched_category = category
            matched_role = role
            break

    is_engpass = matched_category is not None

    result = {
        "title": title,
        "is_engpassberuf": is_engpass,
        "category": matched_category if is_engpass else None,
        "matched_role": matched_role if is_engpass else None,
        "eu_blue_card_eligible": False,
        "chancenkarte_points": 0,
        "visa_info": "",
        "badge": ""
    }

    if is_engpass:
        result["badge"] = "🔴 Engpassberuf"
        result["chancenkarte_points"] = 2  # bonus points for shortage occupation

        if salary:
            if salary >= EU_BLUE_CARD_SALARY:
                result["eu_blue_card_eligible"] = True
                result["visa_info"] = (
                    f"✅ EU Blue Card eligible — shortage occupation "
                    f"threshold is €{EU_BLUE_CARD_SALARY:,}/year. "
                    f"Your predicted salary qualifies."
                )
            else:
                result["visa_info"] = (
                    f"⚠️ Salary below EU Blue Card threshold "
                    f"(€{EU_BLUE_CARD_SALARY:,}/year for shortage occupations). "
                    f"Consider negotiating salary."
                )
        else:
            result["visa_info"] = (
                f"This role is a shortage occupation. "
                f"EU Blue Card threshold: €{EU_BLUE_CARD_SALARY:,}/year. "
                f"Chancenkarte bonus: +{result['chancenkarte_points']} points."
            )
    else:
        result["badge"] = "⚪ Standard occupation"
        result["visa_info"] = (
            f"Not on shortage occupation list. "
            f"Standard EU Blue Card threshold: €{STANDARD_BLUE_CARD_SALARY:,}/year."
        )

    return result


def process_dataset(input_file="data/jobs_final.csv",
                    output_file="data/jobs_complete.csv"):
    """
    Adds Engpassberufe information to all jobs in the dataset.
    """
    import pandas as pd
    import json

    df = pd.read_csv(input_file)
    print(f"Processing {len(df)} jobs for Engpassberufe status...\n")

    engpass_results = []
    engpass_count = 0

    for _, row in df.iterrows():
        result = check_engpassberuf(
            row.get('title', ''),
            row.get('predicted_mid', None)
        )
        engpass_results.append(json.dumps(result, ensure_ascii=False))
        if result['is_engpassberuf']:
            engpass_count += 1

    df['engpassberufe_info'] = engpass_results
    df['is_engpassberuf'] = [
        json.loads(r)['is_engpassberuf'] for r in engpass_results
    ]

    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"✅ Saved to {output_file}")
    print(f"\n📊 Engpassberufe Summary:")
    print(f"   Total jobs: {len(df)}")
    print(f"   Shortage occupations: {engpass_count} ({engpass_count/len(df)*100:.1f}%)")
    print(f"   Standard occupations: {len(df) - engpass_count}")

    return df


if __name__ == "__main__":
    print("🔴 Arbeitsmarkt Analyzer — Engpassberufe Checker\n")

    # Test cases
    test_jobs = [
        ("Data Scientist", 72000),
        ("Software Engineer", 65000),
        ("Krankenpfleger", 38000),
        ("Marketing Manager", 55000),
        ("Maschinenbauingenieur", 58000),
        ("Informatiker/in", 52000),
    ]

    print("Sample checks:")
    for title, salary in test_jobs:
        result = check_engpassberuf(title, salary)
        print(f"\n  {title} (€{salary:,}/year)")
        print(f"  {result['badge']}")
        print(f"  {result['visa_info']}")

    # Process full dataset
    print("\n" + "="*50)
    process_dataset()