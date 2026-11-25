"""Cópia local do arquivo Access (modo rede) para leituras longas.

Consultar um .accdb grande direto na pasta compartilhada é lento (o driver lê
páginas pela rede). Copiar o arquivo em sequência para o disco local e consultar a
cópia costuma ser bem mais rápido. A cópia:

- só ocorre na origem ``network`` e **nunca escreve** no arquivo original;
- só é refeita se o arquivo mudou **e** a última cópia tem mais de ``min_interval``
  segundos (ou se o usuário pediu atualização);
- usa arquivo ``.part`` + ``os.replace`` (nunca deixa uma cópia pela metade);
- respeita limite de tamanho e espaço livre em disco;
- em qualquer falha devolve ``None`` + aviso, e quem chama lê pela rede.
"""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import time
from pathlib import Path

from src.services.access_patient_service import AccessConfig

logger = logging.getLogger(__name__)

CHUNK_BYTES = 1024 * 1024
DEFAULT_MAX_MB = 500
DEFAULT_MIN_INTERVAL = 10 * 60


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {'0', 'false', 'no', 'nao', 'não', 'off', ''}


def _env_number(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class LocalCopyManager:
    def __init__(self, cache_dir, enabled: bool | None = None, max_mb: float | None = None,
                 min_interval: float | None = None, clock=time.time, disk_usage=shutil.disk_usage):
        self.cache_dir = Path(cache_dir)
        self.enabled = _env_bool('SURGERY_LOCAL_COPY', True) if enabled is None else enabled
        self.max_bytes = int((_env_number('SURGERY_LOCAL_COPY_MAX_MB', DEFAULT_MAX_MB) if max_mb is None else max_mb) * 1024 * 1024)
        self.min_interval = (_env_number('SURGERY_LOCAL_COPY_MIN_MINUTES', DEFAULT_MIN_INTERVAL / 60) * 60
                             if min_interval is None else min_interval)
        self.clock, self._disk_usage = clock, disk_usage
        self._state: dict[str, dict] = {}  # destino -> {'signature': (tamanho, mtime), 'copied_at': float}

    def _destination(self, source: str) -> Path:
        digest = hashlib.sha1(source.lower().encode('utf-8')).hexdigest()[:12]
        return self.cache_dir / f'cirurgias_{digest}.accdb'

    def prepare(self, config: AccessConfig, force: bool = False) -> tuple[AccessConfig | None, str | None, dict]:
        """Devolve ``(config_local | None, aviso | None, info)``.

        ``info`` traz ``copied`` (bool), ``seconds`` e ``megabytes`` para o log.
        """
        info = {'copied': False, 'seconds': 0.0, 'megabytes': 0.0}
        if not self.enabled or (config.source or '').strip().lower() != 'network':
            return None, None, info
        try:
            source = config.database_path
            stat = os.stat(source)
        except Exception:
            return None, 'Cópia local indisponível: não foi possível ler o arquivo na rede. Lendo direto pela rede.', info
        info['megabytes'] = round(stat.st_size / 1048576, 1)
        if stat.st_size > self.max_bytes:
            return None, (f'Banco com {info["megabytes"]:.0f} MB, acima do limite de cópia local '
                          f'({self.max_bytes // 1048576} MB). Lendo direto pela rede.'), info

        destination = self._destination(source)
        signature = (stat.st_size, int(stat.st_mtime))
        known = self._state.get(str(destination))
        exists = destination.is_file()
        if exists and known:
            unchanged = known['signature'] == signature
            recent = (self.clock() - known['copied_at']) < self.min_interval
            if unchanged or (recent and not force):
                return self._local_config(destination), None, info
        try:
            info['seconds'] = self._copy(source, destination, stat.st_size)
        except Exception as exc:
            logger.warning('Falha ao copiar o banco Access para o disco local (%s).', type(exc).__name__)
            if exists:  # mantém a cópia anterior, mesmo velha, em vez de voltar à rede lenta
                return self._local_config(destination), 'Cópia local desatualizada: não foi possível renová-la agora.', info
            return None, 'Cópia local indisponível (falha ao copiar). Lendo direto pela rede.', info
        info['copied'] = True
        self._state[str(destination)] = {'signature': signature, 'copied_at': self.clock()}
        self._cleanup(keep=destination)
        return self._local_config(destination), None, info

    def _copy(self, source: str, destination: Path, size: int) -> float:
        """Copia em blocos para ``.part`` e troca atomicamente. Devolve os segundos gastos."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        free = self._disk_usage(self.cache_dir).free
        if free < size * 2:
            raise OSError('Espaço em disco insuficiente para a cópia local.')
        part = destination.with_suffix('.accdb.part')
        started = self.clock()
        try:
            with open(source, 'rb') as reader, open(part, 'wb') as writer:
                while True:
                    block = reader.read(CHUNK_BYTES)
                    if not block:
                        break
                    writer.write(block)
            if size and part.stat().st_size == 0:
                raise OSError('Cópia vazia.')
            os.replace(part, destination)
            return round(self.clock() - started, 1)
        finally:
            try:
                if part.exists():
                    part.unlink()
            except OSError:
                pass

    def _cleanup(self, keep: Path) -> None:
        try:
            for item in self.cache_dir.glob('cirurgias_*'):
                if item != keep:
                    item.unlink()
        except OSError:
            logger.debug('Não foi possível limpar cópias antigas do Access.')

    @staticmethod
    def _local_config(destination: Path) -> AccessConfig:
        return AccessConfig(host='', share_path='', filename=destination.name, enabled=True,
                            source='local', local_path=str(destination))
