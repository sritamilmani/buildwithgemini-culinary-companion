"""Seed Firestore with initial pantry inventory data for Culinary Companion."""

import time
from google.cloud import firestore
from google.api_core.exceptions import GoogleAPICallError

PROJECT_ID = "qwiklabs-gcp-03-f55cf09067a8"

SEED_PANTRY_ITEMS = [
    {
        "item_name": "Arborio Rice",
        "quantity": "500g",
        "category": "Grains",
        "notes": "Ideal for Mushroom Risotto",
    },
    {
        "item_name": "Parmesan Cheese",
        "quantity": "250g",
        "category": "Dairy",
        "notes": "Aged 24 months, freshly block",
    },
    {
        "item_name": "Garlic",
        "quantity": "1 head",
        "category": "Produce",
        "notes": "Fresh organic garlic",
    },
    {
        "item_name": "Extra Virgin Olive Oil",
        "quantity": "750ml",
        "category": "Pantry",
        "notes": "Cold pressed",
    },
    {
        "item_name": "Cremini Mushrooms",
        "quantity": "300g",
        "category": "Produce",
        "notes": "Cleaned and whole",
    },
    {
        "item_name": "Vegetable Broth",
        "quantity": "1 Liter",
        "category": "Pantry",
        "notes": "Low sodium",
    },
]


def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("pantry_inventory")

    print("Seeding pantry items into Firestore...")
    for item in SEED_PANTRY_ITEMS:
        doc_id = item["item_name"].lower().replace(" ", "_")
        doc_ref = collection_ref.document(doc_id)
        
        # Retry logic for eventual IAM propagation
        for attempt in range(5):
            try:
                doc_ref.set(item)
                print(f"  [+] Added: {item['item_name']} ({item['quantity']})")
                break
            except GoogleAPICallError as e:
                if attempt == 4:
                    raise e
                time.sleep(2)

    print("\n✅ Firestore database successfully seeded!")


if __name__ == "__main__":
    seed_database()
