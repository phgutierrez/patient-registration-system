"""Snapshots versionados e geração de PDFs inteiramente em memória."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pymupdf
from flask import current_app
from sqlalchemy import func

from src.extensions import db
from src.models.sync import DocumentTemplateArchive, GeneratedDocumentSnapshot
from src.pdf.generator import generate_pdf
from src.pdf.inventory import get_document_spec
from src.pdf.mappings import build_hemocomponente_mapping, build_internacao_mapping


class DocumentSnapshotError(RuntimeError):
    pass


def _safe_name(value: str) -> str:
    normalized = re.sub(r'[^\w.-]+', '_', (value or '').strip(), flags=re.UNICODE)
    return normalized.strip('._') or 'Paciente'


def _template_metadata(document_type: str) -> tuple[str, str]:
    spec = get_document_spec(document_type)
    template = spec.template_path(Path(current_app.root_path))
    return spec.template_name, hashlib.sha256(template.read_bytes()).hexdigest()


def _ensure_template_archive(
    document_type: str, template_id: str, template_sha256: str
):
    archive = DocumentTemplateArchive.query.filter_by(
        template_sha256=template_sha256, sync_deleted=False
    ).first()
    if archive is not None:
        return archive
    spec = get_document_spec(document_type)
    template = spec.template_path(Path(current_app.root_path))
    archive = DocumentTemplateArchive(
        document_type=document_type,
        template_id=template_id,
        template_sha256=template_sha256,
        pdf_bytes=template.read_bytes(),
    )
    db.session.add(archive)
    return archive

def _mapping(document_type: str, patient, surgery, requester) -> dict[str, str]:
    if document_type == 'internacao':
        values = build_internacao_mapping(patient, surgery, requester)
    elif document_type == 'hemocomponente':
        values = build_hemocomponente_mapping(patient, surgery, requester)
    else:
        raise DocumentSnapshotError(f'Documento desconhecido: {document_type}')
    return {key: str(value or '') for key, value in values.items()}


def _output_filename(document_type: str, patient, surgery) -> str:
    prefix = 'Internacao' if document_type == 'internacao' else 'Hemocomponente'
    return (
        f'{prefix}_{patient.id}_{surgery.id}_{_safe_name(patient.nome)}.pdf'
    )


def create_snapshot(document_type: str, patient, surgery, requester):
    if document_type == 'hemocomponente' and not surgery.reserva_sangue:
        return None
    values = _mapping(document_type, patient, surgery, requester)
    # Valida o snapshot antes de persistir, mas descarta os bytes.
    generate_pdf(document_type, values, Path(current_app.root_path))
    template_id, template_sha256 = _template_metadata(document_type)
    _ensure_template_archive(document_type, template_id, template_sha256)
    latest_revision = (
        db.session.query(func.max(GeneratedDocumentSnapshot.revision))
        .filter_by(
            surgery_request_id=surgery.id,
            document_type=document_type,
        )
        .scalar()
        or 0
    )
    snapshot = GeneratedDocumentSnapshot(
        surgery_request_id=surgery.id,
        document_type=document_type,
        revision=latest_revision + 1,
        output_filename=_output_filename(document_type, patient, surgery),
        payload_json=json.dumps(
            values, ensure_ascii=False, sort_keys=True, separators=(',', ':')
        ),
        template_id=template_id,
        template_sha256=template_sha256,
        renderer_version=pymupdf.version[0],
        created_by_user_id=getattr(requester, 'id', None),
    )
    db.session.add(snapshot)
    if document_type == 'internacao':
        surgery.pdf_filename = snapshot.output_filename
    else:
        surgery.pdf_hemocomponente = snapshot.output_filename
    return snapshot


def create_request_snapshots(patient, surgery, requester) -> list:
    created = [create_snapshot('internacao', patient, surgery, requester)]
    if surgery.reserva_sangue:
        created.append(
            create_snapshot('hemocomponente', patient, surgery, requester)
        )
    else:
        surgery.pdf_hemocomponente = None
    return [snapshot for snapshot in created if snapshot is not None]


def latest_snapshot(surgery_id: int, document_type: str):
    return (
        GeneratedDocumentSnapshot.query
        .filter_by(
            surgery_request_id=surgery_id,
            document_type=document_type,
            sync_deleted=False,
        )
        .order_by(GeneratedDocumentSnapshot.revision.desc())
        .first()
    )


def ensure_legacy_snapshot(surgery, document_type: str, fallback_user=None):
    snapshot = latest_snapshot(surgery.id, document_type)
    if snapshot is not None:
        return snapshot
    if document_type == 'hemocomponente' and not surgery.reserva_sangue:
        return None
    requester = surgery.created_by_user or fallback_user
    if requester is None:
        raise DocumentSnapshotError(
            'A solicitação antiga não identifica um usuário emissor disponível.'
        )
    snapshot = create_snapshot(
        document_type, surgery.patient, surgery, requester
    )
    db.session.commit()
    return snapshot


def migrate_legacy_document_snapshots() -> int:
    """Converte marcadores de PDFs antigos em snapshots versionados.

    Os arquivos físicos permanecem apenas no backup da migração. O fluxo ativo
    passa a regenerar os bytes sob demanda.
    """
    from src.models.surgery_request import SurgeryRequest
    from src.models.user import User

    # O baseline inicial precisa carregar os modelos vigentes mesmo quando ainda
    # não há solicitações. Assim, novas estações conseguem regenerar documentos
    # históricos sem depender dos arquivos da distribuição que estiverem usando.
    for document_type in ('internacao', 'hemocomponente'):
        template_id, template_sha256 = _template_metadata(document_type)
        _ensure_template_archive(document_type, template_id, template_sha256)

    fallback_user = (
        User.query.filter_by(role='admin', sync_deleted=False).order_by(User.id).first()
        or User.query.filter_by(sync_deleted=False).order_by(User.id).first()
    )
    migrated = 0
    surgeries = SurgeryRequest.query.filter_by(sync_deleted=False).order_by(
        SurgeryRequest.id
    ).all()
    for surgery in surgeries:
        requested_types = []
        if surgery.pdf_filename:
            requested_types.append('internacao')
        if surgery.reserva_sangue and surgery.pdf_hemocomponente:
            requested_types.append('hemocomponente')
        for document_type in requested_types:
            if latest_snapshot(surgery.id, document_type) is not None:
                continue
            ensure_legacy_snapshot(surgery, document_type, fallback_user)
            migrated += 1
    return migrated

def render_snapshot(snapshot) -> bytes:
    archive = DocumentTemplateArchive.query.filter_by(
        template_sha256=snapshot.template_sha256,
        sync_deleted=False,
    ).first()
    template_bytes = archive.pdf_bytes if archive is not None else None
    if template_bytes is None:
        _template_id, current_hash = _template_metadata(snapshot.document_type)
        if current_hash != snapshot.template_sha256:
            raise DocumentSnapshotError(
                f'O modelo histórico {snapshot.template_id} não está disponível nesta estação.'
            )
    try:
        values = json.loads(snapshot.payload_json)
    except ValueError as exc:
        raise DocumentSnapshotError('Snapshot de documento inválido.') from exc
    return generate_pdf(
        snapshot.document_type,
        values,
        Path(current_app.root_path),
        template_bytes=template_bytes,
    )
