"""Leitura somente leitura das cirurgias de ortopedia no Access (Ocorrencias_SS).

Tabelas e colunas são constantes (nunca vêm de entrada do usuário) e a estrutura é
validada em tempo de execução por ``SELECT * ... WHERE 1=0``. A conexão, a
configuração e a classificação de erros são as de ``AccessPatientService``.
"""
from __future__ import annotations

import calendar as _calendar
import logging
import os
import re
import threading
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Any

from src.services.access_local_copy import LocalCopyManager
from src.services.access_patient_service import (
    AccessConfig, AccessLookupError, access_patient_service,
)

logger = logging.getLogger(__name__)

SURGERY_TABLE = 'Ocorrencias_SS'
PROCEDURES_TABLE = 'tb_procedimentos_BC'
SUSPENSIONS_TABLE = 'tb_registro_bC'  # registro do bloco: cirurgias realizadas e canceladas
STALE_AFTER_SECONDS = 300  # snapshot mais velho que isto é servido e atualizado em segundo plano
ERROR_COOLDOWN = 30  # após erro, não tenta de novo antes disso (salvo pedido do usuário)
MAX_JOB_SECONDS = 600  # limite entre etapas de uma carga
STUCK_AFTER_SECONDS = 900  # carga "presa" é descartada
DEFAULT_HISTORY_MONTHS = 12
RANGE_CHUNK_MONTHS = 6  # ao voltar no tempo, carrega blocos de 6 meses
MAX_ROWS = 20000
FETCH_BATCH = 500
IN_BATCH = 100
PROCEDURE_TTL = 24 * 3600
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
    covered_from: date | None = None  # primeira data programada carregada
    undated_since: date | None = None  # sem data: só cadastros a partir daqui
    origin: str = 'rede'  # 'rede' ou 'cópia local'


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


# ------------------------------------------------------------------ carregador

def add_months(day: date, months: int) -> date:
    """Primeiro dia do mês ``months`` meses a partir de ``day``."""
    year, month = divmod(day.year * 12 + day.month - 1 + months, 12)
    return date(year, month + 1, 1)


def _as_datetime(day: date) -> datetime:
    return datetime(day.year, day.month, day.day)


@dataclass(frozen=True)
class ViewState:
    """Estado devolvido imediatamente às rotas (nunca espera o Access)."""
    status: str  # 'loading' | 'ready' | 'error'
    snapshot: SurgerySnapshot | None = None
    phase: str = ''
    elapsed: float = 0.0
    reason: str = ''
    error: dict | None = None
    refreshing: bool = False
    age: float | None = None
    loading_range: bool = False


