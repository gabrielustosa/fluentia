from __future__ import annotations

from typing import Generic, Sequence, Type, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T', bound='BaseModel')


# taken from: https://github.com/uriyyo/fastapi-pagination/blob/main/fastapi_pagination/bases.py
class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    next_page: str = Field(examples=['https://example.com/?page=3&size=50'])
    previous_page: str | None = Field(
        examples=['https://example.com/?page=1&size=50'], defualt=None
    )

    @classmethod
    def create(
        cls: Type[Page[T]],
        items: Sequence[T],
        total: int,
        next_page: str,
        previous_page: str | None,
    ) -> Page[T]:
        return cls(
            items=items,
            total=total,
            next_page=next_page,
            previous_page=previous_page,
        )
