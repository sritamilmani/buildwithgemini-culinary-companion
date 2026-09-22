"""External recipe search tool for Culinary Companion using TheMealDB public API."""

import json
import os
import requests

THEMEALDB_API_KEY = os.environ.get("THEMEALDB_API_KEY", "1")
BASE_URL = f"https://www.themealdb.com/api/json/v1/{THEMEALDB_API_KEY}"


def search_external_recipes(query: str) -> str:
    """Search for real recipes, cooking instructions, and ingredients from TheMealDB public database.
    
    Args:
        query: Recipe or meal name to search for (e.g. 'Risotto', 'Chicken', 'Pasta', 'Curry').
        
    Returns:
        JSON string listing matching external recipes with instructions and ingredients.
    """
    clean_query = query.strip()
    if not clean_query:
        return json.dumps({"status": "error", "message": "Query parameter cannot be empty."})
        
    try:
        url = f"{BASE_URL}/search.php?s={clean_query}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        meals = data.get("meals")
        if not meals:
            return json.dumps({"status": "not_found", "message": f"No external recipes found for '{clean_query}'."})
            
        recipes = []
        for meal in meals[:3]:  # Top 3 matches
            # Parse ingredients and measures
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                meas = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    ingredients.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())
                    
            recipes.append({
                "meal_id": meal.get("idMeal"),
                "name": meal.get("strMeal"),
                "category": meal.get("strCategory"),
                "area": meal.get("strArea"),
                "instructions": meal.get("strInstructions"),
                "ingredients": ingredients,
                "thumbnail": meal.get("strMealThumb"),
                "youtube": meal.get("strYoutube"),
            })
            
        return json.dumps({"status": "success", "count": len(recipes), "recipes": recipes}, indent=2)
    except Exception as err:
        return json.dumps({"status": "error", "message": f"Failed to fetch recipes from external API: {str(err)}"})
