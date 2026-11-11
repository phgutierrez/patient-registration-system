from __future__ import annotations

import logging
import os
import secrets
import shutil
import sqlite3
import uuid
from functools import wraps
from pathlib import Path

from flask import abort, current_app, jsonify, request
from flask_login import current_user

logger = logging.getLogger(__name__)


def _get_sqlite_db_path(app) -> str | None:
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not uri.startswith('sqlite:///'):
        return None
    return uri.replace('sqlite:///', '', 1)


def ensure_security_schema(app) -> None:
    db_path = _get_sqlite_db_path(app)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        def get_columns(table_name):
            cursor.execute(f'PRAGMA table_info({table_name})')
            return {row[1] for row in cursor.fetchall()}

        def add_column_if_missing(table_name, column_name, sql_definition):
            columns = get_columns(table_name)
            if column_name in columns:
                return False
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_definition}')
            logger.info("Coluna adicionada automaticamente: %s.%s", table_name, column_name)
            return True

        tables = {
            row[0]
            for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

        if 'users' in tables:
            users_column_added = add_column_if_missing('users', 'must_change_password', 'BOOLEAN NOT NULL DEFAULT 0')
            cursor.execute(
                """
                UPDATE users
                   SET role = CASE
                        WHEN lower(coalesce(role, '')) IN ('admin', 'administrador') THEN 'admin'
                        WHEN trim(coalesce(role, '')) = '' THEN 'solicitante'
                        ELSE lower(role)
                   END
                """
            )
            if users_column_added:
                cursor.execute(
                    """
                    UPDATE users
                       SET must_change_password = 1
                     WHERE lower(coalesce(role, '')) != 'admin'
                    """
                )

        if 'patient' in tables:
            add_column_if_missing('patient', 'specialty_id', 'INTEGER')
            cursor.execute(
                """
                UPDATE patient
                   SET specialty_id = (
                       SELECT sr.specialty_id
                         FROM surgery_requests sr
                        WHERE sr.patient_id = patient.id
                          AND sr.specialty_id IS NOT NULL
                        ORDER BY sr.created_at DESC, sr.id DESC
                        LIMIT 1
                   )
                 WHERE specialty_id IS NULL
                """
            )
            if 'specialties' in tables:
                cursor.execute(
                    """
                    UPDATE patient
                       SET specialty_id = (
                           SELECT id FROM specialties WHERE slug = 'ortopedia' LIMIT 1
                       )
                     WHERE specialty_id IS NULL
                    """
                )
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patient_specialty_id ON patient(specialty_id)')

        if 'surgery_requests' in tables:
            add_column_if_missing('surgery_requests', 'created_by_user_id', 'INTEGER')
            cursor.execute(
                """
                UPDATE surgery_requests
                   SET specialty_id = (
                       SELECT patient.specialty_id
                         FROM patient
                        WHERE patient.id = surgery_requests.patient_id
                   )
                 WHERE specialty_id IS NULL
                """
            )
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_surgery_requests_created_by_user_id ON surgery_requests(created_by_user_id)')
            add_column_if_missing('surgery_requests', 'scheduled_attempt_id', 'VARCHAR(36)')
            add_column_if_missing('surgery_requests', 'scheduled_result_uncertain', 'BOOLEAN NOT NULL DEFAULT 0')
            cursor.execute('CREATE INDEX IF NOT EXISTS ix_surgery_requests_scheduled_attempt_id ON surgery_requests(scheduled_attempt_id)')

        if 'calendar_event_status' in tables:
            add_column_if_missing('calendar_event_status', 'surgery_request_id', 'INTEGER')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_calendar_event_status_surgery_request_id '
                'ON calendar_event_status(surgery_request_id)'
            )

        if 'specialty_settings' in tables:
            add_column_if_missing('specialty_settings', 'access_host', "VARCHAR(255) NOT NULL DEFAULT '192.168.1.252'")
            add_column_if_missing('specialty_settings', 'access_share_path', "VARCHAR(500) NOT NULL DEFAULT 'naqh\\AMBULATORIO_SERV'")
            add_column_if_missing('specialty_settings', 'access_filename', "VARCHAR(255) NOT NULL DEFAULT 'AMBULATORIO_SERV.accdb'")
            add_column_if_missing('specialty_settings', 'access_enabled', 'BOOLEAN NOT NULL DEFAULT 1')
            add_column_if_missing('specialty_settings', 'access_source', "VARCHAR(20) NOT NULL DEFAULT 'network'")
            add_column_if_missing('specialty_settings', 'access_local_path', 'TEXT')

        sync_tables = (
            'users', 'patient', 'surgery_requests', 'specialties',
            'specialty_settings', 'specialty_procedures', 'calendar_event_status',
        )
        for table_name in sync_tables:
            if table_name not in tables:
                continue
            add_column_if_missing(table_name, 'sync_uuid', 'VARCHAR(36)')
            add_column_if_missing(
                table_name, 'sync_field_versions', "TEXT NOT NULL DEFAULT '{}'"
            )
            add_column_if_missing(
                table_name, 'sync_deleted', 'BOOLEAN NOT NULL DEFAULT 0'
            )
            add_column_if_missing(table_name, 'sync_updated_at', 'DATETIME')
            missing_ids = cursor.execute(
                f'SELECT id FROM {table_name} WHERE sync_uuid IS NULL OR trim(sync_uuid) = ""'
            ).fetchall()
            for (row_id,) in missing_ids:
                cursor.execute(
                    f'UPDATE {table_name} SET sync_uuid = ?, '
                    'sync_updated_at = coalesce(sync_updated_at, CURRENT_TIMESTAMP) '
                    'WHERE id = ?',
                    (str(uuid.uuid4()), row_id),
                )
            cursor.execute(
                f'CREATE UNIQUE INDEX IF NOT EXISTS uq_{table_name}_sync_uuid '
                f'ON {table_name}(sync_uuid)'
            )

        if 'patient' in tables:
            add_column_if_missing('patient', 'superseded_by_uuid', 'VARCHAR(36)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS ix_patient_superseded_by_uuid '
                'ON patient(superseded_by_uuid)'
            )
        conn.commit()
    finally:
        conn.close()


