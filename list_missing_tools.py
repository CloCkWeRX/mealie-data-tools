import asyncio
import re
from mealie_client import MealieClient
from common import BASE_URL, API_TOKEN


async def has_missing_tools(recipe) -> bool:
    """
    Check if the given recipe object has no tools listed.
    """
    return len(recipe.tools) == 0


async def find_tool_mentions(recipe) -> list[str]:
    """
    Search for tool-related keywords (oven, grill, fry) in recipe steps.
    Returns a list of matched phrases or empty list.
    """
    matches = []
    for step in recipe.recipeInstructions:
        text = step["text"]

        if not text:
            continue

        found = re.findall(
            r"(skillet|wok|blend|food processor|bake|oven|grill|broil|fry(?:ing)?)",
            text,
            re.IGNORECASE,
        )

        if found:
            # Keep a record of which word matched and where
            matches.append(f"{', '.join(set(found))}: {text.strip()}")
    return matches


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
                missing_tools = await has_missing_tools(recipe)
                tool_mentions = await find_tool_mentions(recipe)

                if missing_tools and tool_mentions:
                    print(
                        f"{recipe_summary.name} ({BASE_URL}/g/home/r/{recipe_summary.slug}) missing tools"
                    )
                    for match in tool_mentions:
                        print(f"   ↳ {match}")


if __name__ == "__main__":
    asyncio.run(main())
