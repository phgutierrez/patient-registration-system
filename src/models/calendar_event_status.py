# src/models/calendar_event_status.py

from datetime import datetime
from src.extensions import db


class CalendarEventStatus(db.Model):
    """Modelo para persistir status de eventos da agenda (Realizada/Suspensa)"""
    __tablename__ = 'calendar_event_status'
    
    id = db.Column(db.Integer, primary_key=True)
    event_uid = db.Column(db.String(500), unique=True, nullable=False, index=True)
    event_date = db.Column(db.Date, nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False)  # REALIZADA ou SUSPENSA
    suspension_reason = db.Column(db.Text, nullable=True)  # Motivo de suspensão (obrigatório se status=SUSPENSA)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CalendarEventStatus uid={self.event_uid[:20]}... status={self.status}>'
    
    @property
    def status_display(self):
        """Retorna o status em formato legível"""
        if self.status == "REALIZADA":
            return "realizada"
        elif self.status == "SUSPENSA":
            return "suspensa"
        return None
