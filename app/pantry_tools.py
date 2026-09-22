"""Firestore pantry management tools for Culinary Companion agent."""

import json
from google.cloud import firestore

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-f55cf09067a8"

_db = None


def get_firestore_client() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    return _db


def get_pantry_items(category: str = "") -> str:
    """Retrieve pantry items from the Firestore pantry_inventory collection.
    
    Args:
        category: Optional category filter (e.g. 'Produce', 'Grains', 'Dairy', 'Pantry').
        
    Returns:
        JSON string listing pantry items and their quantities.
    """
    db = get_firestore_client()
    collection_ref = db.collection("pantry_inventory")
    
    if category:
        docs = collection_ref.where("category", "==", category).stream()
    else:
        docs = collection_ref.stream()
        
    items = []
    for doc in docs:
        data = doc.to_dict()
        data["doc_id"] = doc.id
        items.append(data)
        
    if not items:
        return json.dumps({"status": "empty", "message": "No pantry items found matching the query.", "items": []})
        
    return json.dumps({"status": "success", "count": len(items), "items": items}, indent=2)


def add_pantry_item(item_name: str, quantity: str, category: str = "Pantry", notes: str = "") -> str:
    """Add or update an item in the Firestore pantry_inventory collection.
    
    Args:
        item_name: Name of the pantry item (e.g. 'Tomatoes', 'Flour').
        quantity: Amount available (e.g. '200g', '2 cans', '1 bag').
        category: Food category (e.g. 'Produce', 'Grains', 'Dairy', 'Pantry').
        notes: Optional extra notes or culinary details.
        
    Returns:
        JSON status message confirming item addition/update.
    """
    db = get_firestore_client()
    doc_id = item_name.strip().lower().replace(" ", "_")
    doc_ref = db.collection("pantry_inventory").document(doc_id)
    
    item_data = {
        "item_name": item_name.strip(),
        "quantity": quantity.strip(),
        "category": category.strip(),
        "notes": notes.strip(),
    }
    
    doc_ref.set(item_data)
    return json.dumps({"status": "success", "message": f"Successfully saved '{item_name}' to pantry inventory.", "item": item_data})


def remove_pantry_item(item_name: str) -> str:
    """Remove an item from the Firestore pantry_inventory collection.
    
    Args:
        item_name: Name of the item to remove (e.g. 'Garlic').
        
    Returns:
        JSON status message.
    """
    db = get_firestore_client()
    doc_id = item_name.strip().lower().replace(" ", "_")
    doc_ref = db.collection("pantry_inventory").document(doc_id)
    
    if not doc_ref.get().exists:
        return json.dumps({"status": "not_found", "message": f"Item '{item_name}' was not found in pantry inventory."})
        
    doc_ref.delete()
    return json.dumps({"status": "success", "message": f"Successfully removed '{item_name}' from pantry inventory."})
