import os
import asyncio
from mealie_client import MealieClient
from mealie_client.models.food import FoodUpdateRequest
from dotenv import load_dotenv
from SPARQLWrapper import SPARQLWrapper, JSON

load_dotenv()

# ============ CONFIGURATION ============
BASE_URL = os.getenv("MEALIE_URL")
API_TOKEN = os.getenv("API_TOKEN")

if not BASE_URL or not API_TOKEN:
    print("❌ Missing environment variables: MEALIE_URL and/or API_TOKEN")
    exit(1)
# ======================================

def get_wikidata_aliases(food_name):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setReturnFormat(JSON)

    # In Wikidata, 'spice' is Q42527 and 'food ingredient' is Q25403900
    # We'll search for items that are an instance of either of these classes
    query = f"""
    SELECT ?alias WHERE {{
      ?item rdfs:label "{food_name}"@en .
      ?item skos:altLabel ?alias .
      FILTER(LANG(?alias) = "en")
      {{ ?item (wdt:P31/(wdt:P279*)) wd:Q42527 . }} # Instance of spice or subclass of spice
      UNION
      {{ ?item (wdt:P31/(wdt:P279*)) wd:Q25403900 . }} # Instance of food ingredient or subclass of food ingredient
    }}
    """
    sparql.setQuery(query)

    try:
        results = sparql.query().convert()
        aliases = [result["alias"]["value"] for result in results["results"]["bindings"]]
        return aliases
    except Exception as e:
        print(f"  Error querying Wikidata for '{food_name}': {e}")
        return []

async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching all foods from Mealie…")

        all_foods_list = await client.foods.get_all()
        all_foods_dict = {food.name: food for food in all_foods_list}

        print(f"Found {len(all_foods_dict)} foods to process.\n")

        for food in all_foods_list:
            if food.name not in all_foods_dict:
                continue

            if len(food.aliases) == 0:
                print(f"'{food.name}' has no aliases. Searching Wikidata...")

                aliases = get_wikidata_aliases(food.name)

                if aliases:
                    print(f"  Found aliases on Wikidata: {', '.join(aliases)}")
                    for alias_name in aliases:
                        if alias_name != food.name:
                            food.aliases.append(alias_name)
                            print(f"    Creating new food for alias '{alias_name}'...")
                            updated_food = FoodUpdateRequest(
                                name=food.name,
                                pluralName=food.pluralName,
                                description=food.description,
                                extra=food.extras,
                                labelId=food.labelId,
                                aliases=food.aliases,
                                householdsWithIngredientFood=food.householdsWithIngredientFood,
                                label=food.label
                            )
                            await client.foods.update(food_id=food.id, food=updated_food)
                else:
                    print("  No aliases found on Wikidata.")

if __name__ == "__main__":
    asyncio.run(main())
