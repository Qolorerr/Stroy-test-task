from pydantic import BaseModel


class PostItem(BaseModel):
    tag_ids: list[int]
    content: str
    price: float


class PatchItem(BaseModel):
    tag_ids: list[int] | None = None
    content: str | None = None
    price: float | None = None
