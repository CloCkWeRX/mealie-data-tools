import os
import asyncio
import argparse
from mealie_client import MealieClient
from dotenv import load_dotenv

load_dotenv()

# ============ CONFIGURATION ============
BASE_URL = os.getenv("MEALIE_URL")
API_TOKEN = os.getenv("API_TOKEN")

if not BASE_URL or not API_TOKEN:
    print("❌ Missing environment variables: MEALIE_URL and/or API_TOKEN")
    exit(1)
# ======================================

async def main(main_food_name: str, alias_food_name: str):
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print(f"Fetching foods from Mealie to merge '{alias_food_name}' into '{main_food_name}'…")

        all_foods = {food.name: food for food in await client.foods.get_all()}

        main_food = all_foods.get(main_food_name)
        alias_food = all_foods.get(alias_food_name)

        if not main_food:
            print(f"❌ Main food '{main_food_name}' not found.")
            return

        if not alias_food:
            print(f"❌ Alias food '{alias_food_name}' not found.")
            return

        print(f"Found main food '{main_food.name}' (ID: {main_food.id})")
        print(f"Found alias food '{alias_food.name}' (ID: {alias_food.id})")

        # In Mealie, you don't add an alias by name, you absorb another food.
        # This will merge the alias_food into the main_food.
        await client.foods.merge(main_food.id, alias_food.id)

        print(f"✅ Successfully merged '{alias_food_name}' into '{main_food_name}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge one ingredient into another in Mealie.")
    parser.add_argument("main_food", help="The name of the ingredient to keep.")
    parser.add_argument("alias_food", help="The name of the ingredient to merge and make an alias.")

    args = parser.parse_args()

    asyncio.run(main(args.main_food, args.alias_food))
