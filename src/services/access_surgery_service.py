"""Leitura somente leitura das cirurgias de ortopedia no Access (Ocorrencias_SS).

Tabelas e colunas são constantes (nunca vêm de entrada do usuário) e a estrutura é
validada em tempo de execução por ``SELECT * ... WHERE 1=0``. A conexão, a
configuração e a classificação de erros são as de ``AccessPatientService``.
"""
from __future__ import annotations

import calendar as _calendar
import logging
import re
import threading
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Any

from src.services.access_patient_service import (
    AccessConfig, AccessLookupError, access_patient_service,
)

logger = logging.getLogger(__name__)

SURGERY_TABLE = 'Ocorrencias_SS'
PROCEDURES_TABLE = 'tb_procedimentos_BC'
SUSPENSIONS_TABLE = 'tb_registro_bC'  # registro do bloco: cirurgias realizadas e canceladas
SNAPSHOT_TTL = 180  # segundos
MIN_VALID_YEAR = 1950  # datas "zero" do Access (1899/1900) são tratadas como inválidas

STATUS_NO_ANSWER, STATUS_CANCELED, STATUS_DONE, STATUS_UNKNOWN = 'sem_resposta', 'cancelada', 'realizada', 'desconhecido'
STATUS_LABELS = {
    STATUS_NO_ANSWER: 'Sem resposta do bloco',
    STATUS_CANCELED: 'Cancelada',
    STATUS_DONE: 'Realizada',
    STATUS_UNKNOWN: 'Status desconhecido',
}
_STATUS_BY_CODE = {0: STATUS_CANCELED, 1: STATUS_DONE}  # nulo = sem resposta do bloco

LINK_CONFIRMED, LINK_MISSING, LINK_AMBIGUOUS, LINK_UNAVAILABLE = 'confirmado', 'nao_localizado', 'ambiguo', 'indisponivel'
LINK_DIVERGENT = 'divergente'
LINK_LABELS = {
    LINK_MISSING: 'Motivo não localizado',
    LINK_DIVERGENT: 'Divergência: o registro do bloco indica cirurgia realizada',
    LINK_AMBIGUOUS: 'Vínculo ambíguo: mais de uma suspensão corresponde a esta cirurgia',
    LINK_UNAVAILABLE: 'Motivos indisponíveis (tabela de suspensões não pôde ser lida)',
}
NO_GROUP_LABEL = 'Sem grupo informado'

SURGERY_ALIASES = {
    'prontuario': ('prontuario',),
    'nome': ('nome do paciente', 'nome_paciente', 'nome paciente', 'nome', 'paciente'),
    'cadastro': ('dt_atend_cons',),
    'medico': ('nome_medico_cons',),
    'especialidade': ('especialidade_cons',),
    'procedimento': ('procedimento_cir',),
    'programada': ('dt_prov_CIR',),
    'observacoes': ('orientaçao_ss', 'orientacao_ss', 'orientacao ss'),
    'status': ('CIRURGIA_agendada',),
}
SURGERY_REQUIRED = ('prontuario', 'nome', 'especialidade', 'programada', 'status')

PROCEDURE_CODE_ALIASES = ('codigo_sus', 'cod_sus', 'codigo', 'cod', 'co_procedimento', 'procedimento_cir', 'procedimento', 'id')
PROCEDURE_NAME_ALIASES = ('nome_procedimento', 'no_procedimento', 'nome', 'descricao', 'procedimento')

# Nomes reais das colunas de tb_registro_bC (chave interna → coluna no Access).
# Obs.: Mot_Cancelam é o grupo (MOTIVO) e Obs_Cancelam o motivo específico.
SUSPENSION_ALIASES = {
    'nome': ('Nome_Paciente',),
    'especialidade': ('Especialidade',),
    'data': ('Data_da_Cirurgia',),
    'motivo': ('Mot_Cancelam',),
    'descricao': ('Obs_Cancelam',),
    'situacao': ('Situaçao',),  # opcional: CANCELADA, REALIZADA ou nulo
}
SUSPENSION_REQUIRED = ('nome', 'especialidade', 'data', 'motivo')


