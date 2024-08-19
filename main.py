import logging.config
from datetime import datetime
from typing import Annotated
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, status, Header, Path, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from starlette.responses import JSONResponse, Response

from src import Item, User, base_init, create_session, Tag
from src.config import DB_PATH, LOGGER_CONFIG

app = FastAPI()

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger("app")


# Token verifications
async def user_token_verification(token: Annotated[str | None, Header()] = None) -> int:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    async with create_session() as session:
        query = select(User).where(User.token == token)
        result = (await session.scalars(query)).all()
        if len(result) < 1:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return result[0].user_id


async def admin_token_verification(token: Annotated[str | None, Header()] = None):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    async with create_session() as session:
        query = select(User).where(User.token == token)
        result = (await session.scalars(query)).all()
        if len(result) < 1:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        if not result[0].admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


# Users management
@app.post("/user", responses={
    201: {
        "content": {
            "application/json": {
                "example": {"user_id": 12, "token": "Some secret token"}
            }
        },
        "description": "User created"
    },
})
async def create_user(username: str):
    async with create_session() as session:
        token = str(uuid4())
        user = User(username=username, token=token)
        session.add(user)
        await session.flush()
        await session.commit()
        return JSONResponse(content={"user_id": user.user_id, "token": user.token},
                            status_code=status.HTTP_201_CREATED)


@app.delete("/user", responses={
    204: {
        "description": "User deleted"
    },
    401: {
        "description": "Not authorized"
    },
    404: {
        "description": "User not found"
    },
})
async def delete_user_self(user_id=Depends(user_token_verification)):
    async with create_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return status.HTTP_404_NOT_FOUND

        await session.delete(user)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _admin_rights_verification(user_id: int) -> bool:
    async with create_session() as session:
        query = select(User).where(User.user_id == user_id)
        result = (await session.scalars(query)).all()
        if len(result) < 1:
            return False
        return result[0].admin


@app.delete("/user/{user_id}", responses={
    204: {
        "description": "User deleted"
    },
    401: {
        "description": "Not authorized"
    },
    403: {
        "description": "Have no rights"
    },
    404: {
        "description": "User not found"
    },
})
async def delete_user(user_id: Annotated[int, Path()], curr_user_id=Depends(user_token_verification)):
    async with create_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return status.HTTP_404_NOT_FOUND

        if user.user_id != curr_user_id and not await _admin_rights_verification(curr_user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await session.delete(user)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/admin", dependencies=[Depends(admin_token_verification)], responses={
    201: {
        "content": {
            "application/json": {
                "example": {"user_id": 12, "token": "Some secret token"}
            }
        },
        "description": "Admin created"
    },
    401: {
        "description": "Not authorized"
    },
    403: {
        "description": "Have no rights"
    },
})
async def create_admin(username: str):
    async with create_session() as session:
        token = str(uuid4())
        user = User(username=username, token=token, admin=True)
        session.add(user)
        await session.flush()
        await session.commit()
        return JSONResponse(content={"user_id": user.user_id, "token": user.token},
                            status_code=status.HTTP_201_CREATED)


# Items management
@app.get("/item", responses={
    200: {
        "content": {
            "application/json": {
                "example": [
                    {
                        "item_id": 12,
                        "tag_ids": [1, 2, 3],
                        "owner_id": 12,
                        "content": "Some info about item",
                        "price": 12,
                        "created_at": "2024-08-19T12:00:00.000000",
                        "updated_at": "2024-08-19T12:00:00.000000"
                    }
                ]
            }
        },
        "description": "Ok"
    },
})
async def get_items(owner_id: int | None = None, tag_id: int | None = None,
                    price_more_than: float | None = None,
                    price_less_than: float | None = None,
                    limit: int | None = None, offset: int | None = 0):
    async with create_session() as session:
        # Check tag existence
        if tag_id is not None:
            tag = await session.get(Tag, tag_id)
            if tag is None:
                return JSONResponse(content=[], status_code=status.HTTP_200_OK)

        conditions = []
        if owner_id is not None:
            conditions.append(Item.owner_id == owner_id)
        if tag_id is not None:
            conditions.append(Tag.tag_id == tag_id)
        if price_more_than is not None:
            conditions.append(Item.price > price_more_than)
        if price_less_than is not None:
            conditions.append(Item.price < price_less_than)

        query = select(Item).join(Item.tags).where(and_(*conditions))
        results = (await session.scalars(query)).all()
        if limit is not None:
            results = results[offset:offset + limit]

        for i in range(len(results)):
            results[i] = results[i].get_as_dict()
        return JSONResponse(content=results, status_code=status.HTTP_200_OK)


