from datetime import datetime
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from src.exceptions import NotFoundError, ForbiddenError
from src.models import Tag, Item
from src.schemas import PostItem, PatchItem
from src.services import create_session
from src.services.user_service import admin_rights_verification


async def get_items(
    owner_id: int | None,
    tag_id: int | None,
    price_more_than: float | None,
    price_less_than: float | None,
    limit: int | None,
    offset: int,
) -> list[dict[str, Any]]:
    async with create_session() as session:
        # Check tag existence
        if tag_id is not None:
            tag = await session.get(Tag, tag_id)
            if tag is None:
                return []

        conditions = []
        if owner_id is not None:
            conditions.append(Item.owner_id == owner_id)
        if tag_id is not None:
            conditions.append(Tag.tag_id == tag_id)
        if price_more_than is not None:
            conditions.append(Item.price > price_more_than)
        if price_less_than is not None:
            conditions.append(Item.price < price_less_than)

        query = (
            select(Item)
            .join(Item.tags)
            .options(selectinload(Item.tags))
            .where(and_(*conditions))
        )
        results = (await session.scalars(query)).all()
        if limit is not None:
            results = results[offset : offset + limit]

        for i in range(len(results)):
            results[i] = results[i].get_as_dict()
        return results


async def get_item(item_id: int) -> dict[str, Any]:
    async with create_session() as session:
        stmt = (
            select(Item).options(selectinload(Item.tags)).where(Item.item_id == item_id)
        )
        result = await session.execute(stmt)
        item = result.scalars().first()
        if not item:
            raise NotFoundError("Can't find item with this ID")
        return item.get_as_dict()


async def post_item(args: PostItem, user_id: int) -> int:
    async with create_session() as session:
        item = Item(
            owner_id=user_id,
            content=args.content,
            price=args.price,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        for tag_id in args.tag_ids:
            tag = await session.get(Tag, tag_id)
            if tag is None:
                tag = Tag(tag_id=tag_id)
                session.add(tag)
            item.tags.append(tag)
        session.add(item)
        await session.flush()
        await session.commit()
        return item.item_id


async def patch_item(args: PatchItem, item_id: int, user_id: int) -> None:
    async with create_session() as session:
        stmt = (
            select(Item).options(selectinload(Item.tags)).where(Item.item_id == item_id)
        )
        result = await session.execute(stmt)
        item = result.scalars().first()
        if item is None:
            raise NotFoundError("Can't find item with this ID")

        if item.owner_id != user_id and not await admin_rights_verification(user_id):
            raise ForbiddenError("You can't do it")

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


async def delete_item(item_id: int, user_id: int) -> None:
    async with create_session() as session:
        item = await session.get(Item, item_id)
        if not item:
            raise NotFoundError("Can't find item with this ID")

        if item.owner_id != user_id and not await admin_rights_verification(user_id):
            raise ForbiddenError("You can't do it")

        await session.delete(item)
        await session.commit()
