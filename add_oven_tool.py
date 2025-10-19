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

async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching recipes from Mealie…")

        all_recipes = await client.recipes.get_all(per_page=1000)
        print(f"Found {len(all_recipes)} recipes.\n")

        tools = {tool.name: tool for tool in await client.tools.get_all()}
        oven_tool = tools.get("Oven")

        if not oven_tool:
            print("❌ 'Oven' tool not found in Mealie. Please create it.")
            return

        for recipe_summary in all_recipes:
            recipe = await client.recipes.get(recipe_summary.id)

            tool_mentions_oven = False
            for step in recipe.recipeInstructions:
                text = step.get('text', '')
                if text and re.search(r'\boven\b', text, re.IGNORECASE):
                    tool_mentions_oven = True
                    break

            if tool_mentions_oven:
                if not any(tool.id == oven_tool.id for tool in recipe.tools):
                    print(f"'{recipe.name}' mentions 'oven' but is missing the 'Oven' tool. Adding it now...")
                    recipe.tools.append(oven_tool)
                    await client.recipes.update(recipe.id, recipe)


if __name__ == "__main__":
    asyncio.run(main())
