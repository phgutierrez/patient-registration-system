from __future__ import annotations

import difflib
import logging
import re
import threading
import time
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path, PureWindowsPath
from typing import Any

try:
    import pyodbc
except ImportError:  # pragma: no cover - depends on deployment architecture
    pyodbc = None

logger = logging.getLogger(__name__)
ACCESS_DRIVER = 'Microsoft Access Driver (*.mdb, *.accdb)'
TABLE_NAME = 'cadastro_de_pacientes'
OCORRENCIAS_TABLE = 'Ocorrencias'
DAY_CACHE_TTL = 180  # segundos — agenda do dia sincroniza a cada 3 minutos


class AccessLookupError(RuntimeError):
    def __init__(self, code: str, message: str, hint: str, status: int = 502):
        super().__init__(message)
        self.code, self.message, self.hint, self.status = code, message, hint, status

    def payload(self) -> dict[str, Any]:
        return {'ok': False, 'found': False, 'code': self.code, 'message': self.message, 'hint': self.hint, 'data': None}


@dataclass(frozen=True)
class AccessConfig:
    host: str
    share_path: str
    filename: str
    enabled: bool = True
    source: str = 'network'
    local_path: str | None = None

    @property
    def signature(self) -> tuple[str, str, str, bool, str, str]:
        return (
            (self.host or '').lower(),
            (self.share_path or '').lower(),
            (self.filename or '').lower(),
            self.enabled,
            (self.source or '').lower(),
            (self.local_path or '').lower(),
        )

    @property
    def unc_path(self) -> str:
        validate_access_config(self)
        if (self.source or '').strip().lower() != 'network':
            raise ValueError('O caminho UNC está disponível somente no modo de rede.')
        return str(PureWindowsPath(f'//{self.host}/{self.share_path}/{self.filename}'))

    @property
    def database_path(self) -> str:
        validate_access_config(self)
        if (self.source or '').strip().lower() == 'local':
            return str(PureWindowsPath(str(self.local_path)))
        return str(PureWindowsPath(f'//{self.host}/{self.share_path}/{self.filename}'))


def validate_access_config(config: AccessConfig) -> None:
    source = (config.source or '').strip().lower()
    if source not in {'network', 'local'}:
        raise ValueError('Selecione banco em rede ou arquivo local.')
    if source == 'local':
        local_value = (config.local_path or '').strip()
        local_path = PureWindowsPath(local_value)
        if not local_value or not local_path.is_absolute() or not local_path.drive or local_value.startswith(('\\\\', '//')):
            raise ValueError('Selecione um arquivo local com caminho absoluto neste computador.')
        if local_path.suffix.lower() not in {'.accdb', '.mdb'}:
            raise ValueError('O arquivo local deve possuir extensão .accdb ou .mdb.')
        return

    host = (config.host or '').strip()
    share = (config.share_path or '').strip().strip('\\')
    filename = (config.filename or '').strip()
    if not host or not re.fullmatch(r'[A-Za-z0-9.-]{1,255}', host) or '://' in host:
        raise ValueError('Informe um IP ou nome de servidor válido.')
    if not share or '..' in share.split('\\') or ':' in share or '/' in share or share.startswith('\\'):
        raise ValueError('Informe o compartilhamento e as subpastas sem servidor, unidade ou caminho relativo.')
    if any(not part.strip() for part in share.split('\\')):
        raise ValueError('O caminho do compartilhamento contém uma pasta vazia.')
    if not filename or filename != PureWindowsPath(filename).name or not filename.lower().endswith(('.accdb', '.mdb')):
        raise ValueError('Informe somente o nome de um arquivo .accdb ou .mdb.')


def _normalize(value: str) -> str:
    text = unicodedata.normalize('NFKD', str(value or ''))
    return ''.join(ch.lower() for ch in text if ch.isalnum() and not unicodedata.combining(ch))


