from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.services.db_session import SqlAlchemyBase


class Item(SqlAlchemyBase):
    __tablename__ = "items"
    __table_args__ = {"extend_existing": True}
    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[str] = mapped_column(nullable=False)
    updated_at: Mapped[str] = mapped_column(nullable=False)

    tags = relationship("Tag", secondary="item_tags", back_populates="items")

    def get_as_dict(self) -> dict[str, int | str | float | list[int]]:
        return {
            "item_id": self.item_id,
            "tag_ids": [tag.tag_id for tag in self.tags],
            "owner_id": self.owner_id,
            "content": self.content,
            "price": self.price,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
