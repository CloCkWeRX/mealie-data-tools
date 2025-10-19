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


async def has_unparsed_ingredients(recipe: dict) -> bool:
    """
    Check if the given recipe dict contains any ingredients
    whose parsed fields are missing or incomplete.
    """
    for ingredient in recipe.recipeIngredient:
        if ingredient.get("food") is not None:
            return False
    return True


async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching recipes from Mealie…")

        page = 1
        while page == 1 or len(all_recipes) == 100:
            all_recipes = await client.recipes.get_all(per_page=100, page=page)
            page = page + 1
            print(f"Found {len(all_recipes)} recipes.")

            for recipe_summary in all_recipes:
                recipe_id = recipe_summary.id
                recipe_name = recipe_summary.name
                recipe = await client.recipes.get(recipe_id)

                if await has_unparsed_ingredients(recipe):
                    print(
                        f"❗ {recipe_name} (ID: {BASE_URL}/g/home/r/{recipe_summary.slug}) has unparsed ingredients"
                    )


if __name__ == "__main__":
    asyncio.run(main())