COLUMN_ALIASES = {
    'prontuario': ('prontuario',),
    'nome': ('nome do paciente', 'nome', 'nomepaciente', 'nome paciente'),
    'data_nascimento': ('data nascimento', 'datanascimento', 'data_nascimento'),
    'nome_mae': ('nome da mae', 'nomemae', 'mae', 'nome mae'),
    'cns': ('nºcartsus', 'ncartsus', 'cns', 'n cart sus'),
    'endereco': ('endereco', 'endereço', 'endereo'),
    'cidade': ('municip', 'cidade', 'municipio'),
    'contato': ('telefone', 'contato', 'fone'),
    'sexo': ('sexo', 'genero'),
}


OCORRENCIAS_ALIASES = {
    'dt_atend': ('dt_atend', 'data atend', 'dataatend', 'data_atendimento'),
    'medico': ('nome_medico', 'nomemedico', 'medico'),
    'turno': ('turnomed', 'turno'),
    'quandoreg': ('quandoreg', 'quando reg'),
    'prontuario': ('prontuario',),
    'nome': ('nome do paciente', 'nome', 'nomepaciente', 'nome paciente'),
}
OCORRENCIAS_REQUIRED = ('dt_atend', 'medico', 'prontuario')
_NAME_TITLES = {'dr', 'dra', 'drª', 'doutor', 'doutora', 'prof', 'profa'}
_NAME_PARTICLES = {'da', 'de', 'do', 'das', 'dos', 'e'}


def build_access_config(settings) -> AccessConfig:
    """Monta a configuração Access a partir de SpecialtySettings (ou padrões)."""
    return AccessConfig(
        host=(getattr(settings, 'access_host', None) or '192.168.1.252'),
        share_path=(getattr(settings, 'access_share_path', None) or r'naqh\AMBULATORIO_SERV'),
        filename=(getattr(settings, 'access_filename', None) or 'AMBULATORIO_SERV.accdb'),
        enabled=(settings.access_enabled if settings is not None else True),
        source=(getattr(settings, 'access_source', None) or 'network'),
        local_path=getattr(settings, 'access_local_path', None),
    )


def normalize_person_name(value) -> str:
    """Remove acentos, títulos (Dr./Dra.), pontuação e espaços extras."""
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = [token for token in text.split() if token not in _NAME_TITLES]
    return ' '.join(tokens)


def doctor_name_matches(agenda_name, user_name, threshold: float = 0.85) -> bool:
    """Compara nomes de médico tolerando acentos, partículas e pequenos erros."""
    a, b = normalize_person_name(agenda_name), normalize_person_name(user_name)
    if not a or not b:
        return False
    if a == b:
        return True
    core_a = [t for t in a.split() if t not in _NAME_PARTICLES]
    core_b = [t for t in b.split() if t not in _NAME_PARTICLES]
    if not core_a or not core_b:
        return False
    if ' '.join(core_a) == ' '.join(core_b):
        return True
    if difflib.SequenceMatcher(None, ' '.join(core_a), ' '.join(core_b)).ratio() >= threshold:
        return True
    # Primeiro e último nome equivalentes (ex.: nome do meio omitido em um dos lados)
    if len(core_a) >= 2 and len(core_b) >= 2:
        ratio = lambda x, y: difflib.SequenceMatcher(None, x, y).ratio()  # noqa: E731
        return ratio(core_a[0], core_b[0]) >= 0.8 and ratio(core_a[-1], core_b[-1]) >= 0.8
    return False


def normalize_turno(value) -> str:
    """Retorna 'MANHA', 'TARDE' ou '' a partir do valor de turnomed."""
    text = _normalize(value)
    if text.startswith('m'):
        return 'MANHA'
    if text.startswith('t'):
        return 'TARDE'
    return ''


def _as_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    raw = str(value or '').strip()
    if not raw:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            continue
    return None


