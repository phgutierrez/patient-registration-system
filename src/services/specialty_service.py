"""
Serviço de especialidade ativa.

Funções centrais para:
  - ler/gravar a especialidade ativa na sessão Flask
  - carregar dados da especialidade (procedimentos, settings, usuários)
  - fallback seguro para Ortopedia quando não há dados configurados
"""
from __future__ import annotations
from typing import Optional, List, Tuple, Dict
from flask import session


# ── Constantes ──────────────────────────────────────────────────────────────
DEFAULT_SPECIALTY_SLUG = 'ortopedia'


# ── Sessão ───────────────────────────────────────────────────────────────────

def get_active_specialty_slug() -> str:
    """Retorna o slug da especialidade ativa na sessão (fallback: ortopedia)."""
    return session.get('specialty_slug', DEFAULT_SPECIALTY_SLUG)


def set_active_specialty_slug(slug: str) -> None:
    """Grava o slug da especialidade ativa na sessão."""
    session['specialty_slug'] = slug
    session.modified = True


# ── Carregamento do banco ─────────────────────────────────────────────────────

def get_specialty(slug: Optional[str] = None):
    """
    Retorna o objeto Specialty para o slug indicado (ou o ativo na sessão).
    Se não encontrar, retorna o de ortopedia como fallback.
    """
    from src.models.specialty import Specialty
    target = slug or get_active_specialty_slug()
    sp = Specialty.query.filter_by(slug=target, is_active=True).first()
    if sp is None:
        sp = Specialty.query.filter_by(slug=DEFAULT_SPECIALTY_SLUG).first()
    return sp


def get_active_specialty():
    """Atalho: retorna Specialty ativo na sessão."""
    return get_specialty()


def get_specialty_settings(specialty=None):
    """
    Retorna o objeto SpecialtySettings da especialidade.
    Pode receber um objeto Specialty ou buscar o ativo.
    """
    from src.models.specialty import SpecialtySettings
    sp = specialty or get_active_specialty()
    if sp is None:
        return None
    return SpecialtySettings.query.filter_by(specialty_id=sp.id).first()


def get_specialty_procedures(specialty=None) -> List:
    """
    Retorna lista de SpecialtyProcedure ativos da especialidade, ordenados por sort_order.
    """
    from src.models.specialty import SpecialtyProcedure
    sp = specialty or get_active_specialty()
    if sp is None:
        return []
    return (
        SpecialtyProcedure.query
        .filter_by(specialty_id=sp.id, is_active=True)
        .order_by(SpecialtyProcedure.sort_order, SpecialtyProcedure.id)
        .all()
    )


def get_procedure_choices(specialty=None) -> List[Tuple[str, str]]:
    """
    Retorna lista de choices para SelectField de procedimento:
    [('', 'Selecione um procedimento'), ('Osteotomia da Pelve', 'Osteotomia da Pelve'), ...]
    """
    procs = get_specialty_procedures(specialty)
    choices = [('', 'Selecione um procedimento')]
    choices += [(p.descricao, p.descricao) for p in procs]
    return choices


def get_procedure_code_map(specialty=None) -> Dict[str, str]:
    """
    Retorna dicionário { descricao: codigo_sus } para uso no template JS.
    """
    procs = get_specialty_procedures(specialty)
    return {p.descricao: (p.codigo_sus or '') for p in procs}


def get_sus_code_for_procedure(descricao: str, specialty=None) -> str:
    """Retorna o código SUS para uma descrição de procedimento."""
    return get_procedure_code_map(specialty).get(descricao, '')


def get_specialty_users(specialty=None) -> List:
    """
    Retorna lista de usuários vinculados à especialidade.
    """
    from src.models.user import User
    sp = specialty or get_active_specialty()
    if sp is None:
        return []
    return User.query.filter_by(specialty_id=sp.id).all()


def get_user_choices(specialty=None) -> List[Tuple[str, str]]:
    """
    Retorna choices para SelectField de assistente.
    [('', 'Selecione um assistente'), ('Dr. Fulano', 'Dr. Fulano'), ...]
    """
    users = get_specialty_users(specialty)
    choices = [('', 'Selecione um assistente')]
    choices += [(u.full_name, u.full_name) for u in users if u.full_name]
    return choices


# ── Context processor helper ──────────────────────────────────────────────────

def specialty_context() -> Dict:
    """
    Retorna dict para injeção como context processor no app Flask.
    Disponibiliza {{ active_specialty }} e {{ active_specialty_name }} em todos os templates.
    """
    try:
        sp = get_active_specialty()
        return {
            'active_specialty': sp.slug if sp else DEFAULT_SPECIALTY_SLUG,
            'active_specialty_name': sp.name if sp else 'Ortopedia',
            'active_specialty_obj': sp,
        }
    except Exception:
        return {
            'active_specialty': DEFAULT_SPECIALTY_SLUG,
            'active_specialty_name': 'Ortopedia',
            'active_specialty_obj': None,
        }
