import os
import asyncio
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


async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching recipes from Mealie…")

        all_recipes = await client.recipes.get_all(per_page=1000)
        print(f"Found {len(all_recipes)} recipes.\n")

        for recipe_summary in all_recipes:
            recipe = await client.recipes.get(recipe_summary.id)

            if len(recipe.recipe_category) == 0:
                print(
                    f"{recipe.name} ({BASE_URL}/g/home/r/{recipe.slug}) has no categories"
                )


if __name__ == "__main__":
    asyncio.run(main())
