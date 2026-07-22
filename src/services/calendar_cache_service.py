"""Per-specialty, thread-safe Google Calendar cache.

Warm requests never wait for the network. Expired data is returned immediately
while a single background worker refreshes the ICS feed.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, NamedTuple, Optional

import requests
from flask import current_app

from src.extensions import db
from src.models.calendar_cache import CalendarCache
from src.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)


class CalendarData(NamedTuple):
    events: List[Dict[str, Any]]
    events_by_date: Dict[str, List[Dict[str, Any]]]
    fetched_at: datetime
    source_status: str  # ok, stale or error
    last_error: Optional[str]


class CalendarCacheService:
    def __init__(
        self,
        calendar_id: str,
        ics_url: str,
        timezone_str: str = 'America/Fortaleza',
    ):
        self.base_calendar_id = calendar_id
        self.ics_url = ics_url
        self.timezone_str = timezone_str
        url_hash = hashlib.sha256(ics_url.encode('utf-8')).hexdigest()[:16]
        self.calendar_id = f'{calendar_id}:{url_hash}'
        self.calendar_service = CalendarService(
            calendar_id=calendar_id,
            ics_url=ics_url,
            timezone_str=timezone_str,
        )
        self._lock = threading.RLock()
        self._memory_cache: Optional[CalendarData] = None
        self._refresh_in_progress = False

    def get_calendar_data(self, force_refresh: bool = False) -> CalendarData:
        ttl_seconds = max(
            15,
            int(current_app.config.get('CALENDAR_CACHE_TTL_SECONDS', 300)),
        )
        with self._lock:
            cached = self._memory_cache
            if cached is None:
                cached = self._load_from_db()
                self._memory_cache = cached

            if force_refresh:
                refreshed = self._refresh()
                if refreshed is not None:
                    return refreshed
                if cached is not None:
                    return cached._replace(source_status='stale')
                return self._empty_error('Não foi possível atualizar a agenda.')

            if cached is not None:
                age = (datetime.utcnow() - cached.fetched_at).total_seconds()
                if age < ttl_seconds:
                    return cached
                self._start_background_refresh()
                return cached._replace(source_status='stale')

            refreshed = self._refresh()
            return refreshed or self._empty_error(
                'Agenda indisponível e ainda não existe cache local.'
            )

    def _start_background_refresh(self) -> None:
        if self._refresh_in_progress:
            return
        self._refresh_in_progress = True
        app = current_app._get_current_object()
        worker = threading.Thread(
            target=self._background_refresh,
            args=(app,),
            name=f'calendar-refresh-{self.base_calendar_id}',
            daemon=True,
        )
        worker.start()

    def _background_refresh(self, app) -> None:
        try:
            with app.app_context():
                with self._lock:
                    self._refresh()
        except Exception:
            logger.exception(
                'Falha inesperada na atualização assíncrona da agenda %s',
                self.base_calendar_id,
            )
        finally:
            with self._lock:
                self._refresh_in_progress = False

    def _refresh(self) -> Optional[CalendarData]:
        cache_entry = CalendarCache.query.filter_by(
            calendar_id=self.calendar_id
        ).first()
        headers: Dict[str, str] = {}
        if cache_entry and cache_entry.etag:
            headers['If-None-Match'] = cache_entry.etag
        if cache_entry and cache_entry.last_modified:
            headers['If-Modified-Since'] = cache_entry.last_modified

        try:
            response = requests.get(
                self.ics_url,
                headers=headers,
                timeout=self.calendar_service.request_timeout,
            )
            if response.status_code == 304:
                cached = self._memory_cache or self._load_from_db()
                if cached is None:
                    logger.warning(
                        'Agenda %s retornou 304 sem cache correspondente.',
                        self.base_calendar_id,
                    )
                    return None
                data = cached._replace(
                    fetched_at=datetime.utcnow(),
                    source_status='ok',
                    last_error=None,
                )
            else:
                response.raise_for_status()
                events = self.calendar_service._parse_ics(response.text)
                data = CalendarData(
                    events=events,
                    events_by_date=self.calendar_service.group_events_by_day(events),
                    fetched_at=datetime.utcnow(),
                    source_status='ok',
                    last_error=None,
                )
            self._memory_cache = data
            self._persist_to_db(data, dict(response.headers))
            logger.info(
                'Agenda %s atualizada: %s evento(s).',
                self.base_calendar_id,
                len(data.events),
            )
            return data
        except requests.Timeout:
            logger.warning('Timeout ao atualizar agenda %s.', self.base_calendar_id)
        except requests.ConnectionError:
            logger.warning('Falha de conexão ao atualizar agenda %s.', self.base_calendar_id)
        except requests.HTTPError as exc:
            logger.warning(
                'HTTP %s ao atualizar agenda %s.',
                getattr(exc.response, 'status_code', '?'),
                self.base_calendar_id,
            )
        except Exception:
            logger.exception('Erro ao atualizar agenda %s.', self.base_calendar_id)
        return None

    def _persist_to_db(
        self,
        data: CalendarData,
        response_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        try:
            entry = CalendarCache.query.filter_by(
                calendar_id=self.calendar_id
            ).first()
            if entry is None:
                entry = CalendarCache(calendar_id=self.calendar_id)
                db.session.add(entry)
            entry.fetched_at = data.fetched_at
            entry.events_json = json.dumps(
                [self._serialize_event(event) for event in data.events],
                ensure_ascii=False,
            )
            entry.error_message = data.last_error
            response_headers = response_headers or {}
            if response_headers.get('ETag'):
                entry.etag = response_headers['ETag']
            if response_headers.get('Last-Modified'):
                entry.last_modified = response_headers['Last-Modified']
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception(
                'Não foi possível persistir o cache da agenda %s.',
                self.base_calendar_id,
            )

    def _load_from_db(self) -> Optional[CalendarData]:
        try:
            entry = CalendarCache.query.filter_by(
                calendar_id=self.calendar_id
            ).first()
            if entry is None or not entry.events_json:
                return None
            events = [
                self._deserialize_event(event)
                for event in json.loads(entry.events_json)
            ]
            return CalendarData(
                events=events,
                events_by_date=self.calendar_service.group_events_by_day(events),
                fetched_at=entry.fetched_at or datetime.utcnow(),
                source_status='ok',
                last_error=entry.error_message,
            )
        except Exception:
            logger.exception(
                'Não foi possível ler o cache da agenda %s.',
                self.base_calendar_id,
            )
            return None

    @staticmethod
    def _serialize_event(event: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'uid': event.get('uid', ''),
            'title': event.get('title', ''),
            'start': event['start'].isoformat(),
            'end': event['end'].isoformat(),
            'start_date': (
                event.get('start_date').isoformat()
                if event.get('start_date')
                else None
            ),
            'end_date': (
                event.get('end_date').isoformat()
                if event.get('end_date')
                else None
            ),
            'all_day': bool(event.get('all_day')),
            'location': event.get('location'),
            'description': event.get('description'),
        }

    @staticmethod
    def _deserialize_event(event: Dict[str, Any]) -> Dict[str, Any]:
        event['start'] = datetime.fromisoformat(event['start'])
        event['end'] = datetime.fromisoformat(event['end'])
        if event.get('start_date'):
            event['start_date'] = datetime.fromisoformat(
                event['start_date']
            ).date()
        if event.get('end_date'):
            event['end_date'] = datetime.fromisoformat(
                event['end_date']
            ).date()
        return event

    @staticmethod
    def _empty_error(message: str) -> CalendarData:
        return CalendarData([], {}, datetime.utcnow(), 'error', message)


_registry_lock = threading.RLock()
_services: Dict[str, CalendarCacheService] = {}


def get_calendar_cache_service(
    calendar_id: Optional[str] = None,
    ics_url: Optional[str] = None,
    timezone_str: str = 'America/Fortaleza',
) -> CalendarCacheService:
    """Return an isolated cache service for a calendar configuration."""
    if not calendar_id or not ics_url:
        from src.services.calendar_service import get_calendar_service
        legacy = get_calendar_service()
        calendar_id = calendar_id or legacy.calendar_id
        ics_url = ics_url or legacy.ics_url
        timezone_str = timezone_str or legacy.timezone_str
    registry_key = f'{calendar_id}|{ics_url}|{timezone_str}'
    with _registry_lock:
        service = _services.get(registry_key)
        if service is None:
            service = CalendarCacheService(calendar_id, ics_url, timezone_str)
            _services[registry_key] = service
        return service


def invalidate_calendar_cache(calendar_id: Optional[str] = None) -> None:
    """Drop in-process instances; persisted rows remain safe historical cache."""
    with _registry_lock:
        if calendar_id is None:
            _services.clear()
            return
        prefix = f'{calendar_id}|'
        for key in [key for key in _services if key.startswith(prefix)]:
            _services.pop(key, None)
