from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status, Depends, Path
from starlette.responses import JSONResponse, Response

import src.services.user_service as us
from src.exceptions import UnauthorizedError, ForbiddenError, NotFoundError

router = APIRouter()


async def user_token_verification(token: Annotated[str | None, Header()] = None) -> int:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        user_id = await us.user_token_verification(token)
    except UnauthorizedError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_401_UNAUTHORIZED)

    return user_id


async def admin_token_verification(
    token: Annotated[str | None, Header()] = None
) -> None:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        await us.admin_token_verification(token)
    except UnauthorizedError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_401_UNAUTHORIZED)
    except ForbiddenError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_403_FORBIDDEN)


@router.post("", include_in_schema=False)
@router.post(
    "/",
    responses={
        201: {
            "content": {
                "application/json": {
                    "example": {"user_id": 12, "token": "Some secret token"}
                }
            },
            "description": "User created",
        },
    },
)
async def create_user(username: str):
    content = await us.create_user(username)
    return JSONResponse(content=content, status_code=status.HTTP_201_CREATED)


@router.delete("", include_in_schema=False)
@router.delete(
    "/",
    responses={
        204: {"description": "User deleted"},
        401: {"description": "Not authorized"},
        404: {"description": "User not found"},
    },
)
async def delete_user_self(user_id=Depends(user_token_verification)):
    try:
        await us.delete_user_self(user_id)
    except NotFoundError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_404_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{user_id}",
    responses={
        204: {"description": "User deleted"},
        401: {"description": "Not authorized"},
        403: {"description": "Have no rights"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: Annotated[int, Path()], curr_user_id=Depends(user_token_verification)
):
    try:
        await us.delete_user(user_id, curr_user_id)
    except NotFoundError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_404_NOT_FOUND)
    except ForbiddenError as e:
        raise HTTPException(detail=e.args, status_code=status.HTTP_403_FORBIDDEN)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/admin",
    dependencies=[Depends(admin_token_verification)],
    responses={
        201: {
            "content": {
                "application/json": {
                    "example": {"user_id": 12, "token": "Some secret token"}
                }
            },
            "description": "Admin created",
        },
        401: {"description": "Not authorized"},
        403: {"description": "Have no rights"},
    },
)
async def create_admin(username: str):
    content = await us.create_user(username, admin=True)
    return JSONResponse(content=content, status_code=status.HTTP_201_CREATED)
