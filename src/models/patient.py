from datetime import datetime
from src.extensions import db


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    # Prontuário com índice para otimizar buscas LAN
    prontuario = db.Column(db.String(20), nullable=False, index=True)
    data_nascimento = db.Column(db.DateTime, nullable=False)
    sexo = db.Column(db.String(1), nullable=False)
    nome_mae = db.Column(db.String(100), nullable=False)
    cns = db.Column(db.String(15), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(200), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    contato = db.Column(db.String(20), nullable=False)
    diagnostico = db.Column(db.Text, nullable=False)
    cid = db.Column(db.String(4), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Adiciona o relacionamento reverso com cascade
    surgery_requests = db.relationship(
        'SurgeryRequest',
        backref='patient',
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def idade(self):
        """Calcula a idade atual do paciente."""
        today = datetime.today()
        born = self.data_nascimento
        age = today.year - born.year - \
            ((today.month, today.day) < (born.month, born.day))
        return age
