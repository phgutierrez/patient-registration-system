from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SurgeryRequest(Base):
    __tablename__ = 'surgery_requests'

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'), index=True)
    peso: Mapped[float] = mapped_column(Float)
    sinais_sintomas: Mapped[str] = mapped_column(Text)
    condicoes_justificativa: Mapped[str] = mapped_column(Text)
    resultados_diagnosticos: Mapped[str] = mapped_column(Text)
    procedimento_solicitado: Mapped[str] = mapped_column(String(120))
    codigo_procedimento: Mapped[str] = mapped_column(String(20))
    tipo_cirurgia: Mapped[str] = mapped_column(String(20))
    data_cirurgia: Mapped[date] = mapped_column(Date)
    internar_antes: Mapped[bool] = mapped_column(Boolean, default=False)
    hora_cirurgia: Mapped[time] = mapped_column(Time)
    assistente: Mapped[str] = mapped_column(String(120))
    aparelhos_especiais: Mapped[str | None] = mapped_column(Text, nullable=True)
    reserva_sangue: Mapped[bool] = mapped_column(Boolean, default=False)
    quantidade_sangue: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raio_x: Mapped[bool] = mapped_column(Boolean, default=False)
    reserva_uti: Mapped[bool] = mapped_column(Boolean, default=False)
    duracao_prevista: Mapped[str] = mapped_column(String(30))
    evolucao_internacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescricao_internacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    exames_preop: Mapped[str | None] = mapped_column(Text, nullable=True)
    opme: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey('specialties.id'), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Pendente')
    pdf_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pdf_hemocomponente: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scheduled_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_event_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    calendar_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
