from typing import Annotated

from fastapi import APIRouter, status, Path, HTTPException, Depends
from starlette.responses import JSONResponse, Response

import src.services.item_service as its
from src.exceptions import NotFoundError, ForbiddenError
from src.handlers.user_handler import user_token_verification
from src.schemas import PostItem, PatchItem

router = APIRouter()


@router.get("", include_in_schema=False)
@router.get(
    "/",
    responses={
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
                            "updated_at": "2024-08-19T12:00:00.000000",
                        }
                    ]
                }
            },
            "description": "Ok",
        },
    },
)
async def get_items(
    owner_id: int | None = None,
    tag_id: int | None = None,
    price_more_than: float | None = None,
    price_less_than: float | None = None,
    limit: int | None = None,
    offset: int = 0,
):
    results = await its.get_items(
        owner_id, tag_id, price_more_than, price_less_than, limit, offset
    )
    return JSONResponse(content=results, status_code=status.HTTP_200_OK)


@router.get(
    "/{item_id}",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "item_id": 12,
                        "tag_ids": [1, 2, 3],
                        "owner_id": 12,
                        "content": "Some info about item",
                        "price": 12,
                        "created_at": "2024-08-19T12:00:00.000000",
                        "updated_at": "2024-08-19T12:00:00.000000",
                    }
                }
            },
            "description": "Ok",
        },
        404: {"description": "Item not found"},
    },
)
async def get_item(item_id: Annotated[int, Path()]):
    try:
        result = await its.get_item(item_id)
    except NotFoundError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(content=result, status_code=status.HTTP_200_OK)


@router.post("", include_in_schema=False)
@router.post(
    "/",
    responses={
        201: {
            "content": {"application/json": {"example": {"item_id": 12}}},
            "description": "User created",
        },
        401: {"description": "Not authorized"},
    },
)
async def post_item(args: PostItem, user_id=Depends(user_token_verification)):
    item_id = await its.post_item(args, user_id)
    return JSONResponse(
        content={"item_id": item_id}, status_code=status.HTTP_201_CREATED
    )


@router.patch(
    "/{item_id}",
    responses={
        200: {"description": "Ok"},
        401: {"description": "Not authorized"},
        403: {"description": "Have no rights"},
        404: {"description": "Item not found"},
    },
)
async def patch_item(
    args: PatchItem,
    item_id: Annotated[int, Path()],
    user_id=Depends(user_token_verification),
):
    try:
        await its.patch_item(args, item_id, user_id)
    except NotFoundError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_404_NOT_FOUND)
    except ForbiddenError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_403_FORBIDDEN)
    return Response(status_code=status.HTTP_200_OK)


@router.delete(
    "/{item_id}",
    responses={
        204: {"description": "Item deleted"},
        401: {"description": "Not authorized"},
        403: {"description": "Have no rights"},
        404: {"description": "Item not found"},
    },
)
async def delete_item(
    item_id: Annotated[int, Path()], user_id=Depends(user_token_verification)
):
    try:
        await its.delete_item(item_id, user_id)
    except NotFoundError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_404_NOT_FOUND)
    except ForbiddenError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_403_FORBIDDEN)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
