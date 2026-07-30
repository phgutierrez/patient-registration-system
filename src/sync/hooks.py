"""Captura transacional de mudanças locais na outbox."""
from __future__ import annotations

import json
from datetime import datetime

from flask import current_app, has_app_context
from sqlalchemy import event
from sqlalchemy.orm import Session

from src.models.sync import SyncMixin, SyncOutbox, new_sync_uuid

from .adapters import adapter_for_object


_INSTALLED = False


def install_sync_hooks(sync_service) -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    @event.listens_for(Session, 'before_flush')
    def capture_sync_changes(session, flush_context, instances):
        if session.info.get('sync_applying') or not has_app_context():
            return
        if not current_app.config.get('SYNC_ENABLED', False):
            return

        deleted = list(session.deleted)
        for obj in deleted:
            if not isinstance(obj, SyncMixin) or adapter_for_object(obj) is None:
                continue
            session.add(obj)
            obj.sync_deleted = True

        candidates = list(session.new) + list(session.dirty)
        # Referências exportadas no mesmo flush precisam encontrar UUIDs já atribuídos,
        # independentemente da ordem em que os objetos entraram na sessão.
        for candidate in candidates:
            if (
                isinstance(candidate, SyncMixin)
                and adapter_for_object(candidate) is not None
                and not candidate.sync_uuid
            ):
                candidate.sync_uuid = new_sync_uuid()

        seen: set[int] = set()
        for obj in candidates:
            if id(obj) in seen or isinstance(obj, SyncOutbox):
                continue
            seen.add(id(obj))
            adapter = adapter_for_object(obj)
            if adapter is None:
                continue

            is_new = obj in session.new
            if not is_new and not session.is_modified(obj, include_collections=False):
                continue
            if not obj.sync_uuid:
                obj.sync_uuid = new_sync_uuid()
            selected = adapter.changed_fields(obj, is_new=is_new)
            if 'sync_deleted' in obj.__dict__:
                selected.add('_deleted')
            if not selected:
                continue

            event_order, event_uuid = sync_service.next_event_identity()
            changes = adapter.export(obj, selected)
            if '_deleted' in selected:
                changes['_deleted'] = bool(obj.sync_deleted)

            versions = obj.get_sync_field_versions()
            for field_name in changes:
                versions[field_name] = event_order
            obj.set_sync_field_versions(versions)
            obj.sync_updated_at = datetime.utcnow()

            payload = {
                'event_uuid': event_uuid,
                'event_order': event_order,
                'entity_type': adapter.entity_type,
                'entity_uuid': obj.sync_uuid,
                'changes': changes,
                'field_versions': {
                    name: versions[name] for name in changes
                },
            }
            session.add(SyncOutbox(
                event_uuid=event_uuid,
                event_order=event_order,
                entity_type=adapter.entity_type,
                entity_uuid=obj.sync_uuid,
                payload_json=json.dumps(
                    payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')
                ),
            ))

    @event.listens_for(Session, 'after_commit')
    def wake_sync_worker(session):
        if has_app_context() and current_app.config.get('SYNC_ENABLED', False):
            sync_service.wake()
