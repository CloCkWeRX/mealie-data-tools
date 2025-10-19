import os
import asyncio
import re
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

CATEGORY_MAP = {
    "dinner": "Dinner",
    "lunch": "Lunch",
    "breakfast": "Breakfast",
}

async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching categories and recipes from Mealie…")

        all_categories = {cat.name: cat for cat in await client.categories.get_all()}

        # Check if target categories exist
        for cat_name in CATEGORY_MAP.values():
            if cat_name not in all_categories:
                print(f"❌ Category '{cat_name}' not found in Mealie. Please create it.")
                return

        all_recipes = await client.recipes.get_all(per_page=1000)
        print(f"Found {len(all_recipes)} recipes.\n")

        for recipe_summary in all_recipes:
            recipe = await client.recipes.get(recipe_summary.id)

            text_to_search = f"{recipe.name} {recipe.description} {' '.join(tag.name for tag in recipe.tags)}".lower()

            updated = False
            for keyword, category_name in CATEGORY_MAP.items():
                if re.search(fr'\b{keyword}\b', text_to_search, re.IGNORECASE):
                    category_to_add = all_categories[category_name]
                    if not any(cat.id == category_to_add.id for cat in recipe.recipeCategory):
                        print(f"'{recipe.name}' contains '{keyword}', adding '{category_name}' category.")
                        recipe.recipeCategory.append(category_to_add)
                        updated = True

            if updated:
                await client.recipes.update(recipe.id, recipe)

if __name__ == "__main__":
    asyncio.run(main())
