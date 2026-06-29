import asyncio
import re
from mealie_client import MealieClient
from mealie_client.models.common import RecipeCategory, RecipeTag
from common import BASE_URL, API_TOKEN

CATEGORY_MAP = {
    "dinner": "Dinner",
    "lunch": "Lunch",
    "breakfast": "Breakfast",
}


async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching categories from Mealie…")

        categories_response = await client.get("organizers/categories")
        if isinstance(categories_response, dict) and "items" in categories_response:
            categories_data = categories_response["items"]
        elif isinstance(categories_response, list):
            categories_data = categories_response
        else:
            categories_data = []

        all_categories: dict[str, RecipeCategory] = {}
        for c in categories_data:
            cat = RecipeCategory.from_dict(c) if isinstance(c, dict) else c
            all_categories[cat.name] = cat

        for cat_name in CATEGORY_MAP.values():
            if cat_name not in all_categories:
                print(
                    f"❌ Category '{cat_name}' not found in Mealie. Please create it."
                )
                return

        print("Fetching recipes from Mealie…")
        all_recipes = []
        page = 1
        while True:
            batch = await client.recipes.get_all(per_page=100, page=page)
            if not batch:
                break
            all_recipes.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        print(f"Found {len(all_recipes)} recipes.\n")

        updated_count = 0
        for recipe_summary in all_recipes:
            recipe = await client.recipes.get(recipe_summary.id)

            recipe.tags = [
                RecipeTag.from_dict(t) if isinstance(t, dict) else t
                for t in recipe.tags
            ]
            recipe.recipe_category = [
                RecipeCategory.from_dict(c) if isinstance(c, dict) else c
                for c in recipe.recipe_category
            ]

            text_to_search = (
                f"{recipe.name} {recipe.description or ''} "
                f"{' '.join(t.name for t in recipe.tags)}"
            ).lower()

            updated = False
            for keyword, category_name in CATEGORY_MAP.items():
                if re.search(rf"\b{keyword}\b", text_to_search, re.IGNORECASE):
                    category_to_add = all_categories[category_name]
                    if not any(
                        cat.id == category_to_add.id for cat in recipe.recipe_category
                    ):
                        print(
                            f"'{recipe.name}' contains '{keyword}', adding '{category_name}' category."
                        )
                        recipe.recipe_category.append(category_to_add)
                        updated = True

            if updated:
                await client.patch(
                    f"recipes/{recipe.id}",
                    json_data={
                        "recipeCategory": [
                            c.to_dict() for c in recipe.recipe_category
                        ]
                    },
                )
                updated_count += 1

        print(f"\nDone. Updated {updated_count} recipes.")


if __name__ == "__main__":
    asyncio.run(main())
