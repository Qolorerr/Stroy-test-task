from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.services.db_session import SqlAlchemyBase


class Tag(SqlAlchemyBase):
    __tablename__ = "tags"
    __table_args__ = {"extend_existing": True}
    tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)

    items = relationship("Item", secondary="item_tags", back_populates="tags")