def migrate_legacy_pdf_storage(app) -> None:
    protected_dir = Path(app.config['PROTECTED_PDF_DIR'])
    protected_dir.mkdir(parents=True, exist_ok=True)

    legacy_dir = Path(app.root_path) / 'static' / 'preenchidos'
    if not legacy_dir.exists():
        return

    for legacy_file in legacy_dir.glob('*.pdf'):
        target = protected_dir / legacy_file.name
        if not legacy_file.exists():
            continue
        if target.exists():
            legacy_file.unlink(missing_ok=True)
            continue
        try:
            shutil.move(str(legacy_file), str(target))
            logger.info("PDF legado migrado para armazenamento protegido: %s", target.name)
        except FileNotFoundError:
            continue


def bootstrap_admin_if_configured(app) -> None:
    username = app.config.get('ADMIN_BOOTSTRAP_USERNAME')
    password = app.config.get('ADMIN_BOOTSTRAP_PASSWORD')
    if not username or not password:
        return
    from src.password_policy import is_valid_pin
    if not is_valid_pin(password):
        logger.error('ADMIN_BOOTSTRAP_PASSWORD deve conter exatamente 6 dígitos; bootstrap ignorado.')
        return

    from sqlalchemy import inspect
    from src.extensions import db
    from src.models.specialty import Specialty
    from src.models.user import User

    with app.app_context():
        if 'users' not in inspect(db.engine).get_table_names():
            logger.info('Bootstrap de administrador adiado: tabela users ainda não existe.')
            return
        existing_admin = User.query.filter_by(role='admin').first()
        if existing_admin:
            return

        specialty = Specialty.query.filter_by(
            slug=app.config.get('ADMIN_BOOTSTRAP_SPECIALTY', 'ortopedia'),
            is_active=True,
        ).first()
        specialty_id = specialty.id if specialty else None

        user = User(
            username=username,
            password=password,
            full_name=app.config.get('ADMIN_BOOTSTRAP_FULL_NAME', 'Administrador do Sistema'),
            role='admin',
            specialty_id=specialty_id,
            must_change_password=True,
        )
        db.session.add(user)
        db.session.commit()
        logger.warning("Usuário admin bootstrap criado: %s", username)


