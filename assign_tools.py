import asyncio
import re
from mealie_client import MealieClient
from mealie_client.models.common import RecipeInstruction, RecipeTool
from common import BASE_URL, API_TOKEN

# Maps regex patterns (lowercase) to Mealie tool names
TOOL_KEYWORDS: dict[str, str] = {
    r"\boven\b": "Oven",
    r"\bgrill\b": "Grill",
    r"\bskillet\b": "Frypan",
    r"\bwok\b": "Wok",
    r"\bblend(?:er)?\b": "Blender",
    r"\bfood processor\b": "Food Processor",
    r"\bbake\b": "Oven",
    r"\bbroil\b": "Oven",
    r"\bmicrowave\b": "Microwave",
    r"\bslow cook(?:er)?\b": "Slow Cooker",
    r"\bair fry(?:er|ing)?\b": "Air Fryer",
    r"\binstant pot\b": "Pressure Cooker",
    r"\bstand mixer\b": "Stand Mixer",
    r"\bhand mixer\b": "Hand Mixer",
    r"\bimmersion blender\b": "Immersion Blender",
    r"\btoaster\b": "Toaster",
    r"\btoaster oven\b": "Toaster Oven",
    r"\bdutch oven\b": "Dutch Oven",
    r"\bcrock.?pot\b": "Slow Cooker",
    r"\bstove.?top\b": "Stove",
    r"\bsaucepan\b": "Saucepan",
    r"\bsaut[ée]\b": "Frypan",
    r"\bfry(?:ing)? pan\b": "Frypan",
    r"\bcast iron\b": "Cast Iron Skillet",
    r"\bbaking sheet\b": "Baking Sheet",
    r"\bbaking dish\b": "Baking Dish",
    r"\bmuffin tin\b": "Muffin Tin",
    r"\bloaf pan\b": "Loaf Pan",
    r"\bcake pan\b": "Cake Pan",
    r"\bpie plate\b": "Pie Plate",
    r"\bchef'?s knife\b": "Chef's Knife",
    r"\bcutting board\b": "Cutting Board",
    r"\bmixing bowl\b": "Mixing Bowl",
    r"\brolling pin\b": "Rolling Pin",
    r"\bgrater\b": "Grater",
    r"\bpeeler\b": "Vegetable Peeler",
    r"\bcolander\b": "Colander",
    r"\bstrainer\b": "Strainer",
    r"\bwhisk\b": "Whisk",
    r"\bspatula\b": "Spatula",
    r"\btongs\b": "Tongs",
    r"\bladle\b": "Ladle",
    r"\bmeasuring cup\b": "Measuring Cup",
    r"\bmeasuring spoon\b": "Measuring Spoon",
    r"\bkitchen scale\b": "Kitchen Scale",
    r"\bthermometer\b": "Food Thermometer",
    r"\bdehydrator\b": "Dehydrator",
    r"\bice cream maker\b": "Ice Cream Maker",
    r"\bbread machine\b": "Bread Machine",
    r"\bpasta maker\b": "Pasta Maker",
    r"\bmandoline\b": "Mandoline",
    r"\bzester\b": "Zester",
    r"\bjuicer\b": "Juicer",
    r"\bpressure cooker\b": "Pressure Cooker",
    r"\brice cooker\b": "Rice Cooker",
    r"\bsous vide\b": "Sous Vide",
}


def find_matching_tools(
    recipe_tool_names: set[str],
    instruction_text: str,
    recipe_name: str,
) -> set[str]:
    matched = set()
    text_to_search = f"{recipe_name} {instruction_text}".lower()

    for pattern, tool_name in TOOL_KEYWORDS.items():
        if re.search(pattern, text_to_search, re.IGNORECASE):
            matched.add(tool_name)

    return matched - recipe_tool_names


async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching tools from Mealie…")
        tools_response = await client.get("organizers/tools")
        if isinstance(tools_response, dict) and "items" in tools_response:
            tools_data = tools_response["items"]
        elif isinstance(tools_response, list):
            tools_data = tools_response
        else:
            tools_data = []

        available_tools: dict[str, RecipeTool] = {}
        for t in tools_data:
            tool = RecipeTool.from_dict(t) if isinstance(t, dict) else t
            available_tools[tool.name.lower()] = tool

        print(f"Found {len(available_tools)} tools in Mealie.\n")

        print("Fetching recipes from Mealie…")
        all_recipes = await client.recipes.get_all(per_page=1000)
        print(f"Found {len(all_recipes)} recipes.\n")

        updated_count = 0
        for recipe_summary in all_recipes:
            recipe = await client.recipes.get(recipe_summary.id)
            recipe.tools = [
                RecipeTool.from_dict(t) if isinstance(t, dict) else t
                for t in recipe.tools
            ]
            existing_tool_names = {t.name for t in recipe.tools}

            recipe.recipeInstructions = [
                RecipeInstruction.from_dict(s) if isinstance(s, dict) else s
                for s in recipe.recipeInstructions
            ]
            instruction_text = " ".join(
                step.text for step in recipe.recipeInstructions if step.text
            )

            matched_names = find_matching_tools(
                existing_tool_names, instruction_text, recipe.name
            )

            if not matched_names:
                continue

            tools_to_add = []
            for name in sorted(matched_names):
                tool = available_tools.get(name.lower())
                if tool is None:
                    print(
                        f"  ⚠ Tool '{name}' not found in Mealie. "
                        f"Create it first under Organizer > Tools."
                    )
                    continue
                tools_to_add.append(tool)

            if not tools_to_add:
                continue

            print(
                f"'{recipe.name}' mentions: "
                f"{', '.join(t.name for t in tools_to_add)}. Adding..."
            )
            all_tools = recipe.tools + tools_to_add
            await client.patch(
                f"recipes/{recipe.id}",
                json_data={"tools": [t.to_dict() for t in all_tools]},
            )
            updated_count += 1

        print(f"\nDone. Updated {updated_count} recipes.")


if __name__ == "__main__":
    asyncio.run(main())
