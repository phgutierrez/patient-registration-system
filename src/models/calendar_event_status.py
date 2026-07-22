# src/models/calendar_event_status.py

from datetime import datetime
from src.extensions import db


class CalendarEventStatus(db.Model):
    """Persisted outcome and optional surgery link for a calendar event."""
    __tablename__ = 'calendar_event_status'
    
    id = db.Column(db.Integer, primary_key=True)
    event_uid = db.Column(db.String(500), unique=True, nullable=False, index=True)
    event_date = db.Column(db.Date, nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False)  # PENDENTE, REALIZADA ou SUSPENSA
    suspension_reason = db.Column(db.Text, nullable=True)
    surgery_request_id = db.Column(
        db.Integer,
        db.ForeignKey('surgery_requests.id'),
        nullable=True,
        index=True,
    )
    surgery_request = db.relationship(
        'SurgeryRequest',
        foreign_keys=[surgery_request_id],
        back_populates='calendar_event_statuses',
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CalendarEventStatus uid={self.event_uid[:20]}... status={self.status}>'
    
    @property
    def status_display(self):
        """Retorna o status em formato legível"""
        if self.status == "REALIZADA":
            return "realizada"
        if self.status == "SUSPENSA":
            return "suspensa"
        return "pendente"
