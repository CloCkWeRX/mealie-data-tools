import sys

TOOLS: list[dict[str, str]] = [
    {
        "name": "assign_tools",
        "desc": "Match tool keywords in recipe steps to Mealie tools and assign them",
        "usage": "uv run python3 assign_tools.py",
    },
    {
        "name": "tag_vegetarian",
        "desc": "Tag recipes as Vegetarian when ingredients contain no meat or fish",
        "usage": "uv run python3 tag_vegetarian.py",
    },
    {
        "name": "update_recipe_categories",
        "desc": "Auto-assign Dinner/Lunch/Breakfast categories by keyword matching",
        "usage": "uv run python3 update_recipe_categories.py",
    },
    {
        "name": "list_unparsed_recipes",
        "desc": "Show all recipes with unparsed ingredients (food field is null)",
        "usage": "uv run python3 list_unparsed_recipes.py",
    },
    {
        "name": "list_recipes_without_categories",
        "desc": "Show all recipes that have no categories assigned",
        "usage": "uv run python3 list_recipes_without_categories.py",
    },
    {
        "name": "list_missing_tools",
        "desc": "Show recipes with no tools that mention tool keywords in steps",
        "usage": "uv run python3 list_missing_tools.py",
    },
    {
        "name": "merge_ingredients",
        "desc": "Merge one ingredient into another (makes it an alias)",
        "usage": "uv run python3 merge_ingredients.py <main_food> <alias_food>",
    },
    {
        "name": "add_wikidata_aliases",
        "desc": "Enrich ingredients with aliases and descriptions from Wikidata",
        "usage": "uv run python3 add_wikidata_aliases.py",
    },
]


def main():
    print("mealie-data-tools — Mealie data management scripts\n")
    print(f"{'Script':30s} Description")
    print("-" * 80)
    for tool in TOOLS:
        print(f"{tool['name']:30s} {tool['desc']}")
    print()
    print("Examples:")
    for tool in TOOLS:
        print(f"  {tool['usage']}")
    print()
    print("Set MEALIE_URL and API_TOKEN in .env first.")


if __name__ == "__main__":
    main()
