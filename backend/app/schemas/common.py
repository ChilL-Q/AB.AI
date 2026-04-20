from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):  # noqa: UP046
    data: list[T]
    meta: "PaginationMeta"


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    has_next: bool
