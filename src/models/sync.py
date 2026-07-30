"""Modelos e metadados da sincronização offline-first.

O banco SQLite permanece estritamente local. Somente envelopes criptografados
gerados a partir destas tabelas podem ser publicados no compartilhamento.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from src.extensions import db


def new_sync_uuid() -> str:
    return str(uuid.uuid4())


class SyncMixin:
    """Campos comuns das entidades replicadas entre estações."""

    sync_uuid = db.Column(
        db.String(36), nullable=False, default=new_sync_uuid, index=True
    )
    sync_field_versions = db.Column(db.Text, nullable=False, default='{}')
    sync_deleted = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.false(), index=True
    )
    sync_updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def get_sync_field_versions(self) -> dict[str, str]:
        try:
            value = json.loads(self.sync_field_versions or '{}')
            return value if isinstance(value, dict) else {}
        except (TypeError, ValueError):
            return {}

    def set_sync_field_versions(self, versions: dict[str, str]) -> None:
        self.sync_field_versions = json.dumps(
            versions, ensure_ascii=False, sort_keys=True, separators=(',', ':')
        )


class SyncOutbox(db.Model):
    __tablename__ = 'sync_outbox'

    id = db.Column(db.Integer, primary_key=True)
    event_uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    event_order = db.Column(db.String(120), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_uuid = db.Column(db.String(36), nullable=False, index=True)
    payload_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True, index=True)
    publish_attempts = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.String(500), nullable=True)


class SyncAppliedEvent(db.Model):
    __tablename__ = 'sync_applied_events'

    id = db.Column(db.Integer, primary_key=True)
    event_uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    source_device_uuid = db.Column(db.String(36), nullable=False, index=True)
    source_sequence = db.Column(db.Integer, nullable=False)
    event_order = db.Column(db.String(120), nullable=False)
    applied_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class SyncDeviceState(db.Model):
    __tablename__ = 'sync_device_state'

    id = db.Column(db.Integer, primary_key=True)
    device_uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    last_published_sequence = db.Column(db.Integer, nullable=False, default=0)
    last_published_hash = db.Column(db.String(64), nullable=True)
    last_consumed_sequence = db.Column(db.Integer, nullable=False, default=0)
    last_consumed_hash = db.Column(db.String(64), nullable=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.String(500), nullable=True)


class SyncAuditRevision(db.Model):
    __tablename__ = 'sync_audit_revisions'

    id = db.Column(db.Integer, primary_key=True)
    event_uuid = db.Column(db.String(36), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_uuid = db.Column(db.String(36), nullable=False, index=True)
    field_name = db.Column(db.String(100), nullable=False)
    previous_value_json = db.Column(db.Text, nullable=True)
    incoming_value_json = db.Column(db.Text, nullable=True)
    previous_order = db.Column(db.String(120), nullable=True)
    incoming_order = db.Column(db.String(120), nullable=False)
    accepted = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class DeviceSettings(db.Model):
    """Configuração que não deve sair do computador atual."""

    __tablename__ = 'device_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value_json = db.Column(db.Text, nullable=True)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DocumentTemplateArchive(SyncMixin, db.Model):
    """Versão imutável do template necessária à regeneração histórica."""

    __tablename__ = 'document_template_archives'

    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(40), nullable=False, index=True)
    template_id = db.Column(db.String(100), nullable=False)
    template_sha256 = db.Column(
        db.String(64), nullable=False, unique=True, index=True
    )
    pdf_bytes = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('sync_uuid', name='uq_document_template_sync_uuid'),
    )

class GeneratedDocumentSnapshot(SyncMixin, db.Model):
    """Dados versionados usados para regenerar um documento, nunca seus bytes."""

    __tablename__ = 'generated_document_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    surgery_request_id = db.Column(
        db.Integer, db.ForeignKey('surgery_requests.id'), nullable=False, index=True
    )
    document_type = db.Column(db.String(40), nullable=False, index=True)
    revision = db.Column(db.Integer, nullable=False, default=1)
    output_filename = db.Column(db.String(255), nullable=False)
    payload_json = db.Column(db.Text, nullable=False)
    template_id = db.Column(db.String(100), nullable=False)
    template_sha256 = db.Column(db.String(64), nullable=False)
    renderer_version = db.Column(db.String(30), nullable=False)
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True, index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    surgery_request = db.relationship(
        'SurgeryRequest',
        back_populates='document_snapshots',
        foreign_keys=[surgery_request_id],
    )
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id])

    __table_args__ = (
        db.UniqueConstraint(
            'surgery_request_id',
            'document_type',
            'revision',
            name='uq_generated_document_revision',
        ),
        db.UniqueConstraint('sync_uuid', name='uq_generated_document_sync_uuid'),
    )
