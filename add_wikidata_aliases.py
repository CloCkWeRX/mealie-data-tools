import os
import asyncio
from mealie_client import MealieClient
from dotenv import load_dotenv
from wikidata.client import Client as WikidataClient

load_dotenv()

# ============ CONFIGURATION ============
BASE_URL = os.getenv("MEALIE_URL")
API_TOKEN = os.getenv("API_TOKEN")

if not BASE_URL or not API_TOKEN:
    print("❌ Missing environment variables: MEALIE_URL and/or API_TOKEN")
    exit(1)
# ======================================


async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching all foods from Mealie…")

        all_foods_list = await client.foods.get_all()
        # Create a dictionary for quick lookups and state management
        all_foods_dict = {food.name: food for food in all_foods_list}

        print(f"Found {len(all_foods_dict)} foods to process.\n")

        wikidata_client = WikidataClient()

        # Iterate over a static copy of the food list, as we'll be modifying the dictionary
        for food in all_foods_list:
            # If the food we are about to process was already merged as an alias, it will no longer be in our dict.
            if food.name not in all_foods_dict:
                continue

            # In Mealie, aliases are just other Food objects linked together.
            # We look for foods that don't have any other foods linked as aliases.
            if not food.alias:
                print(f"'{food.name}' has no aliases. Searching Wikidata...")

                try:
                    # Search for the food item on Wikidata
                    entity = wikidata_client.get(
                        food.name, load=True, type="item", language="en"
                    )
                    aliases = entity.data.get("aliases", {}).get("en", [])

                    if aliases:
                        print(
                            f"  Found aliases on Wikidata: {', '.join(a['value'] for a in aliases)}"
                        )
                        for alias_data in aliases:
                            alias_name = alias_data["value"]

                            # Check if the alias food already exists in our current state
                            alias_food = all_foods_dict.get(alias_name)

                            if not alias_food:
                                print(
                                    f"    Creating new food for alias '{alias_name}'..."
                                )
                                alias_food = await client.foods.create(name=alias_name)
                                # Add the new food to our dictionary for future lookups
                                all_foods_dict[alias_name] = alias_food

                            print(f"    Merging '{alias_name}' into '{food.name}'...")
                            await client.foods.merge(food.id, alias_food.id)

                            # Remove the merged food from our dictionary to prevent trying to use it again
                            if alias_name in all_foods_dict:
                                del all_foods_dict[alias_name]
                    else:
                        print("  No aliases found on Wikidata.")
                except Exception as e:
                    print(
                        f"  Could not find '{food.name}' on Wikidata or an error occurred: {e}"
                    )


if __name__ == "__main__":
    asyncio.run(main())
