from datetime import datetime
from src.app import db

class SurgeryRequest(db.Model):
    __tablename__ = 'surgery_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Dados clínicos
    peso = db.Column(db.Float, nullable=False)
    sinais_sintomas = db.Column(db.Text, nullable=False)
    condicoes_justificativa = db.Column(db.Text, nullable=False)
    resultados_diagnosticos = db.Column(db.Text, nullable=False)
    
    # Informações do procedimento
    procedimento_solicitado = db.Column(db.String(100), nullable=False)
    codigo_procedimento = db.Column(db.String(10), nullable=False)
    tipo_cirurgia = db.Column(db.String(10), nullable=False)  # 'Eletiva' ou 'Urgência'
    data_cirurgia = db.Column(db.Date, nullable=False)
    internar_antes = db.Column(db.Boolean, default=False)
    hora_cirurgia = db.Column(db.Time, nullable=False)
    
    # Informações adicionais
    assistente = db.Column(db.String(100), nullable=False)
    aparelhos_especiais = db.Column(db.Text, nullable=True)
    reserva_sangue = db.Column(db.Boolean, default=False)
    quantidade_sangue = db.Column(db.String(20), nullable=True)
    raio_x = db.Column(db.Boolean, default=False)
    reserva_uti = db.Column(db.Boolean, default=False)
    duracao_prevista = db.Column(db.String(20), nullable=False)
    
    # Informações para internação
    evolucao_internacao = db.Column(db.Text, nullable=True)
    prescricao_internacao = db.Column(db.Text, nullable=True)
    exames_preop = db.Column(db.Text, nullable=True)
    opme = db.Column(db.Text, nullable=True)
    
    # Metadados
    status = db.Column(db.String(20), default='Pendente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    patient = db.relationship('Patient', backref=db.backref('surgery_requests', lazy=True))