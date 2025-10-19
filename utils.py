from typing import AsyncGenerator, TypeVar
from mealie_client.client import MealieClient
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


async def get_all_paginated(
    endpoint, **kwargs
) -> AsyncGenerator[T, None]:
    page = 1
    per_page = kwargs.pop("per_page", 50)
    while True:
        page_data = await endpoint(page=page, per_page=per_page, **kwargs)
        for item in page_data.items:
            yield item

        if page_data.total_pages <= page:
            break

        page += 1
