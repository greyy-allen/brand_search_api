import requests
import itertools
import json
import random

BASE_URL = "http://127.0.0.1:5000/api/brands/search"


categories_list = [
    ["Immune Health"],
    ["Women's Health"],
    ["Beauty"],
    ["Immune Health", "Women's Health"],
    [],
]

market_metrics_options = [
    {"revenue_tier": 8},
    {"market_share_tier": 3},
    {"category_diversity": {"$gte": 10}},
    {"category_diversity_norm": "11.5%"},
    {"revenue_tier": {"$gte": 5}, "market_share_tier": 3},
    {},
]

filters_options = [
    {"target_customers": ["Aging Adults", "Wellness Seekers", "Clean Label Shoppers"]},
    {
        "unique_selling_points": [
            "Clinically Studied",
            "Organic Certified",
            "Oral Health",
        ]
    },
    {
        "core_messaging": [
            "Science-Backed Claims",
            "Bioavailability",
            "Nutrient Support",
        ]
    },
    {
        "social_and_ethical": [
            "Allergen Free",
            "Science-Based Claims",
            "Transparent Labeling",
        ]
    },
    {"strengths": ["Great Taste"]},
    {"strengths": ["Easy to Use"]},
    {"strengths": ["Health Benefits"]},
    {"strengths": ["Great Taste", "Easy to Use"]},
    {"strengths": ["Easy to Use", "Health Benefits"]},
    {"weaknesses": ["Inconsistent Results"]},
    {"weaknesses": ["Side Effects"]},
    {"weaknesses": ["Dosage Confusion"]},
    {"weaknesses": ["Inconsistent Results", "Side Effects"]},
    {"weaknesses": ["Side Effects", "Dosage Confusion"]},
    {},
]


all_combinations = list(
    itertools.product(categories_list, market_metrics_options, filters_options)
)[:10]
random.shuffle(all_combinations)

test_cases = all_combinations[:10]


for i, (categories, market_metrics, filters) in enumerate(test_cases, 1):
    payload = {}

    if categories:
        payload["categories"] = categories
    if market_metrics:
        payload["market_metrics"] = market_metrics
    if filters:
        payload["filters"] = filters

    print(f"\n--- Test Case {i} ---")
    print("Payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(BASE_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"Response ({data['count']} results):")
        for r in data["results"]:
            print(f" - {r['name']} (ID: {r['_id']})")
    except Exception as e:
        print(f"Error: {e}")