def request_is_loopback() -> bool:
    """Confia somente no socket remoto, nunca em cabeçalhos de proxy."""
    return (request.remote_addr or '').split('%', 1)[0] in {'127.0.0.1', '::1'}


def user_is_admin(user=None) -> bool:
    target_user = user or current_user
    return bool(getattr(target_user, 'is_authenticated', False) and getattr(target_user, 'is_admin', False))


def _forbidden(message='Acesso negado a este recurso.'):
    if request.accept_mimetypes.best == 'application/json' or request.path.startswith('/patients/api/') or request.path.startswith('/surgery_requests/'):
        return jsonify({'error': message}), 403
    abort(403, description=message)


def require_admin(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not user_is_admin():
            return _forbidden('Apenas administradores podem acessar este recurso.')
        return view_func(*args, **kwargs)
    return wrapped


def enforce_specialty_access(specialty_id, message='Acesso negado para outra especialidade.'):
    if user_is_admin():
        return None
    user_specialty_id = getattr(current_user, 'specialty_id', None)
    if not specialty_id or not user_specialty_id or specialty_id != user_specialty_id:
        return _forbidden(message)
    return None


def ensure_patient_access(patient):
    return enforce_specialty_access(patient.specialty_id, 'Você não pode acessar pacientes de outra especialidade.')


def ensure_surgery_access(surgery_request):
    specialty_id = surgery_request.specialty_id or getattr(surgery_request.patient, 'specialty_id', None)
    return enforce_specialty_access(specialty_id, 'Você não pode acessar solicitações de outra especialidade.')


def can_delete_surgery(surgery_request, user=None) -> bool:
    """Autor da solicitação ou administrador. Registros sem autor: só admin."""
    target_user = user or current_user
    if not getattr(target_user, 'is_authenticated', False):
        return False
    if user_is_admin(target_user):
        return True
    author_id = getattr(surgery_request, 'created_by_user_id', None)
    return author_id is not None and author_id == getattr(target_user, 'id', None)


def scoped_patients_query(query):
    from src.models.patient import Patient
    query = query.filter(Patient.sync_deleted.is_(False))
    if user_is_admin():
        return query
    user_specialty_id = getattr(current_user, 'specialty_id', None)
    if not user_specialty_id:
        return query.filter(False)
    return query.filter_by(specialty_id=user_specialty_id)


def scoped_surgery_requests_query(query):
    """Apply the same specialty boundary used by surgery detail routes."""
    from src.models.surgery_request import SurgeryRequest
    query = query.filter(SurgeryRequest.sync_deleted.is_(False))
    if user_is_admin():
        return query
    user_specialty_id = getattr(current_user, 'specialty_id', None)
    if not user_specialty_id:
        return query.filter(False)
    from src.models.patient import Patient
    return query.outerjoin(Patient, SurgeryRequest.patient_id == Patient.id).filter(
        (SurgeryRequest.specialty_id == user_specialty_id)
        | (
            SurgeryRequest.specialty_id.is_(None)
            & (Patient.specialty_id == user_specialty_id)
        )
    )


def get_protected_pdf_path(filename: str) -> Path:
    return Path(current_app.config['PROTECTED_PDF_DIR']) / Path(filename).name


def generate_temporary_password(length: int = 6) -> str:
    """Generate a six-digit PIN. ``length`` remains for API compatibility."""
    from src.password_policy import generate_pin
    return generate_pin()


def slugify_username(full_name: str) -> str:
    normalized = ''.join(ch.lower() if ch.isalnum() else ' ' for ch in (full_name or '').strip())
    parts = [piece for piece in normalized.split() if piece]
    if not parts:
        return ''
    return parts[0]