@app.get("/item/{item_id}", responses={
    200: {
        "content": {
            "application/json": {
                "example":{
                    "item_id": 12,
                    "tag_ids": [1, 2, 3],
                    "owner_id": 12,
                    "content": "Some info about item",
                    "price": 12,
                    "created_at": "2024-08-19T12:00:00.000000",
                    "updated_at": "2024-08-19T12:00:00.000000"
                }
            }
        },
        "description": "Ok"
    },
    404: {
        "description": "Item not found"
    },
})
async def get_item(item_id: Annotated[int, Path()]):
    async with create_session() as session:
        query = select(Item).join(Item.tags).where(Item.item_id == item_id)
        results = (await session.scalars(query)).all()
        if len(results) < 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        content = results[0].get_as_dict()
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)


class PostItem(BaseModel):
    tag_ids: list[int]
    content: str
    price: float


@app.post("/item", responses={
    201: {
        "content": {
            "application/json": {
                "example": {"item_id": 12}
            }
        },
        "description": "User created"
    },
    401: {
        "description": "Not authorized"
    },
})
async def post_item(args: PostItem, user_id=Depends(user_token_verification)):
    async with create_session() as session:
        item = Item(owner_id=user_id, content=args.content,
                    price=args.price, created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat())
        for tag_id in args.tag_ids:
            tag = await session.get(Tag, tag_id)
            if tag is None:
                tag = Tag(tag_id=tag_id)
                session.add(tag)
            item.tags.append(tag)
        session.add(item)
        await session.flush()
        await session.commit()
        return JSONResponse(content={"item_id": item.item_id}, status_code=status.HTTP_201_CREATED)


class PatchItem(BaseModel):
    tag_ids: list[int] | None = None
    content: str | None = None
    price: float | None = None


@app.patch("/item/{item_id}", responses={
    200: {
        "description": "Ok"
    },
    401: {
        "description": "Not authorized"
    },
    403: {
        "description": "Have no rights"
    },
    404: {
        "description": "Item not found"
    },
})
async def patch_item(args: PatchItem, item_id: Annotated[int, Path()],
                     user_id=Depends(user_token_verification)):
    async with create_session() as session:
        item = await session.get(Item, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if item.owner_id != user_id and not await _admin_rights_verification(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        if args.tag_ids is not None:
            item.tags = []
            for tag_id in args.tag_ids:
                tag = await session.get(Tag, tag_id)
                if tag is None:
                    tag = Tag(tag_id=tag_id)
                    session.add(tag)
                item.tags.append(tag)
        if args.content is not None:
            item.content = args.content
        if args.price is not None:
            item.price = args.price
        item.updated_at = datetime.now().isoformat()

        await session.commit()
        return Response(status_code=status.HTTP_200_OK)


@app.delete("/item/{item_id}", responses={
    204: {
        "description": "Item deleted"
    },
    401: {
        "description": "Not authorized"
    },
    403: {
        "description": "Have no rights"
    },
    404: {
        "description": "Item not found"
    },
})
async def delete_item(item_id: Annotated[int, Path()], user_id=Depends(user_token_verification)):
    async with create_session() as session:
        item = await session.get(Item, item_id)
        if not item:
            return status.HTTP_404_NOT_FOUND

        if item.owner_id != user_id and not await _admin_rights_verification(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await session.delete(item)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == '__main__':
    base_init(DB_PATH)
    uvicorn.run("main:app", port=8000, reload=False, log_level="info")
