from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
