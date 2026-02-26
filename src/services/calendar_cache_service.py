"""
Thread-safe calendar cache service with 60-second TTL and conditional GET support.
"""
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, NamedTuple
import requests
from flask import current_app

from src.extensions import db
from src.models.calendar_cache import CalendarCache
from src.services.calendar_service import CalendarService


logger = logging.getLogger(__name__)

class CalendarData(NamedTuple):
    """Container for calendar data and metadata"""
    events: List[Dict[str, Any]]
    events_by_date: Dict[str, List[Dict[str, Any]]]
    fetched_at: datetime
    source_status: str  # 'ok', 'stale', 'error'
    last_error: Optional[str]


class CalendarCacheService:
    """
    Thread-safe calendar cache service with conditional GET support.
    
    Features:
    - TTL-based caching (default 60 seconds)
    - Conditional GET (ETag/If-Modified-Since)
    - Thread-safe operations
    - Graceful error handling (serves stale cache on failure)
    - Database persistence for multi-process scenarios
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._memory_cache: Optional[CalendarData] = None
        self._response_headers: Optional[Dict[str, str]] = None
        
    def get_calendar_data(self, force_refresh: bool = False) -> CalendarData:
        """
        Get cached calendar data with automatic refresh based on TTL.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            CalendarData with events and metadata
        """
        with self._lock:
            ttl_seconds = current_app.config.get('CALENDAR_CACHE_TTL_SECONDS', 60)
            
            # Check if we need to refresh
            needs_refresh = force_refresh
            age_seconds = 0
            if not needs_refresh and self._memory_cache:
                age_seconds = (datetime.utcnow() - self._memory_cache.fetched_at).total_seconds()
                needs_refresh = age_seconds >= ttl_seconds
            elif not self._memory_cache:
                needs_refresh = True
            
            if not needs_refresh and self._memory_cache:
                logger.debug(f"Calendar cache HIT (age: {age_seconds:.1f}s)")
                return self._memory_cache
            
            # Need to refresh - try to get fresh data
            logger.info("Calendar cache MISS - refreshing...")
            fresh_data = self._fetch_fresh_data()
            
            if fresh_data:
                # Success - update memory cache and persist to DB
                self._memory_cache = fresh_data
                self._persist_to_db(fresh_data)
                logger.info(f"Calendar refreshed: {len(fresh_data.events)} events")
                return fresh_data
            
            # Refresh failed - try to serve stale cache
            if self._memory_cache:
                logger.warning("Calendar refresh failed - serving stale cache")
                return self._memory_cache._replace(source_status='stale')
            
            # No memory cache - try to load from DB
            db_data = self._load_from_db()
            if db_data:
                logger.warning("Calendar refresh failed - serving stale DB cache")
                self._memory_cache = db_data._replace(source_status='stale')
                return self._memory_cache
            
            # No cache available - return empty data
            logger.error("No calendar cache available - returning empty data")
            return CalendarData(
                events=[],
                events_by_date={},
                fetched_at=datetime.utcnow(),
                source_status='error',
                last_error='No cache available and refresh failed'
            )
    
    def _fetch_fresh_data(self) -> Optional[CalendarData]:
        """Fetch fresh data from Google Calendar ICS feed"""
        try:
            # Get calendar service
            from src.services.calendar_service import get_calendar_service
            calendar_service = get_calendar_service()
            
            # Load existing cache metadata for conditional GET
            cache_entry = CalendarCache.query.filter_by(
                calendar_id=calendar_service.calendar_id
            ).first()
            
            # Build conditional headers
            headers = {}
            if cache_entry and cache_entry.etag:
                headers['If-None-Match'] = cache_entry.etag
            if cache_entry and cache_entry.last_modified:
                headers['If-Modified-Since'] = cache_entry.last_modified
            
            # Enhanced fetch with conditional GET
            events, error, response_headers = self._fetch_with_conditional_get(
                calendar_service, headers
            )
            
            if error:
                logger.error(f"Calendar fetch failed: {error}")
                return None
            
            # Group events by date
            events_by_date = calendar_service.group_events_by_day(events)
            
            # Store response headers for conditional GET
            self._response_headers = response_headers or {}
            
            return CalendarData(
                events=events,
                events_by_date=events_by_date,
                fetched_at=datetime.utcnow(),
                source_status='ok',
                last_error=None
            )
            
        except Exception as e:
            logger.exception(f"Unexpected error fetching calendar: {e}")
            return None
    
    def _fetch_with_conditional_get(self, 
                                   calendar_service: CalendarService, 
                                   headers: Dict[str, str]) -> tuple[List[Dict], Optional[str], Optional[Dict]]:
        """Fetch ICS with conditional GET support"""
        try:
            response = requests.get(
                calendar_service.ics_url,
                headers=headers,
                timeout=calendar_service.request_timeout
            )
            
            # Handle 304 Not Modified
            if response.status_code == 304:
                logger.info("Calendar not modified (304) - keeping cached data")
                # Update fetched_at for existing cache but keep existing events
                if self._memory_cache:
                    # Just update the timestamp to reset TTL
                    updated_cache = self._memory_cache._replace(fetched_at=datetime.utcnow())
                    return updated_cache.events, None, dict(response.headers)
                else:
                    # Load from DB
                    db_data = self._load_from_db()
                    if db_data:
                        return db_data.events, None, dict(response.headers)
                    return [], "No cached data for 304 response", None
            
            # Handle other non-200 responses
            if response.status_code != 200:
                error = f"HTTP {response.status_code}: {response.reason}"
                return [], error, None
            
            # Parse ICS content
            events = calendar_service._parse_ics(response.text)
            
            return events, None, dict(response.headers)
            
        except requests.exceptions.Timeout:
            return [], "Request timeout", None
        except requests.exceptions.ConnectionError:
            return [], "Connection error", None
        except Exception as e:
            return [], str(e), None
    
    def _persist_to_db(self, data: CalendarData):
        """Persist calendar data to database"""
        try:
            from src.services.calendar_service import get_calendar_service
            calendar_service = get_calendar_service()
            
            # Get or create cache entry
            cache_entry = CalendarCache.query.filter_by(
                calendar_id=calendar_service.calendar_id
            ).first()
            
            if not cache_entry:
                cache_entry = CalendarCache(calendar_id=calendar_service.calendar_id)
                db.session.add(cache_entry)
            
            # Serialize events
            events_json = json.dumps([
                {
                    'uid': e['uid'],
                    'title': e['title'],
                    'start': e['start'].isoformat(),
                    'end': e['end'].isoformat(),
                    'start_date': e.get('start_date').isoformat() if e.get('start_date') else None,
                    'end_date': e.get('end_date').isoformat() if e.get('end_date') else None,
                    'all_day': e['all_day'],
                    'location': e['location'],
                    'description': e['description'],
                }
                for e in data.events
            ])
            
            # Update cache entry
            cache_entry.fetched_at = data.fetched_at
            cache_entry.events_json = events_json
            cache_entry.error_message = data.last_error
            
            # Store ETag and Last-Modified for conditional GET
            if self._response_headers:
                cache_entry.etag = self._response_headers.get('ETag')
                cache_entry.last_modified = self._response_headers.get('Last-Modified')
            
            db.session.commit()
            logger.debug("Calendar cache persisted to database")
            
        except Exception as e:
            logger.exception(f"Failed to persist calendar cache: {e}")
            db.session.rollback()
    
    def _load_from_db(self) -> Optional[CalendarData]:
        """Load calendar data from database"""
        try:
            from src.services.calendar_service import get_calendar_service
            calendar_service = get_calendar_service()
            
            cache_entry = CalendarCache.query.filter_by(
                calendar_id=calendar_service.calendar_id
            ).first()
            
            if not cache_entry or not cache_entry.events_json:
                return None
            
            # Deserialize events
            events_data = json.loads(cache_entry.events_json)
            events = []
            
            for evt in events_data:
                evt['start'] = datetime.fromisoformat(evt['start'])
                evt['end'] = datetime.fromisoformat(evt['end'])
                
                # Convert all-day dates if present
                if evt.get('start_date'):
                    evt['start_date'] = datetime.fromisoformat(evt['start_date']).date()
                if evt.get('end_date'):
                    evt['end_date'] = datetime.fromisoformat(evt['end_date']).date()
                
                events.append(evt)
            
            # Group by date
            events_by_date = calendar_service.group_events_by_day(events)
            
            return CalendarData(
                events=events,
                events_by_date=events_by_date,
                fetched_at=cache_entry.fetched_at or datetime.utcnow(),
                source_status='ok',
                last_error=cache_entry.error_message
            )
            
        except Exception as e:
            logger.exception(f"Failed to load calendar cache from DB: {e}")
            return None


# Global instance
_calendar_cache_service = CalendarCacheService()

def get_calendar_cache_service() -> CalendarCacheService:
    """Get the global calendar cache service instance"""
    return _calendar_cache_service