# ---------------------------------------------------------------- helpers puros

def normalize_text(value) -> str:
    """Sem acentos, caixa baixa, pontuação trocada por espaço e espaços colapsados."""
    text = unicodedata.normalize('NFKD', str(value if value is not None else ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', text).split())


def _column_key(name) -> str:
    return normalize_text(name).replace(' ', '')


def is_orthopedics(value) -> bool:
    return 'ortoped' in normalize_text(value)


def parse_date(value) -> date | None:
    """Converte valores do Access/strings em ``date``; nulo, inválido ou "zero" → None."""
    if value is None:
        return None
    result = None
    if isinstance(value, datetime):
        result = value.date()
    elif isinstance(value, date):
        result = value
    else:
        raw = str(value).strip()
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
            try:
                result = datetime.strptime(raw[:19], fmt).date()
                break
            except ValueError:
                continue
    if result is None or result.year < MIN_VALID_YEAR:
        return None
    return result


def classify_status(value) -> tuple[str, str]:
    """(status, valor_bruto): 0 cancelada, 1 realizada, nulo sem resposta do bloco.

    Qualquer outro valor (inclusive texto, decimais e booleanos) é desconhecido.
    """
    raw = '' if value is None else str(value).strip()
    if value is None or not raw:
        return STATUS_NO_ANSWER, ''
    if isinstance(value, bool):
        return STATUS_UNKNOWN, raw
    try:
        number = float(raw.replace(',', '.'))
    except ValueError:
        return STATUS_UNKNOWN, raw
    if number != number or number in (float('inf'), float('-inf')) or number != int(number):
        return STATUS_UNKNOWN, raw
    return _STATUS_BY_CODE.get(int(number), STATUS_UNKNOWN), str(int(number))


def _clean_id(value) -> str:
    text = str(value if value is not None else '').strip()
    return text[:-2] if text.endswith('.0') and text[:-2].isdigit() else text


def _text(value) -> str:
    return str(value if value is not None else '').strip()


def _code_key(value) -> str:
    return _column_key(_clean_id(value))


@dataclass(frozen=True)
class SuspensionLink:
    estado: str
    grupo: str = ''
    descricao: str = ''
    candidatas: int = 0

    @property
    def label(self) -> str:
        return LINK_LABELS.get(self.estado, '')


@dataclass(frozen=True)
class SurgeryRow:
    prontuario: str
    paciente: str
    cadastro: date | None
    medico: str
    especialidade: str
    procedimento_codigo: str
    procedimento_nome: str  # '' quando não localizado
    programada: date | None
    observacoes: str
    status: str
    status_bruto: str
    vinculo: SuspensionLink | None = None

    @property
    def status_label(self) -> str:
        if self.status == STATUS_UNKNOWN:
            return f'Status desconhecido ({self.status_bruto or "vazio"})'
        return STATUS_LABELS[self.status]

    @property
    def sem_data(self) -> bool:
        return self.programada is None


@dataclass(frozen=True)
class SurgerySnapshot:
    rows: tuple[SurgeryRow, ...]
    warnings: tuple[str, ...]
    synced_at: datetime
    source: str = 'access'


def link_suspensions(rows: list[SurgeryRow], suspensions: list[dict] | None) -> list[SurgeryRow]:
    """Associa cancelamentos de tb_registro_bC (Nome_Paciente + Especialidade + Data_da_Cirurgia normalizados).

    ``suspensions=None`` indica tabela indisponível. Mais de uma correspondência é
    ambígua: nenhum motivo é confirmado.
    """
    index: dict[tuple, list[dict]] = defaultdict(list)
    done_index: set[tuple] = set()
    for item in suspensions or ():
        if item['data'] is None or not item['nome'] or not item['especialidade']:
            continue
        key = (item['nome'], item['especialidade'], item['data'])
        if item.get('tipo', 'cancelada') == 'realizada':
            done_index.add(key)
        else:
            index[key].append(item)
    linked = []
    for row in rows:
        if row.status != STATUS_CANCELED:
            linked.append(row)
            continue
        if suspensions is None:
            link = SuspensionLink(LINK_UNAVAILABLE)
        else:
            key = (normalize_text(row.paciente), normalize_text(row.especialidade), row.programada)
            matches = index.get(key, []) if row.programada else []
            if not matches:
                diverges = bool(row.programada) and key in done_index
                link = SuspensionLink(LINK_DIVERGENT if diverges else LINK_MISSING)
            elif len(matches) > 1:
                link = SuspensionLink(LINK_AMBIGUOUS, candidatas=len(matches))
            else:
                link = SuspensionLink(LINK_CONFIRMED, matches[0]['motivo'], matches[0]['descricao'], 1)
        linked.append(replace(row, vinculo=link))
    return linked


def registry_kind(situacao, motivo, descricao) -> str:
    """Classifica uma linha de tb_registro_bC: 'cancelada', 'realizada' ou '' (ignorar).

    ``Situaçao`` é a fonte principal. Quando está vazia ou desconhecida, a linha só
    é tratada como cancelamento se tiver motivo ou observação de cancelamento.
    """
    situation = normalize_text(situacao)
    if situation.startswith('cancel'):
        return 'cancelada'
    if situation.startswith('realiz'):
        return 'realizada'
    return 'cancelada' if (_text(motivo) or _text(descricao)) else ''


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())  # segunda-feira


def period_bounds(view: str, anchor: date) -> tuple[date, date]:
    """Primeiro e último dia (inclusive) do período. Semana: segunda a domingo."""
    if view == 'week':
        start = week_start(anchor)
        return start, start + timedelta(days=6)
    last = _calendar.monthrange(anchor.year, anchor.month)[1]
    return anchor.replace(day=1), anchor.replace(day=last)


def shift_anchor(view: str, anchor: date, direction: int) -> date:
    if view == 'week':
        return anchor + timedelta(days=7 * direction)
    year, month = divmod(anchor.year * 12 + anchor.month - 1 + direction, 12)
    return date(year, month + 1, 1)


def rows_in_period(rows, start: date, end: date) -> list[SurgeryRow]:
    selected = [r for r in rows if r.programada is not None and start <= r.programada <= end]
    selected.sort(key=lambda r: (r.programada, normalize_text(r.paciente)))
    return selected


def count_by_status(rows) -> dict[str, int]:
    counts = {STATUS_NO_ANSWER: 0, STATUS_CANCELED: 0, STATUS_DONE: 0, STATUS_UNKNOWN: 0}
    for row in rows:
        counts[row.status] += 1
    counts['total'] = sum(counts.values())
    return counts


def build_calendar(view: str, anchor: date, rows, today: date) -> dict[str, Any]:
    """Grade do calendário (semanas começando na segunda) com as cirurgias por dia."""
    start, end = period_bounds(view, anchor)
    by_day: dict[date, list[SurgeryRow]] = defaultdict(list)
    for row in rows_in_period(rows, start, end):
        by_day[row.programada].append(row)
    grid_end = week_start(end) + timedelta(days=6)
    weeks, day = [], week_start(start)
    while day <= grid_end:
        week = []
        for _ in range(7):
            day_rows = by_day.get(day, [])
            week.append({
                'date': day,
                'in_period': start <= day <= end,
                'is_today': day == today,
                'rows': day_rows,
                'counts': count_by_status(day_rows),
            })
            day += timedelta(days=1)
        weeks.append(week)
    return {'view': view, 'start': start, 'end': end, 'weeks': weeks}


def suspension_summary(rows) -> dict[str, Any]:
    """Resumo por motivo (Mot_Cancelam) das cirurgias canceladas do período (já filtradas)."""
    groups: dict[str, dict] = {}
    summary = {'total': 0, 'ambiguous': 0, 'missing': 0, 'unavailable': 0, 'divergent': 0}
    for row in rows:
        if row.status != STATUS_CANCELED:
            continue
        summary['total'] += 1
        link = row.vinculo
        if link is None or link.estado == LINK_MISSING:
            summary['missing'] += 1
        elif link.estado == LINK_AMBIGUOUS:
            summary['ambiguous'] += 1
        elif link.estado == LINK_UNAVAILABLE:
            summary['unavailable'] += 1
        elif link.estado == LINK_DIVERGENT:
            summary['divergent'] += 1
        else:
            label = link.grupo.strip() or NO_GROUP_LABEL
            group = groups.setdefault(normalize_text(label), {'grupo': label, 'cases': []})
            group['cases'].append(row)
    ordered = sorted(groups.values(), key=lambda g: (-len(g['cases']), normalize_text(g['grupo'])))
    for group in ordered:
        group['count'] = len(group['cases'])
    summary['groups'] = ordered
    return summary


def filter_list(rows, status: str = '', query: str = '') -> list[SurgeryRow]:
    needle = normalize_text(query)
    result = []
    for row in rows:
        if status and row.status != status:
            continue
        if needle and needle not in normalize_text(row.paciente) and needle not in normalize_text(row.prontuario):
            continue
        result.append(row)
    return result


# ------------------------------------------------------------------ serviço

class AccessSurgeryService:
    def __init__(self, patient_service=None, clock=time.monotonic):
        self._patients = patient_service or access_patient_service
        self.clock = clock
        self._lock = threading.RLock()
        self._cache: tuple[tuple, float, SurgerySnapshot] | None = None

    def invalidate(self) -> None:
        with self._lock:
            self._cache = None

    def load(self, config: AccessConfig, force: bool = False) -> SurgerySnapshot:
        with self._lock:
            now = self.clock()
            cached = self._cache
            if not force and cached and cached[0] == config.signature and cached[1] > now:
                return replace(cached[2], source='memory_cache')
            snapshot = self._patients.run_read(config, self._read_all, 'cirurgias')
            self._cache = (config.signature, now + SNAPSHOT_TTL, snapshot)
            return snapshot

    # -- leitura -----------------------------------------------------------

    @staticmethod
    def _close(cursor) -> None:
        try:
            cursor.close()
        except Exception:
            pass

    def _describe(self, connection, table: str) -> list[str]:
        cursor = connection.cursor()
        try:
            cursor.execute(f'SELECT * FROM {self._patients._quote(table)} WHERE 1=0')
            return [str(c[0]) for c in (cursor.description or []) if c and c[0]]
        finally:
            self._close(cursor)

    @staticmethod
    def _map_columns(names: list[str], aliases: dict[str, tuple[str, ...]]) -> dict[str, str]:
        by_key = {_column_key(name): name for name in names}
        mapping = {}
        for canonical, options in aliases.items():
            for option in options:
                if _column_key(option) in by_key:
                    mapping[canonical] = by_key[_column_key(option)]
                    break
        return mapping

    def _select(self, connection, table: str, columns: dict[str, str]) -> list[dict]:
        quote = self._patients._quote
        selected = list(columns.items())
        sql = f'SELECT {", ".join(quote(real) for _, real in selected)} FROM {quote(table)}'
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            return [{name: raw[i] for i, (name, _) in enumerate(selected)} for raw in cursor.fetchall()]
        finally:
            self._close(cursor)

    def _read_all(self, connection) -> SurgerySnapshot:
        warnings: list[str] = []
        try:
            names = self._describe(connection, SURGERY_TABLE)
        except Exception as exc:
            if self._patients._is_missing_table_error(exc):
                raise AccessLookupError(
                    'ACCESS_SURGERY_TABLE_NOT_FOUND', 'A tabela de cirurgias não foi encontrada no banco do CPAM.',
                    'Verifique se o arquivo Access configurado é o correto e contém a tabela Ocorrencias_SS.', 502,
                ) from exc
            raise
        columns = self._map_columns(names, SURGERY_ALIASES)
        missing = [key for key in SURGERY_REQUIRED if key not in columns]
        if missing:
            raise AccessLookupError(
                'ACCESS_SURGERY_COLUMNS_MISSING', 'A tabela de cirurgias não possui as colunas esperadas.',
                'Colunas ausentes (nomes internos): ' + ', '.join(missing) + '.', 502,
            )
        raw_rows = self._select(connection, SURGERY_TABLE, columns)
        procedures = self._read_procedures(connection, warnings)
        suspensions = self._read_suspensions(connection, warnings)

        rows = []
        for raw in raw_rows:
            if not is_orthopedics(raw.get('especialidade')):
                continue
            status, status_raw = classify_status(raw.get('status'))
            code = _clean_id(raw.get('procedimento'))
            rows.append(SurgeryRow(
                prontuario=_clean_id(raw.get('prontuario')),
                paciente=_text(raw.get('nome')),
                cadastro=parse_date(raw.get('cadastro')),
                medico=_text(raw.get('medico')),
                especialidade=_text(raw.get('especialidade')),
                procedimento_codigo=code,
                procedimento_nome=procedures.get(_code_key(code), '') if code else '',
                programada=parse_date(raw.get('programada')),
                observacoes=_text(raw.get('observacoes')),
                status=status,
                status_bruto=status_raw,
            ))
        rows = link_suspensions(rows, suspensions)
        logger.info('Cirurgias de ortopedia carregadas do Access: %d', len(rows))
        return SurgerySnapshot(tuple(rows), tuple(warnings), datetime.now())

    def _read_procedures(self, connection, warnings: list[str]) -> dict[str, str]:
        try:
            names = self._describe(connection, PROCEDURES_TABLE)
            by_key = {_column_key(n): n for n in names}
            code_col = next((by_key[_column_key(a)] for a in PROCEDURE_CODE_ALIASES if _column_key(a) in by_key), None)
            name_col = next((by_key[_column_key(a)] for a in PROCEDURE_NAME_ALIASES
                             if _column_key(a) in by_key and by_key[_column_key(a)] != code_col), None)
            if not code_col or not name_col:
                warnings.append('Nomes de procedimentos indisponíveis: colunas de código/nome não identificadas em tb_procedimentos_BC.')
                return {}
            data = self._select(connection, PROCEDURES_TABLE, {'codigo': code_col, 'nome': name_col})
            return {_code_key(item['codigo']): _text(item['nome']) for item in data if item['codigo'] is not None}
        except Exception as exc:
            self._patients._log_odbc_failure('procedimentos_cirurgias', exc)
            warnings.append('Nomes de procedimentos indisponíveis: não foi possível ler tb_procedimentos_BC.')
            return {}

    def _read_suspensions(self, connection, warnings: list[str]) -> list[dict] | None:
        try:
            names = self._describe(connection, SUSPENSIONS_TABLE)
            columns = self._map_columns(names, SUSPENSION_ALIASES)
            missing = [key for key in SUSPENSION_REQUIRED if key not in columns]
            if missing:
                warnings.append('Motivos de cancelamento indisponíveis: colunas ausentes em tb_registro_bC (' + ', '.join(missing) + ').')
                return None
            data = self._select(connection, SUSPENSIONS_TABLE, columns)
        except Exception as exc:
            self._patients._log_odbc_failure('suspensoes_cirurgias', exc)
            warnings.append('Motivos de cancelamento indisponíveis: não foi possível ler tb_registro_bC.')
            return None
        # tb_registro_bC também registra cirurgias realizadas. A coluna Situaçao
        # separa cancelamentos de realizadas; linhas sem situação só valem como
        # cancelamento se tiverem motivo ou observação (ver registry_kind).
        result = []
        for item in data:
            if not is_orthopedics(item.get('especialidade')):
                continue
            kind = registry_kind(item.get('situacao'), item.get('motivo'), item.get('descricao'))
            if not kind:
                continue
            result.append({
                'nome': normalize_text(item.get('nome')),
                'especialidade': normalize_text(item.get('especialidade')),
                'data': parse_date(item.get('data')),
                'tipo': kind,
                'motivo': _text(item.get('motivo')),
                'descricao': _text(item.get('descricao')),
            })
        return result


access_surgery_service = AccessSurgeryService()
