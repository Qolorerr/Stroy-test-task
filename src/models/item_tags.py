from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.services.db_session import SqlAlchemyBase


class ItemTag(SqlAlchemyBase):
    __tablename__ = "item_tags"
    __table_args__ = {"extend_existing": True}
    item_tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.tag_id"), nullable=False)

    item = relationship("Item")
    tag = relationship("Tag")
