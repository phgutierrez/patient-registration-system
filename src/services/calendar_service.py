from datetime import date
from urllib.parse import quote

import requests
from icalendar import Calendar

from src.core.config import get_settings


class CalendarFacade:
    def __init__(self):
        self.settings = get_settings()

    def _ics_url(self) -> str:
        if self.settings.google_calendar_ics_url:
            return self.settings.google_calendar_ics_url
        cid = quote(self.settings.google_calendar_id, safe='')
        return f'https://calendar.google.com/calendar/ical/{cid}/public/basic.ics'

    async def list_events(self, start: date | None = None, end: date | None = None) -> list[dict]:
        if not self.settings.google_calendar_id and not self.settings.google_calendar_ics_url:
            return []
        response = requests.get(self._ics_url(), timeout=10)
        response.raise_for_status()
        calendar = Calendar.from_ical(response.text)
        events = []
        for component in calendar.walk('VEVENT'):
            dtstart = component.get('DTSTART')
            if not dtstart:
                continue
            start_dt = dtstart.dt
            if hasattr(start_dt, 'date'):
                event_date = start_dt.date()
            else:
                event_date = start_dt
            if start and event_date < start:
                continue
            if end and event_date > end:
                continue
            events.append({
                'uid': str(component.get('UID', '')),
                'title': str(component.get('SUMMARY', 'Sem título')),
                'date': event_date.isoformat(),
            })
        return events
