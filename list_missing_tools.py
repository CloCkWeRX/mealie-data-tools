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
# =========================================

async def has_missing_tools(recipe: dict) -> bool:
    """
    Check if the given recipe dict contains any tools
    """
    return len(recipe.tools) == 0

async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching recipes from Mealie…")

        # Fetch all recipes (the SDK might paginate internally or allow per_page; adjust if needed)
        all_recipes = await client.recipes.get_all(per_page=1000)
        print(f"Found {len(all_recipes)} recipes.")

        for recipe_summary in all_recipes:
            recipe_id = recipe_summary.id  # or recipe_summary.get("id")
            recipe_name = recipe_summary.name  # or .get("name")
            # Fetch full recipe details
            recipe = await client.recipes.get(recipe_id)

            if await has_missing_tools(recipe):
                print(f"❗ {recipe_name} (ID: {BASE_URL}/g/home/r/{recipe_summary.slug}) has missing tools")

if __name__ == "__main__":
    asyncio.run(main())

