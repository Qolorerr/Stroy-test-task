from typing import Any
from uuid import uuid4

from sqlalchemy import select

from src.exceptions import NotFoundError, ForbiddenError, UnauthorizedError
from src.models import User
from src.services import create_session


# Token verifications
async def user_token_verification(token: str) -> int:
    async with create_session() as session:
        query = select(User).where(User.token == token)
        result = (await session.scalars(query)).all()
        if len(result) < 1:
            raise UnauthorizedError("Wrong token")
        return result[0].user_id


async def admin_token_verification(token: str) -> None:
    async with create_session() as session:
        query = select(User).where(User.token == token)
        result = (await session.scalars(query)).all()
        if len(result) < 1:
            raise UnauthorizedError("Wrong token")
        if not result[0].admin:
            raise ForbiddenError("You can't do it")


async def create_user(username: str, admin: bool = False) -> dict[str, Any]:
    async with create_session() as session:
        token = str(uuid4())
        user = User(username=username, token=token, admin=admin)
        session.add(user)
        await session.flush()
        await session.commit()
        return {"user_id": user.user_id, "token": user.token}


async def delete_user_self(user_id: int) -> None:
    async with create_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise NotFoundError("Can't find user with this ID")

        await session.delete(user)
        await session.commit()


async def admin_rights_verification(user_id: int) -> bool:
    async with create_session() as session:
        user = await session.get(User, user_id)
        return user and user.admin


async def delete_user(user_id: int, curr_user_id: int) -> None:
    async with create_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise NotFoundError("Can't find user with this ID")

        if user.user_id != curr_user_id and not await admin_rights_verification(
            curr_user_id
        ):
            raise ForbiddenError("You can't do it")

        await session.delete(user)
        await session.commit()
