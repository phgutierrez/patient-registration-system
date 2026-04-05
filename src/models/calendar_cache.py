from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class CalendarCache(Base):
    __tablename__ = 'calendar_cache'

    id: Mapped[int] = mapped_column(primary_key=True)
    calendar_id: Mapped[str] = mapped_column(String(255), unique=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    events_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
