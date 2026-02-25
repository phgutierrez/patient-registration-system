"""
Modelo de Especialidade Médica.
Cada especialidade possui configurações e catálogo de procedimentos próprios.
"""
from datetime import datetime
from src.extensions import db


class Specialty(db.Model):
    __tablename__ = 'specialties'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)      # ortopedia, cirurgia_pediatrica
    name = db.Column(db.String(100), nullable=False)                   # "Ortopedia", "Cirurgia Pediátrica"
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    settings = db.relationship('SpecialtySettings', back_populates='specialty', uselist=False, cascade='all, delete-orphan')
    procedures = db.relationship('SpecialtyProcedure', back_populates='specialty', cascade='all, delete-orphan', order_by='SpecialtyProcedure.sort_order')
    users = db.relationship('User', back_populates='specialty', foreign_keys='User.specialty_id')
    surgery_requests = db.relationship('SurgeryRequest', back_populates='specialty', foreign_keys='SurgeryRequest.specialty_id')

    def __repr__(self):
        return f'<Specialty {self.slug}>'


class SpecialtySettings(db.Model):
    __tablename__ = 'specialty_settings'

    id = db.Column(db.Integer, primary_key=True)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'), unique=True, nullable=False)
    agenda_url = db.Column(db.Text, nullable=True)
    forms_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    specialty = db.relationship('Specialty', back_populates='settings')

    def __repr__(self):
        return f'<SpecialtySettings specialty_id={self.specialty_id}>'


class SpecialtyProcedure(db.Model):
    __tablename__ = 'specialty_procedures'

    id = db.Column(db.Integer, primary_key=True)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'), nullable=False)
    descricao = db.Column(db.String(300), nullable=False)
    codigo_sus = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    specialty = db.relationship('Specialty', back_populates='procedures')

    def __repr__(self):
        return f'<SpecialtyProcedure {self.descricao[:40]}>'
