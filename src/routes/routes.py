from fastapi import FastAPI

from src.handlers.user_handler import router as user_router
from src.handlers.item_handler import router as item_router


def register_routes(app: FastAPI) -> None:
    app.include_router(user_router, prefix="/users", tags=["Work with users"])
    app.include_router(item_router, prefix="/items", tags=["Work with items"])
