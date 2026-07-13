from __future__ import annotations

import logging
import re
import threading
import time
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import PureWindowsPath
from typing import Any

try:
    import pyodbc
except ImportError:  # pragma: no cover - depends on deployment architecture
    pyodbc = None

logger = logging.getLogger(__name__)
ACCESS_DRIVER = 'Microsoft Access Driver (*.mdb, *.accdb)'
TABLE_NAME = 'cadastro_de_pacientes'


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

    @property
    def signature(self) -> tuple[str, str, str, bool]:
        return (self.host.lower(), self.share_path.lower(), self.filename.lower(), self.enabled)

    @property
    def unc_path(self) -> str:
        validate_access_config(self)
        return str(PureWindowsPath(f'//{self.host}/{self.share_path}/{self.filename}'))


def validate_access_config(config: AccessConfig) -> None:
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


class AccessPatientService:
    def __init__(self, success_ttl=300, miss_ttl=60, max_cache=256, clock=time.monotonic):
        self.success_ttl, self.miss_ttl, self.max_cache = success_ttl, miss_ttl, max_cache
        self.clock = clock
        self._lock = threading.RLock()
        self._connection = None
        self._signature = None
        self._columns = None
        self._cache: OrderedDict[str, tuple[float, dict[str, Any] | None]] = OrderedDict()

    def invalidate(self) -> None:
        with self._lock:
            self._close_connection()
            self._signature, self._columns = None, None
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
        connection_string = f'DRIVER={{{ACCESS_DRIVER}}};DBQ={config.unc_path};READONLY=TRUE;'
        started = self.clock()
        try:
            self._connection = pyodbc.connect(connection_string, timeout=5, autocommit=True)
            logger.info('Conexão Access somente leitura aberta em %.1f ms', (self.clock() - started) * 1000)
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
        if any(token in detail for token in ('server', 'host', 'unreachable', 'não respondeu')):
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
