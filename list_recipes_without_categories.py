import asyncio
from mealie_client import MealieClient
from common import BASE_URL, API_TOKEN


async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching recipes from Mealie…")

        page = 1
        while page == 1 or len(all_recipes) == 100:
            all_recipes = await client.recipes.get_all(per_page=100, page=page)
            page = page + 1
            print(f"Found {len(all_recipes)} recipes.\n")

            for recipe_summary in all_recipes:
                recipe = await client.recipes.get(recipe_summary.id)

                if len(recipe.recipe_category) == 0:
                    print(
                        f"{recipe.name} ({BASE_URL}/g/home/r/{recipe.slug}) has no categories"
                    )


if __name__ == "__main__":
    asyncio.run(main())
