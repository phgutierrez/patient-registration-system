from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class SurgeryRequestBase(BaseModel):
    patient_id: int
    peso: float
    sinais_sintomas: str
    condicoes_justificativa: str
    resultados_diagnosticos: str
    procedimento_solicitado: str
    codigo_procedimento: str
    tipo_cirurgia: str
    data_cirurgia: date
    internar_antes: bool = False
    hora_cirurgia: time
    assistente: str
    aparelhos_especiais: str | None = None
    reserva_sangue: bool = False
    quantidade_sangue: str | None = None
    raio_x: bool = False
    reserva_uti: bool = False
    duracao_prevista: str
    evolucao_internacao: str | None = None
    prescricao_internacao: str | None = None
    exames_preop: str | None = None
    opme: str | None = None


class SurgeryRequestCreate(SurgeryRequestBase):
    pass


class SurgeryRequestRead(SurgeryRequestBase):
    id: int
    status: str
    pdf_filename: str | None = None
    pdf_hemocomponente: str | None = None
    scheduled_at: datetime | None = None
    scheduled_event_link: str | None = None
    calendar_status: str | None = None

    model_config = ConfigDict(from_attributes=True)
