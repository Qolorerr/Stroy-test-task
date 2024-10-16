import logging
from contextlib import asynccontextmanager
from typing import Any

import pytest
import yaml
from httpx import AsyncClient

from main import app
from src.services import base_init

with open("config.yaml", encoding="utf-8") as stream:
    try:
        cfg = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("Can't read config file")
        raise exc
logging.config.dictConfig(cfg["logger"])
logger = logging.getLogger("testing")

base_init(cfg["db_path"])


DEFAULT_ITEM = {"tag_ids": [1, 2, 3], "content": "Some new product", "price": 5.99}
DEFAULT_ITEM_2 = {"tag_ids": [1, 4], "content": "Some used product", "price": 15.30}
DEFAULT_ITEM_3 = {"tag_ids": [2, 4], "content": "Some free product", "price": 0}
DEFAULT_USERNAME = "test_user"


async def _create_test_user(
    username: str = DEFAULT_USERNAME,
    admin: bool = False,
    admin_token: str | None = None,
) -> tuple[int, str]:
    if admin and admin_token is None:
        raise ValueError("No admin token provided")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        if admin:
            response = await ac.post(
                "/users/admin",
                params={
                    "username": username,
                },
                headers={"token": admin_token},
            )
        else:
            response = await ac.post(
                "/users",
                params={
                    "username": username,
                },
            )
        assert response.status_code == 201
        json = response.json()
        user_id = json["user_id"]
        token = json["token"]
    return user_id, token


async def _delete_test_user(token: str) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(
            "/users",
            headers={"token": token},
        )
        assert response.status_code == 204


@asynccontextmanager
async def context_user(*args, **kwargs):
    user_id, token = await _create_test_user(*args, **kwargs)
    yield token
    await _delete_test_user(token=token)


async def _create_items(post_items: list[dict[str, Any]], token: str) -> list[int]:
    item_ids = []
    async with AsyncClient(app=app, base_url="http://test") as ac:
        for post_item in post_items:
            response = await ac.post(
                "/items",
                json=post_item,
                headers={"token": token},
            )
            assert response.status_code == 201
            item_id = response.json()["item_id"]
            item_ids.append(item_id)
    return item_ids


async def _delete_items(item_ids: list[int], token: str) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        for item_id in item_ids:
            response = await ac.delete(
                f"/items/{item_id}",
                headers={"token": token},
            )
            assert response.status_code == 204


@asynccontextmanager
async def context_items(post_items: list[dict[str, Any]], token: str):
    item_ids = await _create_items(post_items, token)
    yield item_ids
    await _delete_items(item_ids, token)


@pytest.mark.parametrize(
    "post_item, token, status_code",
    [
        (DEFAULT_ITEM, "SELF", 201),
        (DEFAULT_ITEM, None, 401),
        (DEFAULT_ITEM, "wrong_token", 401),
    ],
)
async def test_item_creation(
    post_item: dict[str, Any], token: str | None, status_code: int
) -> None:
    async with context_user() as user_token:
        if token == "SELF":
            token = user_token

        # Create new item
        headers = {"token": token} if token else {}
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/items",
                json=post_item,
                headers=headers,
            )
        assert response.status_code == status_code
        if status_code != 201:
            return

        item_id = response.json()["item_id"]

        # Delete item
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete(
                f"/items/{item_id}",
                headers={"token": token},
            )
        assert response.status_code == 204


@pytest.mark.parametrize(
    "post_item, token, status_code",
    [
        (DEFAULT_ITEM, "SELF", 204),
        (DEFAULT_ITEM, None, 401),
        (DEFAULT_ITEM, "wrong_token", 401),
    ],
)
async def test_item_deletion(
    post_item: dict[str, Any], token: str | None, status_code: int
) -> None:
    async with context_user() as user_token:
        # Create new item
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/items",
                json=post_item,
                headers={"token": user_token},
            )
        assert response.status_code == 201
        item_id = response.json()["item_id"]

        # Delete item
        if token == "SELF":
            token = user_token
        headers = {"token": token} if token else {}
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete(
                f"/items/{item_id}",
                headers=headers,
            )
        assert response.status_code == status_code

        if status_code == 204:
            return
        async with AsyncClient(app=app, base_url="http://test") as ac:
            await ac.delete(
                f"/items/{item_id}",
                headers={"token": user_token},
            )


@pytest.mark.parametrize(
    "post_items, params, status_code, result_items",
    [
        (
            [DEFAULT_ITEM, DEFAULT_ITEM_2, DEFAULT_ITEM_3],
            {"tag_id": 1},
            200,
            [DEFAULT_ITEM, DEFAULT_ITEM_2],
        ),
        (
            [DEFAULT_ITEM, DEFAULT_ITEM_2, DEFAULT_ITEM_3],
            {"price_less_than": 10},
            200,
            [DEFAULT_ITEM, DEFAULT_ITEM_3],
        ),
        (
            [DEFAULT_ITEM, DEFAULT_ITEM_2, DEFAULT_ITEM_3],
            {"price_more_than": 20},
            200,
            [],
        ),
    ],
)
async def test_get_items(
    post_items: list[dict[str, Any]],
    params: dict[str, int],
    status_code: int,
    result_items: list[dict[str, Any]],
) -> None:
    async with context_user() as user_token, context_items(post_items, user_token):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/items",
                params=params,
            )
        assert response.status_code == status_code
        if status_code != 200:
            return

        to_tuple = lambda x: (tuple(x["tag_ids"]), x["content"], x["price"])
        result_items = set(map(to_tuple, result_items))
        response_items = response.json()
        response_items = set(map(to_tuple, response_items))
        assert result_items == response_items


@pytest.mark.parametrize(
    "post_item, params, status_code",
    [
        (DEFAULT_ITEM, {"tag_ids": [2]}, 200),
        (DEFAULT_ITEM, {"content": "Some new content"}, 200),
        (DEFAULT_ITEM, {"price": 20}, 200),
    ],
)
async def test_patch_item(
    post_item: dict[str, Any],
    params: dict[str, int | str | bool | list[int]],
    status_code: int,
):
    async with context_user() as token, context_items([post_item], token) as item_ids:
        item_id = item_ids[0]
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.patch(
                f"/items/{item_id}",
                json=params,
                headers={"token": token},
            )
        assert response.status_code == status_code
        if status_code != 200:
            return
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                f"/items/{item_id}",
            )
        assert response.status_code == 200
        item = response.json()
        if "tag_ids" in params:
            assert item["tag_ids"] == params["tag_ids"]
        if "content" in params:
            assert item["content"] == params["content"]
        if "price" in params:
            assert item["price"] == params["price"]