class AccessSurgeryService:
    """Mantém um snapshot em memória das cirurgias de ortopedia.

    As leituras do Access acontecem **em uma thread de segundo plano** (uma por
    vez), com conexão própria somente leitura e consultas filtradas por período.
    As rotas só consultam ``get_view``, que responde na hora.
    """

    def __init__(self, patient_service=None, clock=time.monotonic, background: bool = True,
                 copy_manager=None, history_months: int | None = None):
        self._patients = patient_service or access_patient_service
        self.clock = clock
        self.background = background
        self._copy_manager = copy_manager
        self._history_months = history_months
        self._lock = threading.RLock()
        self._reset_state()

    # -- estado -------------------------------------------------------------

    def _reset_state(self) -> None:
        self._generation = getattr(self, '_generation', 0) + 1
        self._proc_cache = {}
        self._signature = None
        self._status = 'idle'
        self._phase = ''
        self._reason = ''
        self._started_at = 0.0
        self._error: dict | None = None
        self._error_at = 0.0
        self._loaded_at: float | None = None
        self._base_rows: list[SurgeryRow] = []
        self._registry: list[dict] | None = []
        self._warnings: tuple[str, ...] = ()
        self._covered_from: date | None = None
        self._undated_since: date | None = None
        self._origin = 'rede'
        self._synced_at: datetime | None = None
        self._snapshot: SurgerySnapshot | None = None
        self._loading_range = False

    def invalidate(self) -> None:
        with self._lock:
            self._reset_state()

    def configure(self, cache_dir) -> None:
        """Define a pasta da cópia local (``instance/access_cache``)."""
        with self._lock:
            if self._copy_manager is None and cache_dir:
                self._copy_manager = LocalCopyManager(cache_dir)

    def _history(self) -> int:
        if self._history_months is not None:
            return self._history_months
        try:
            return max(1, int(os.environ.get('SURGERY_HISTORY_MONTHS', DEFAULT_HISTORY_MONTHS)))
        except ValueError:
            return DEFAULT_HISTORY_MONTHS

    def _check_signature(self, config: AccessConfig) -> None:
        if self._signature != config.signature:
            self._reset_state()
            self._signature = config.signature

    def _view(self) -> ViewState:
        now = self.clock()
        age = None if self._loaded_at is None else now - self._loaded_at
        if self._status == 'loading':
            return ViewState('loading', self._snapshot, self._phase, now - self._started_at, self._reason,
                             refreshing=self._snapshot is not None, age=age, loading_range=self._loading_range)
        if self._snapshot is not None:
            failed = self._error if self._status == 'error' else None
            return ViewState('ready', self._snapshot, age=age, error=failed)
        if self._status == 'error':
            return ViewState('error', error=self._error, reason=self._reason)
        return ViewState('loading', phase='Iniciando', reason=self._reason)

    # -- API usada pelas rotas ----------------------------------------------

    def get_view(self, config: AccessConfig, today: date | None = None) -> ViewState:
        """Estado atual. Inicia a carga inicial ou a atualização em segundo plano se preciso."""
        with self._lock:
            self._check_signature(config)
            now = self.clock()
            if self._status == 'loading' and now - self._started_at > STUCK_AFTER_SECONDS:
                self._generation += 1  # o resultado da thread presa será descartado
                self._fail(self._generation, AccessLookupError(
                    'ACCESS_TIMEOUT', 'A leitura do banco do CPAM demorou demais e foi interrompida.',
                    'Verifique a rede e o tamanho do banco; use "Tentar novamente".', 504))
            if self._status != 'loading':
                cooling = self._status == 'error' and now - self._error_at < ERROR_COOLDOWN
                if self._snapshot is None and not cooling:
                    self._start_full(config, today or date.today(), 'Carga inicial')
                elif (self._snapshot is not None and self._loaded_at is not None
                      and now - self._loaded_at > STALE_AFTER_SECONDS and not cooling):
                    self._start_full(config, today or date.today(), 'Atualização')
            return self._view()

    def refresh(self, config: AccessConfig, today: date | None = None) -> ViewState:
        """Atualização pedida pelo usuário (ignora o intervalo de espera após erro)."""
        with self._lock:
            self._check_signature(config)
            if self._status != 'loading':
                self._start_full(config, today or date.today(), 'Atualização manual', force_copy=True)
            return self._view()

    def ensure_range(self, config: AccessConfig, start: date) -> ViewState:
        """Garante que ``start`` esteja carregado; busca períodos anteriores em segundo plano."""
        with self._lock:
            self._check_signature(config)
            covered = self._covered_from
            if (self._status != 'loading' and self._snapshot is not None and covered is not None
                    and start < covered):
                new_from = add_months(start, -(RANGE_CHUNK_MONTHS - 1))
                self._start_range(config, new_from, covered)
            return self._view()

    def is_covered(self, day: date) -> bool:
        with self._lock:
            return self._covered_from is not None and day >= self._covered_from

    # -- disparo das threads -------------------------------------------------

    def _begin(self, reason: str, phase: str) -> int:
        self._status, self._reason, self._phase = 'loading', reason, phase
        self._started_at = self.clock()
        self._error = None
        return self._generation

    def _start_full(self, config: AccessConfig, today: date, reason: str, force_copy: bool = False) -> None:
        generation = self._begin(reason, 'Preparando')
        self._loading_range = False
        window_start = add_months(today, -self._history())
        self._spawn(lambda: self._run_job(config, generation, window_start, None, True, force_copy))

    def _start_range(self, config: AccessConfig, start: date, end: date) -> None:
        generation = self._begin('Período anterior', 'Preparando')
        self._loading_range = True
        self._spawn(lambda: self._run_job(config, generation, start, end, False, False))

    def _spawn(self, target) -> None:
        if not self.background:
            target()
            return
        thread = threading.Thread(target=target, name='surgery-loader', daemon=True)
        thread.start()

    def _set_phase(self, generation: int, phase: str) -> None:
        with self._lock:
            if generation == self._generation:
                self._phase = phase

    # -- execução da carga (thread própria) -----------------------------------

    def _run_job(self, config, generation, start, end, full: bool, force_copy: bool) -> None:
        began = self.clock()
        try:
            result = self._read_range(config, generation, start, end, full, force_copy, began)
        except AccessLookupError as exc:
            self._fail(generation, exc)
            return
        except ValueError:
            self._fail(generation, AccessLookupError(
                'ACCESS_CONFIG_INVALID', 'A configuração do banco Access é inválida.',
                'Revise o banco Access nas Configurações.', 503))
            return
        except Exception as exc:  # defesa final: a tela nunca deve ficar presa em "carregando"
            logger.exception('Falha inesperada ao carregar cirurgias (%s).', type(exc).__name__)
            self._fail(generation, AccessLookupError(
                'SURGERY_LOAD_FAILED', 'Não foi possível carregar as cirurgias.',
                'Tente novamente; se persistir, consulte o log do sistema.', 500))
            return
        with self._lock:
            if generation != self._generation:
                return  # resultado descartado (config mudou ou carga travada anterior)
            raw_rows, registry, registry_ok, warnings, origin, undated_since = result
            if full:
                self._base_rows, self._registry = list(raw_rows), (registry if registry_ok else None)
                self._covered_from, self._undated_since = start, undated_since
            else:
                self._base_rows = list(raw_rows) + self._base_rows
                if registry_ok and self._registry is not None:
                    self._registry = registry + self._registry
                elif not registry_ok:
                    self._registry = None
                self._covered_from = start
            self._warnings = tuple(dict.fromkeys(warnings))
            self._origin = origin
            self._assemble()
            self._status, self._phase, self._loading_range = 'ready', '', False
            self._loaded_at = self.clock()
            logger.info('Cirurgias carregadas (%s): %d linhas em %.1f s', 'completa' if full else 'período',
                        len(self._base_rows), self.clock() - began)

    def _fail(self, generation: int, exc: AccessLookupError) -> None:
        with self._lock:
            if generation != self._generation:
                return
            logger.warning('Carga de cirurgias falhou: %s', exc.code)
            self._status, self._phase, self._loading_range = 'error', '', False
            self._error = {'message': exc.message, 'hint': exc.hint, 'code': exc.code}
            self._error_at = self.clock()

    def _assemble(self) -> None:
        rows = link_suspensions(list(self._base_rows), self._registry)
        self._synced_at = datetime.now()
        self._snapshot = SurgerySnapshot(
            tuple(rows), self._warnings, self._synced_at, self._covered_from, self._undated_since, self._origin)

    def _deadline(self, began: float) -> None:
        if self.clock() - began > MAX_JOB_SECONDS:
            raise AccessLookupError('ACCESS_TIMEOUT', 'A leitura do banco do CPAM demorou demais e foi interrompida.',
                                    'Verifique a rede e o tamanho do banco; use "Tentar novamente".', 504)

    def _read_range(self, config, generation, start: date, end: date | None, full: bool,
                    force_copy: bool, began: float):
        warnings: list[str] = []
        candidates: list[tuple[AccessConfig, str]] = []
        self._set_phase(generation, 'Copiando banco para o disco local')
        manager = self._copy_manager
        if manager is not None:
            local, note, info = manager.prepare(config, force=force_copy)
            if note:
                warnings.append(note)
            if local is not None:
                if info.get('copied'):
                    logger.info('Cópia local do Access: %.1f MB em %.1f s', info['megabytes'], info['seconds'])
                candidates.append((local, 'cópia local'))
        candidates.append((config, 'rede'))
        base_warnings = list(warnings)
        last_error: Exception | None = None
        for index, (candidate, origin) in enumerate(candidates):
            try:
                with self._patients.open_readonly(candidate) as connection:
                    data = self._read_with(connection, generation, start, end, full, warnings, began)
                return (*data, warnings, origin, start if full else self._undated_since)
            except Exception as exc:
                last_error = exc
                if index < len(candidates) - 1:
                    logger.warning('Leitura pela cópia local falhou (%s); usando a rede.', type(exc).__name__)
                    warnings[:] = base_warnings + ['Não foi possível ler a cópia local; consulta feita direto pela rede.']
                    base_warnings = list(warnings)
                    continue
                raise
        raise last_error  # pragma: no cover

    # -- consultas -------------------------------------------------------------

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

    def _query(self, connection, table: str, columns: dict[str, str], where: str = '',
               params: tuple = (), cap: int | None = None) -> tuple[list[dict], bool]:
        """SELECT parametrizado, lido em lotes. ``where`` só contém identificadores
        já descobertos no schema (entre colchetes) e literais constantes."""
        cap = MAX_ROWS if cap is None else cap
        quote = self._patients._quote
        selected = list(columns.items())
        sql = f'SELECT {", ".join(quote(real) for _, real in selected)} FROM {quote(table)}'
        if where:
            sql += f' WHERE {where}'
        cursor = connection.cursor()
        try:
            cursor.execute(sql, *params)
            rows: list[dict] = []
            while True:
                batch = cursor.fetchmany(FETCH_BATCH)
                if not batch:
                    return rows, False
                rows.extend({name: raw[i] for i, (name, _) in enumerate(selected)} for raw in batch)
                if len(rows) >= cap:
                    return rows[:cap], True
        finally:
            self._close(cursor)

    def _ortho_filter(self, column: str) -> str:
        # vbTextCompare (1): sem diferenciar caixa. 'ortop' cobre ORTOPEDIA/ORTOPÉDICA.
        return f"InStr(1, {self._patients._quote(column)}, 'ortop', 1) > 0"

    def _read_with(self, connection, generation, start: date, end: date | None, full: bool,
                   warnings: list[str], began: float):
        quote = self._patients._quote
        stage = self.clock()

        def lap(name: str, count: int) -> None:
            now = self.clock()
            logger.info('Cirurgias etapa=%s linhas=%d segundos=%.1f', name, count, now - stage)

        # 1) cirurgias
        self._set_phase(generation, 'Lendo cirurgias')
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
        prog, esp = columns['programada'], columns['especialidade']
        where = f'{quote(prog)} >= ?'
        params: list = [_as_datetime(start)]
        if end is not None:
            where += f' AND {quote(prog)} < ?'
            params.append(_as_datetime(end))
        raw_rows, truncated = self._query(connection, SURGERY_TABLE, columns,
                                          f'{where} AND {self._ortho_filter(esp)}', tuple(params))
        if truncated:
            warnings.append(f'Limite de {MAX_ROWS} cirurgias por consulta atingido: reduza o período ou procure a equipe técnica.')
        if full:  # sem data programada: só cadastros recentes (mesma janela do histórico)
            undated_where = f'{quote(prog)} IS NULL AND {self._ortho_filter(esp)}'
            undated_params: tuple = ()
            if 'cadastro' in columns:
                undated_where += f' AND {quote(columns["cadastro"])} >= ?'
                undated_params = (_as_datetime(start),)
            undated, undated_truncated = self._query(connection, SURGERY_TABLE, columns, undated_where, undated_params)
            raw_rows += [raw for raw in undated if raw.get('programada') is None]  # defesa: sem duplicar as já datadas
            if undated_truncated:
                warnings.append(f'Limite de {MAX_ROWS} cirurgias sem data atingido; a lista está incompleta.')
        lap('cirurgias', len(raw_rows))
        self._deadline(began)

        # 2) registro do bloco (opcional)
        self._set_phase(generation, 'Lendo registro do bloco')
        stage = self.clock()
        registry, registry_ok = self._read_registry(connection, start, end, warnings)
        lap('registro_bloco', len(registry))
        self._deadline(began)

        # 3) nomes dos procedimentos (só os códigos usados)
        self._set_phase(generation, 'Buscando nomes dos procedimentos')
        stage = self.clock()
        ortho = [raw for raw in raw_rows if is_orthopedics(raw.get('especialidade'))]
        names_by_code = self._read_procedures(connection, ortho, warnings)
        lap('procedimentos', len(names_by_code))

        rows = []
        for raw in ortho:
            status, status_raw = classify_status(raw.get('status'))
            code = _clean_id(raw.get('procedimento'))
            rows.append(SurgeryRow(
                prontuario=_clean_id(raw.get('prontuario')),
                paciente=_text(raw.get('nome')),
                cadastro=parse_date(raw.get('cadastro')),
                medico=_text(raw.get('medico')),
                especialidade=_text(raw.get('especialidade')),
                procedimento_codigo=code,
                procedimento_nome=names_by_code.get(_code_key(code), '') if code else '',
                programada=parse_date(raw.get('programada')),
                observacoes=_text(raw.get('observacoes')),
                status=status,
                status_bruto=status_raw,
            ))
        return rows, registry, registry_ok

    def _read_registry(self, connection, start: date, end: date | None, warnings: list[str]):
        quote = self._patients._quote
        try:
            names = self._describe(connection, SUSPENSIONS_TABLE)
            columns = self._map_columns(names, SUSPENSION_ALIASES)
            missing = [key for key in SUSPENSION_REQUIRED if key not in columns]
            if missing:
                warnings.append('Motivos de cancelamento indisponíveis: colunas ausentes em tb_registro_bC (' + ', '.join(missing) + ').')
                return [], False
            date_col = quote(columns['data'])
            where = f'{date_col} >= ?'
            params: list = [_as_datetime(start)]
            if end is not None:
                where += f' AND {date_col} < ?'
                params.append(_as_datetime(end))
            data, truncated = self._query(connection, SUSPENSIONS_TABLE, columns,
                                          f'{where} AND {self._ortho_filter(columns["especialidade"])}', tuple(params))
            if truncated:
                warnings.append(f'Limite de {MAX_ROWS} registros do bloco atingido; alguns motivos podem faltar.')
        except Exception as exc:
            self._patients._log_odbc_failure('registro_bloco_cirurgias', exc)
            warnings.append('Motivos de cancelamento indisponíveis: não foi possível ler tb_registro_bC.')
            return [], False
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
        return result, True

    def _read_procedures(self, connection, raw_rows: list[dict], warnings: list[str]) -> dict[str, str]:
        """Código → nome, consultando só os códigos usados (e guardando por 24 h)."""
        now = self.clock()
        wanted: dict[str, object] = {}
        for raw in raw_rows:
            value = raw.get('procedimento')
            key = _code_key(value)
            if key and value is not None and key not in wanted:
                wanted[key] = value
        result: dict[str, str] = {}
        pending: dict[str, object] = {}
        for key, value in wanted.items():
            cached = self._proc_cache.get(key)
            if cached and now - cached[1] < PROCEDURE_TTL:
                result[key] = cached[0]
            else:
                pending[key] = value
        if not pending:
            return result
        try:
            names = self._describe(connection, PROCEDURES_TABLE)
            by_key = {_column_key(n): n for n in names}
            code_col = next((by_key[_column_key(a)] for a in PROCEDURE_CODE_ALIASES if _column_key(a) in by_key), None)
            name_col = next((by_key[_column_key(a)] for a in PROCEDURE_NAME_ALIASES
                             if _column_key(a) in by_key and by_key[_column_key(a)] != code_col), None)
            if not code_col or not name_col:
                warnings.append('Nomes de procedimentos indisponíveis: colunas de código/nome não identificadas em tb_procedimentos_BC.')
                return result
            quote = self._patients._quote
            keys, values = list(pending), list(pending.values())
            for offset in range(0, len(values), IN_BATCH):
                chunk = values[offset:offset + IN_BATCH]
                marks = ', '.join('?' for _ in chunk)
                data, _ = self._query(connection, PROCEDURES_TABLE, {'codigo': code_col, 'nome': name_col},
                                      f'{quote(code_col)} IN ({marks})', tuple(chunk), cap=len(chunk) * 4)
                for item in data:
                    if item['codigo'] is not None:
                        result[_code_key(item['codigo'])] = _text(item['nome'])
            for key in keys:
                self._proc_cache[key] = (result.get(key, ''), now)
        except Exception as exc:
            self._patients._log_odbc_failure('procedimentos_cirurgias', exc)
            warnings.append('Nomes de procedimentos indisponíveis: não foi possível ler tb_procedimentos_BC.')
        return result


access_surgery_service = AccessSurgeryService()
