import asyncio
import re
from mealie_client import MealieClient
from mealie_client.models.common import RecipeTag
from common import BASE_URL, API_TOKEN

MEAT_FISH_KEYWORDS: list[str] = [
    "anchovy", "bacon", "bass", "beef", "brisket",
    "catfish", "chicken", "chorizo", "clam", "cod", "crab",
    "duck", "eel", "fish", "goat", "goose", "grouse",
    "haddock", "hake", "halibut", "ham", "herring",
    "kangaroo",
    "lamb", "liver", "lobster", "mackerel", "mussel", "mutton",
    "octopus", "oxtail", "oyster",
    "pancetta", "pastrami", "pâté", "pepperoni", "pheasant",
    "pork", "prawn", "prosciutto", "quail",
    "rabbit", "salami", "salmon", "sardine", "sausage",
    "scallop", "shrimp", "snapper", "steak",
    "tilapia", "trout", "tuna", "turkey",
    "veal", "venison",
    "whiting",
]
_MEAT_FISH_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(kw) for kw in MEAT_FISH_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


_NON_MEAT_FOODS: set[str] = {
    "oyster sauce",
}


def has_meat_or_fish(recipe) -> bool:
    name = getattr(recipe, "name", "") or ""
    if _MEAT_FISH_RE.search(name):
        return True

    ingredients = getattr(recipe, "recipeIngredient", [])
    for ing in ingredients:
        food = ing.get("food")
        if isinstance(food, dict):
            food_name = (food.get("name") or "")
            if food_name and food_name.lower() not in _NON_MEAT_FOODS:
                if _MEAT_FISH_RE.search(food_name):
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

        tagged_count = 0
        untagged_count = 0
        for recipe_summary in all_recipes:
            try:
                recipe = await client.recipes.get(recipe_summary.id)
            except Exception:
                continue

            recipe.tags = [
                RecipeTag.from_dict(t) if isinstance(t, dict) else t
                for t in recipe.tags
            ]
            has_veg_tag = any(
                t.name.lower() == "vegetarian" for t in recipe.tags
            )
            contains_meat = has_meat_or_fish(recipe)

            if not has_veg_tag and not contains_meat:
                print(f"'{recipe.name}' appears vegetarian. Tagging…")
                recipe.tags.append(veg_tag)
                await client.patch(
                    f"recipes/{recipe.id}",
                    json_data={"tags": [t.to_dict() for t in recipe.tags]},
                )
                tagged_count += 1

            elif has_veg_tag and contains_meat:
                print(f"'{recipe.name}' contains meat/fish. Removing Vegetarian tag…")
                recipe.tags = [
                    t for t in recipe.tags if t.name.lower() != "vegetarian"
                ]
                await client.patch(
                    f"recipes/{recipe.id}",
                    json_data={"tags": [t.to_dict() for t in recipe.tags]},
                )
                untagged_count += 1

        parts = []
        if tagged_count:
            parts.append(f"Tagged {tagged_count}")
        if untagged_count:
            parts.append(f"Untagged {untagged_count}")
        print(f"\nDone. {'; '.join(parts)}." if parts else "\nDone. No changes.")


if __name__ == "__main__":
    asyncio.run(main())
