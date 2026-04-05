from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='enfermeiro')
    full_name: Mapped[str] = mapped_column(String(120))
    cns: Mapped[str | None] = mapped_column(String(15), nullable=True)
    crm: Mapped[str | None] = mapped_column(String(20), nullable=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey('specialties.id'), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