class AccessPatientService:
    def __init__(self, success_ttl=300, miss_ttl=60, max_cache=256, clock=time.monotonic):
        self.success_ttl, self.miss_ttl, self.max_cache = success_ttl, miss_ttl, max_cache
        self.clock = clock
        self._lock = threading.RLock()
        self._connection = None
        self._signature = None
        self._columns = None
        self._occ_columns = None
        self._day_cache = None
        self._cache: OrderedDict[str, tuple[float, dict[str, Any] | None]] = OrderedDict()

    def invalidate(self) -> None:
        with self._lock:
            self._close_connection()
            self._signature, self._columns = None, None
            self._occ_columns, self._day_cache = None, None
            self._cache.clear()

    def _close_connection(self):
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass
        self._connection = None

    def _prepare(self, config: AccessConfig):
        validate_access_config(config)
        if not config.enabled:
            raise AccessLookupError('ACCESS_DISABLED', 'A busca no banco do CPAM está desativada.', 'Um administrador pode ativá-la em Configurações.', 503)
        if self._signature != config.signature:
            self.invalidate()
            self._signature = config.signature

    def _connect(self, config: AccessConfig):
        if pyodbc is None:
            raise AccessLookupError('ACCESS_DRIVER_MISSING', 'Integração com Microsoft Access indisponível.', 'Instale pyodbc e o Microsoft Access Database Engine compatível.', 503)
        drivers = {driver.lower() for driver in pyodbc.drivers()}
        if ACCESS_DRIVER.lower() not in drivers:
            raise AccessLookupError('ACCESS_DRIVER_MISSING', 'Microsoft Access Database Engine não está instalado.', 'Instale o driver Access da mesma arquitetura do sistema.', 503)
        source = (config.source or '').strip().lower()
        if source == 'local' and not Path(config.database_path).is_file():
            raise AccessLookupError(
                'ACCESS_FILE_NOT_FOUND',
                'O arquivo Access local configurado não foi encontrado.',
                'Selecione novamente o arquivo nas Configurações.',
                404,
            )
        connection_string = f'DRIVER={{{ACCESS_DRIVER}}};DBQ={config.database_path};READONLY=TRUE;'
        started = self.clock()
        try:
            self._connection = pyodbc.connect(connection_string, timeout=5, autocommit=True)
            logger.info(
                'Conexão Access somente leitura aberta em %.1f ms (origem=%s)',
                (self.clock() - started) * 1000,
                source,
            )
            return self._connection
        except Exception as exc:
            raise self._classify_error(exc, config) from exc

    def _classify_error(self, exc: Exception, config: AccessConfig) -> AccessLookupError:
        detail = str(exc).lower()
        if any(token in detail for token in ('permission', 'denied', 'permissão', 'acesso negado')):
            return AccessLookupError('ACCESS_PERMISSION_DENIED', 'Sem permissão para ler o banco do CPAM.', 'Verifique as permissões do compartilhamento para este usuário.', 403)
        if any(token in detail for token in ('timeout', 'timed out', 'tempo limite')):
            return AccessLookupError('ACCESS_TIMEOUT', 'A consulta ao banco do CPAM excedeu o tempo limite.', 'Verifique a rede e tente novamente.', 504)
        if any(token in detail for token in ('not a valid file name', 'could not find file', 'não foi possível encontrar')):
            return AccessLookupError('ACCESS_FILE_NOT_FOUND', 'O arquivo Access configurado não foi encontrado.', 'Revise o endereço e o nome do arquivo nas Configurações.', 404)
        if any(token in detail for token in ('network path', 'rede não foi encontrado', 'network name')):
            return AccessLookupError('ACCESS_SHARE_UNAVAILABLE', 'O compartilhamento do banco do CPAM não está acessível.', 'Verifique o compartilhamento configurado e as permissões da rede.', 503)
        if (config.source or '').strip().lower() == 'network' and any(token in detail for token in ('server', 'host', 'unreachable', 'não respondeu')):
            return AccessLookupError('ACCESS_HOST_UNREACHABLE', f'O servidor {config.host} não respondeu.', 'Verifique a conexão com a rede do CPAM.', 503)
        return AccessLookupError('ACCESS_QUERY_FAILED', 'Não foi possível consultar o banco do CPAM.', 'Tente novamente ou solicite ao administrador que teste a conexão.', 502)

    @staticmethod
    def _quote(identifier: str) -> str:
        return '[' + identifier.replace(']', ']]') + ']'

    @staticmethod
    def _sqlstates(exc: Exception) -> tuple[str, ...]:
        """Extract ODBC SQLSTATE values without logging the full driver message."""
        states = []
        for item in getattr(exc, 'args', ()):
            text = str(item).strip().upper()
            match = re.fullmatch(r'([0-9A-Z]{5})', text) or re.match(r'^\[([0-9A-Z]{5})\]', text)
            if match and match.group(1) not in states:
                states.append(match.group(1))
        return tuple(states)

    def _log_odbc_failure(self, stage: str, exc: Exception, attempt: int | None = None) -> None:
        logger.warning(
            'Falha Access na etapa=%s tipo=%s sqlstate=%s tentativa=%s',
            stage,
            type(exc).__name__,
            ','.join(self._sqlstates(exc)) or 'indisponível',
            attempt if attempt is not None else '-',
        )

    def _is_missing_table_error(self, exc: Exception) -> bool:
        states = set(self._sqlstates(exc))
        detail = str(exc).lower()
        return bool(states.intersection({'42S02', 'S0002'})) or any(
            token in detail
            for token in ('could not find', 'cannot find', 'não foi possível encontrar', 'tabela inexistente')
        )

    def _discover_columns(self, connection) -> dict[str, str]:
        if self._columns is not None:
            return self._columns
        cursor = None
        try:
            # Alguns drivers Access antigos falham em cursor.columns(), embora
            # executem SELECT normalmente. WHERE 1=0 lê somente os metadados.
            cursor = connection.cursor()
            cursor.execute(f'SELECT * FROM {self._quote(TABLE_NAME)} WHERE 1=0')
            description = cursor.description
        except Exception as exc:
            self._log_odbc_failure('descoberta_esquema', exc)
            if self._is_missing_table_error(exc):
                raise AccessLookupError(
                    'ACCESS_TABLE_NOT_FOUND',
                    'A tabela cadastro_de_pacientes não foi encontrada.',
                    'Selecione o arquivo Access correto nas Configurações.',
                    502,
                ) from exc
            raise
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    logger.warning('Não foi possível fechar o cursor de metadados do Access.')
        if not description:
            raise AccessLookupError(
                'ACCESS_SCHEMA_EMPTY',
                'O driver não retornou a estrutura da tabela de pacientes.',
                'Verifique o arquivo e a compatibilidade do Microsoft Access Database Engine.',
                502,
            )
        names = [str(column[0]) for column in description if column and column[0]]
        if not names:
            raise AccessLookupError(
                'ACCESS_SCHEMA_EMPTY',
                'A tabela de pacientes não possui colunas legíveis.',
                'Verifique a integridade do arquivo Access configurado.',
                502,
            )
        normalized = {_normalize(name): name for name in names}
        mapping = {}
        for canonical, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if _normalize(alias) in normalized:
                    mapping[canonical] = normalized[_normalize(alias)]
                    break
        if 'prontuario' not in mapping:
            raise AccessLookupError(
                'ACCESS_PRONTUARIO_COLUMN_MISSING',
                'A coluna de prontuário não foi encontrada.',
                'Verifique se o arquivo configurado contém a tabela esperada.',
                502,
            )
        self._columns = mapping
        return mapping

    def _cached(self, prontuario: str):
        item = self._cache.get(prontuario)
        if item is None:
            return False, None
        expires, value = item
        if expires <= self.clock():
            del self._cache[prontuario]
            return False, None
        self._cache.move_to_end(prontuario)
        return True, value

    def _store(self, prontuario: str, value):
        ttl = self.success_ttl if value is not None else self.miss_ttl
        self._cache[prontuario] = (self.clock() + ttl, value)
        self._cache.move_to_end(prontuario)
        while len(self._cache) > self.max_cache:
            self._cache.popitem(last=False)

    def search(self, config: AccessConfig, prontuario: str) -> dict[str, Any]:
        started = self.clock()
        with self._lock:
            self._prepare(config)
            hit, value = self._cached(prontuario)
            if hit:
                return {'found': value is not None, 'data': value, 'source': 'memory_cache', 'query_time_ms': round((self.clock() - started) * 1000, 2)}
            for attempt in range(2):
                cursor = None
                try:
                    connection = self._connection or self._connect(config)
                    columns = self._discover_columns(connection)
                    selected = list(columns.items())
                    select_sql = ', '.join(self._quote(real) for _, real in selected)
                    sql = f'SELECT TOP 1 {select_sql} FROM {self._quote(TABLE_NAME)} WHERE {self._quote(columns["prontuario"])} = ?'
                    cursor = connection.cursor()
                    cursor.execute(sql, prontuario)
                    row = cursor.fetchone()
                    value = None if row is None else {canonical: row[index] for index, (canonical, _) in enumerate(selected)}
                    self._store(prontuario, value)
                    logger.info('Consulta Access concluída em %.1f ms (%s)', (self.clock() - started) * 1000, 'encontrado' if value else 'não encontrado')
                    return {'found': value is not None, 'data': value, 'source': 'access', 'query_time_ms': round((self.clock() - started) * 1000, 2)}
                except AccessLookupError:
                    raise
                except Exception as exc:
                    self._log_odbc_failure('consulta_paciente', exc, attempt + 1)
                    self._close_connection()
                    self._columns = None
                    if attempt == 1:
                        raise self._classify_error(exc, config) from exc
                finally:
                    if cursor is not None:
                        try:
                            cursor.close()
                        except Exception:
                            logger.warning('Não foi possível fechar o cursor de consulta do Access.')
        raise AssertionError('unreachable')

    def _discover_ocorrencias_columns(self, connection) -> dict[str, str]:
        if self._occ_columns is not None:
            return self._occ_columns
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(f'SELECT * FROM {self._quote(OCORRENCIAS_TABLE)} WHERE 1=0')
            description = cursor.description
        except Exception as exc:
            self._log_odbc_failure('descoberta_ocorrencias', exc)
            if self._is_missing_table_error(exc):
                raise AccessLookupError(
                    'ACCESS_OCORRENCIAS_NOT_FOUND',
                    'A tabela Ocorrencias não foi encontrada no banco do CPAM.',
                    'Verifique se o arquivo Access configurado contém a agenda de consultas.',
                    502,
                ) from exc
            raise
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
        names = [str(column[0]) for column in (description or []) if column and column[0]]
        normalized = {_normalize(name): name for name in names}
        mapping = {}
        for canonical, aliases in OCORRENCIAS_ALIASES.items():
            for alias in aliases:
                if _normalize(alias) in normalized:
                    mapping[canonical] = normalized[_normalize(alias)]
                    break
        missing = [name for name in OCORRENCIAS_REQUIRED if name not in mapping]
        if missing:
            raise AccessLookupError(
                'ACCESS_OCORRENCIAS_COLUMNS_MISSING',
                'A tabela Ocorrencias não possui as colunas esperadas.',
                'Colunas ausentes: ' + ', '.join(missing) + '.',
                502,
            )
        self._occ_columns = mapping
        return mapping

    def _fetch_names(self, connection, prontuarios: list[str]) -> dict[str, str]:
        """Casa prontuário → nome em cadastro_de_pacientes (consultas em lote)."""
        if not prontuarios:
            return {}
        columns = self._discover_columns(connection)
        if 'nome' not in columns:
            return {}
        names: dict[str, str] = {}
        for start in range(0, len(prontuarios), 100):
            chunk = prontuarios[start:start + 100]
            placeholders = ', '.join('?' for _ in chunk)
            sql = (
                f'SELECT {self._quote(columns["prontuario"])}, {self._quote(columns["nome"])} '
                f'FROM {self._quote(TABLE_NAME)} WHERE {self._quote(columns["prontuario"])} IN ({placeholders})'
            )
            cursor = connection.cursor()
            try:
                cursor.execute(sql, *chunk)
                for row in cursor.fetchall():
                    key = str(row[0] or '').strip()
                    if key and row[1]:
                        names[key] = str(row[1]).strip()
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
        return names

    def daily_appointments(self, config: AccessConfig, day: date, force: bool = False) -> dict[str, Any]:
        """Consultas do dia (todos os médicos), com cache compartilhado de 3 minutos."""
        with self._lock:
            self._prepare(config)
            now = self.clock()
            cached = self._day_cache
            if not force and cached and cached[0] == day and cached[1] > now:
                return {'rows': list(cached[2]), 'synced_at': cached[3], 'source': 'memory_cache'}
            start = datetime(day.year, day.month, day.day)
            end = start + timedelta(days=1)
            for attempt in range(2):
                cursor = None
                try:
                    connection = self._connection or self._connect(config)
                    columns = self._discover_ocorrencias_columns(connection)
                    selected = list(columns.items())
                    select_sql = ', '.join(self._quote(real) for _, real in selected)
                    dt_col = self._quote(columns['dt_atend'])
                    sql = (
                        f'SELECT {select_sql} FROM {self._quote(OCORRENCIAS_TABLE)} '
                        f'WHERE {dt_col} >= ? AND {dt_col} < ?'
                    )
                    cursor = connection.cursor()
                    cursor.execute(sql, start, end)
                    raw_rows = cursor.fetchall()
                    cursor.close()
                    cursor = None
                    rows = []
                    for raw in raw_rows:
                        item = {canonical: raw[index] for index, (canonical, _) in enumerate(selected)}
                        prontuario = str(item.get('prontuario') or '').strip()
                        if prontuario.endswith('.0') and prontuario[:-2].isdigit():
                            prontuario = prontuario[:-2]
                        if not prontuario:
                            continue
                        rows.append({
                            'prontuario': prontuario,
                            'nome': str(item.get('nome') or '').strip(),
                            'medico': str(item.get('medico') or '').strip(),
                            'turno': normalize_turno(item.get('turno')),
                            'quandoreg': _as_datetime(item.get('quandoreg')),
                            'dt_atend': _as_datetime(item.get('dt_atend')),
                        })
                    try:
                        names = self._fetch_names(connection, sorted({row['prontuario'] for row in rows}))
                    except AccessLookupError:
                        names = {}
                    except Exception as exc:  # nomes são complementares; não derruba a lista
                        self._log_odbc_failure('nomes_ocorrencias', exc)
                        names = {}
                    for row in rows:
                        row['nome'] = names.get(row['prontuario']) or row['nome'] or f'Prontuário {row["prontuario"]}'
                    synced_at = datetime.now()
                    self._day_cache = (day, self.clock() + DAY_CACHE_TTL, rows, synced_at)
                    logger.info('Agenda do dia carregada do Access: %d consultas', len(rows))
                    return {'rows': list(rows), 'synced_at': synced_at, 'source': 'access'}
                except AccessLookupError:
                    raise
                except Exception as exc:
                    self._log_odbc_failure('consulta_ocorrencias', exc, attempt + 1)
                    self._close_connection()
                    self._columns, self._occ_columns = None, None
                    if attempt == 1:
                        raise self._classify_error(exc, config) from exc
                finally:
                    if cursor is not None:
                        try:
                            cursor.close()
                        except Exception:
                            pass
        raise AssertionError('unreachable')

    def test_connection(self, config: AccessConfig) -> dict[str, Any]:
        started = self.clock()
        with self._lock:
            self._prepare(config)
            connection = self._connection or self._connect(config)
            try:
                columns = self._discover_columns(connection)
            except AccessLookupError:
                raise
            except Exception as exc:
                self._close_connection()
                self._columns = None
                raise self._classify_error(exc, config) from exc
            return {'ok': True, 'code': 'ACCESS_CONNECTION_OK', 'message': 'Conexão somente leitura realizada com sucesso.', 'hint': f'Tabela {TABLE_NAME} e coluna {columns["prontuario"]} encontradas.', 'query_time_ms': round((self.clock() - started) * 1000, 2)}


access_patient_service = AccessPatientService()
