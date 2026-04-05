from __future__ import annotations

import logging
import os
import secrets
import shutil
import sqlite3
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

    from src.extensions import db
    from src.models.specialty import Specialty
    from src.models.user import User

    with app.app_context():
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


def scoped_patients_query(query):
    if user_is_admin():
        return query
    user_specialty_id = getattr(current_user, 'specialty_id', None)
    if not user_specialty_id:
        return query.filter(False)
    return query.filter_by(specialty_id=user_specialty_id)


def get_protected_pdf_path(filename: str) -> Path:
    return Path(current_app.config['PROTECTED_PDF_DIR']) / Path(filename).name


def generate_temporary_password(length: int = 20) -> str:
    return secrets.token_urlsafe(length)[:length]


def slugify_username(full_name: str) -> str:
    normalized = ''.join(ch.lower() if ch.isalnum() else ' ' for ch in (full_name or '').strip())
    parts = [piece for piece in normalized.split() if piece]
    if not parts:
        return ''
    return parts[0]
