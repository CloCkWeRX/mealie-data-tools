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


def get_wikidata_info(food_name):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setReturnFormat(JSON)

    # Match on label OR alias, and fetch aliases + description
    query = f"""
    SELECT ?item ?alias ?itemDescription WHERE {{
      ?item (rdfs:label|skos:altLabel) "{food_name}"@en .
      FILTER(LANG(?itemDescription) = "en")
      OPTIONAL {{ ?item skos:altLabel ?alias FILTER(LANG(?alias) = "en") }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
      
      {{
        ?item (wdt:P31/(wdt:P279*)) wd:Q42527 .    # spice or subclass
      }} UNION {{
        ?item (wdt:P31/(wdt:P279*)) wd:Q25403900 . # food ingredient or subclass
      }}
    }}
    """
    sparql.setQuery(query)

    try:
        results = sparql.query().convert()
        aliases = set()
        description = None
        for result in results["results"]["bindings"]:
            if "alias" in result:
                aliases.add(result["alias"]["value"])
            if "itemDescription" in result:
                description = result["itemDescription"]["value"]
        return list(aliases), description
    except Exception as e:
        print(f"Error querying Wikidata for '{food_name}': {e}")
        return [], None


async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching all foods from Mealie…")

        all_foods_list = await client.foods.get_all()
        all_foods_dict = {food.name: food for food in all_foods_list}

        print(f"Found {len(all_foods_dict)} foods to process.\n")

        for food in all_foods_list:
            if food.name not in all_foods_dict:
                continue

            aliases, description = get_wikidata_info(food.name)

            updated = False

            # Add aliases if missing
            if aliases:
                existing_alias_names = {a["name"] for a in food.aliases}
                new_aliases = [
                    {"name": alias_name}
                    for alias_name in aliases
                    if alias_name not in existing_alias_names
                    and alias_name != food.name
                ]
                if new_aliases:
                    print(
                        f"  Adding aliases: {', '.join(a['name'] for a in new_aliases)}"
                    )
                    food.aliases.extend(new_aliases)
                    updated = True
            else:
                print("  No aliases found on Wikidata.")

            # Set description if missing
            if not food.description and description:
                print(f"  Setting description from Wikidata: {description}")
                food.description = description
                updated = True

            if updated:
                updated_food = {
                    "name": food.name,
                    "description": food.description,
                    "aliases": food.aliases,
                }
                await client.foods.update(food_id=food.id, food=updated_food)
                print(f"  Updated '{food.name}' successfully.\n")
            else:
                print(f"  No updates required for '{food.name}'.\n")


if __name__ == "__main__":
    asyncio.run(main())
