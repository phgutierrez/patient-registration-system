"""Public, non-secret integration defaults bundled with every distribution."""
from urllib.parse import quote

DEFAULT_CALENDAR_ID = 's4obpr7j3q70p7b4q5o8vsla9k@group.calendar.google.com'
DEFAULT_CALENDAR_TZ = 'America/Fortaleza'
DEFAULT_FORMS_EDIT_ID = '1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw'
DEFAULT_FORMS_PUBLIC_ID = '1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg'


def calendar_ics_url(calendar_id: str = DEFAULT_CALENDAR_ID) -> str:
    normalized = (calendar_id or '').strip()
    if not normalized:
        return ''
    return f'https://calendar.google.com/calendar/ical/{quote(normalized, safe="")}/public/basic.ics'


def forms_view_url(public_id: str = DEFAULT_FORMS_PUBLIC_ID) -> str:
    normalized = (public_id or '').strip()
    return f'https://docs.google.com/forms/d/e/{normalized}/viewform' if normalized else ''


DEFAULT_CALENDAR_ICS_URL = calendar_ics_url()
DEFAULT_FORMS_VIEW_URL = forms_view_url()

PUBLIC_ENV_DEFAULTS = {
    'GOOGLE_CALENDAR_ID': DEFAULT_CALENDAR_ID,
    'GOOGLE_CALENDAR_TZ': DEFAULT_CALENDAR_TZ,
    'GOOGLE_CALENDAR_ICS_URL': DEFAULT_CALENDAR_ICS_URL,
    'ORTOPEDIA_AGENDA_URL': DEFAULT_CALENDAR_ICS_URL,
    'GOOGLE_FORMS_EDIT_ID': DEFAULT_FORMS_EDIT_ID,
    'GOOGLE_FORMS_PUBLIC_ID': DEFAULT_FORMS_PUBLIC_ID,
    'GOOGLE_FORMS_VIEWFORM_URL': DEFAULT_FORMS_VIEW_URL,
}
