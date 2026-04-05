from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Patient(Base):
    __tablename__ = 'patients'

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    prontuario: Mapped[str] = mapped_column(String(20), index=True)
    data_nascimento: Mapped[date] = mapped_column(Date)
    sexo: Mapped[str] = mapped_column(String(1))
    nome_mae: Mapped[str] = mapped_column(String(100))
    cns: Mapped[str] = mapped_column(String(15))
    cidade: Mapped[str] = mapped_column(String(100))
    endereco: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado: Mapped[str | None] = mapped_column(String(2), nullable=True)
    contato: Mapped[str] = mapped_column(String(20))
    diagnostico: Mapped[str] = mapped_column(Text)
    cid: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
