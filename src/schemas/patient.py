from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    prontuario: str = Field(min_length=1, max_length=20)
    data_nascimento: date
    sexo: str = Field(min_length=1, max_length=1)
    nome_mae: str
    cns: str
    cidade: str
    endereco: str | None = None
    estado: str | None = None
    contato: str
    diagnostico: str
    cid: str


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    nome: str | None = None
    prontuario: str | None = None
    data_nascimento: date | None = None
    sexo: str | None = None
    nome_mae: str | None = None
    cns: str | None = None
    cidade: str | None = None
    endereco: str | None = None
    estado: str | None = None
    contato: str | None = None
    diagnostico: str | None = None
    cid: str | None = None


class PatientRead(PatientBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
