import asyncio
import re
from mealie_client import MealieClient
from mealie_client.models.common import RecipeTag
from common import BASE_URL, API_TOKEN

MEAT_FISH_KEYWORDS: list[str] = [
    "anchovy", "bacon", "bass", "beef", "brisket", "chicken", "clam",
    "cod", "crab", "duck", "fish", "goat", "goose", "ham", "lamb",
    "lobster", "mackerel", "mussel", "mutton", "octopus", "oxtail",
    "oyster", "pork", "prawn", "rabbit", "salmon", "sardine",
    "sausage", "scallop", "shrimp", "snapper", "steak", "tilapia",
    "trout", "tuna", "turkey", "veal", "venison",
]
_MEAT_FISH_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(kw) for kw in MEAT_FISH_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def has_meat_or_fish(recipe) -> bool:
    name = getattr(recipe, "name", "") or ""
    if _MEAT_FISH_RE.search(name):
        return True

    description = getattr(recipe, "description", "") or ""
    if description and _MEAT_FISH_RE.search(description):
        return True

    ingredients = getattr(recipe, "recipeIngredient", [])
    for ing in ingredients:
        food = ing.get("food")
        if isinstance(food, dict):
            food_name = (food.get("name") or "")
            if food_name and _MEAT_FISH_RE.search(food_name):
                return True

        text = (ing.get("text") or "")
        if text and _MEAT_FISH_RE.search(text):
            return True

        original_text = (ing.get("originalText") or "")
        if original_text and _MEAT_FISH_RE.search(original_text):
            return True

    return False


async def main():
    async with MealieClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        print("Fetching tags from Mealie…")
        veg_tag: RecipeTag | None = None
        page = 1
        while True:
            tags_response = await client.get(
                "organizers/tags", params={"page": page, "perPage": 50}
            )
            if isinstance(tags_response, dict) and "items" in tags_response:
                tags_data = tags_response["items"]
            elif isinstance(tags_response, list):
                tags_data = tags_response
            else:
                tags_data = []

            for t in tags_data:
                tag = RecipeTag.from_dict(t) if isinstance(t, dict) else t
                if tag.name.lower() == "vegetarian":
                    veg_tag = tag
                    break

            if veg_tag is not None:
                break

            total_pages = (
                tags_response.get("total_pages", 0) if isinstance(tags_response, dict) else 1
            )
            if page >= total_pages:
                break
            page += 1

        if veg_tag is None:
            print(
                "❌ 'Vegetarian' tag not found in Mealie. "
                "Create it first under Organizer > Tags."
            )
            return

        print("Fetching recipes from Mealie…")
        all_recipes: list = []
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
            already_tagged = any(
                t.name.lower() == "vegetarian" for t in recipe.tags
            )
            if already_tagged:
                continue

            if has_meat_or_fish(recipe):
                continue

            print(f"'{recipe.name}' appears vegetarian. Tagging…")
            recipe.tags.append(veg_tag)
            await client.patch(
                f"recipes/{recipe.id}",
                json_data={"tags": [t.to_dict() for t in recipe.tags]},
            )
            updated_count += 1

        print(f"\nDone. Tagged {updated_count} recipes as Vegetarian.")


if __name__ == "__main__":
    asyncio.run(main())
