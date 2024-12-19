import requests
import sqlite3

BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
API_KEY = "8klfCdIFNWMpGFmhohEHQrh2atotz3o0yuxYOx7F"

def search_food_in_cache(query):
    conn = sqlite3.connect('site.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT food_name, calories, protein, carbs, fat FROM foods WHERE food_name LIKE ? LIMIT 10", ('%' + query + '%',))
    results = cursor.fetchall()
    
    conn.close()
    
    # Convert the tuples into dictionaries that mimic the USDA API structure
    foods = []
    for food in results:
        food_dict = {
            'description': food[0],
            'foodNutrients': [
                {'nutrientName': 'Protein', 'value': food[2]},
                {'nutrientName': 'Total lipid (fat)', 'value': food[4]},
                {'nutrientName': 'Carbohydrate, by difference', 'value': food[3]},
                {'nutrientName': 'Energy', 'value': food[1]}
            ]
        }
        foods.append(food_dict)
    
    return foods




def search_food_in_usda_api(query, limit=10):
    """
    Search for a food item in the USDA API.
    query --> search query in API
    limit --> limit of searches
    """
    params = {
        "query": query,
        "api_key": API_KEY,
        "limit": limit
    }
    
    response = requests.get(BASE_URL, params=params)

    data = response.json()
    
    # Check and return foods if they exist in the API response
    if data.get("foods"):
        return data["foods"][:10]
    else:
        return print("Error, API didn't load foods")
    return []



def search_and_fetch_food(query, limit=10):
    
    """
    query --> searches query string
    limit --> results fetched from API
    """

    cached_results = search_food_in_cache(query)
    
    if cached_results:
        return cached_results
    
    api_results = search_food_in_usda_api(query)
     
    return api_results


def save_to_cache(food_details, athlete_id=None):
    """
    Save the food details to the local cache (database).
    food_details: The food details obtained from the USDA API.
    athlete_id: Optional. The ID of the athlete who added the food (if applicable).
    """
    conn = sqlite3.connect('site.db')
    cursor = conn.cursor()
    
    # Extract values directly from food_details
    food_name = food_details.get('food_name', '')
    calories = float(food_details.get('calories', 0.0))
    protein = float(food_details.get('protein', 0.0))
    carbs = float(food_details.get('carbs', 0.0))
    fat = float(food_details.get('fats', 0.0))

    # Print extracted values for debugging
    print(f"Food Name: {food_name}")
    print(f"Calories: {calories}")
    print(f"Protein: {protein}")
    print(f"Carbs: {carbs}")
    print(f"Fat: {fat}")

    cursor.execute("""
        INSERT INTO foods (food_name, calories, protein, carbs, fat, created_by_athlete_id) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (food_name, calories, protein, carbs, fat, athlete_id))
    
    conn.commit()
    conn.close()
