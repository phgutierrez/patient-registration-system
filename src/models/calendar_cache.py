# src/models/calendar_cache.py

from datetime import datetime
from src.extensions import db


class CalendarCache(db.Model):
    """Cache de eventos do Google Calendar (ICS)"""
    __tablename__ = 'calendar_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    fetched_at = db.Column(db.DateTime, nullable=True)
    events_json = db.Column(db.Text, nullable=True)  # JSON serializado da lista de eventos
    error_message = db.Column(db.Text, nullable=True)  # Mensagem de erro se falhar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CalendarCache {self.calendar_id}>'
