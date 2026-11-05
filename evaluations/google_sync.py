"""Optional read-only Google Sheets adapter, using a server-side credential file."""
from django.conf import settings
from .importers import RAW_TABS, inspect_and_import
from .services import digest

def sync_google(session, actor):
    from google.auth import default
    from google.auth.transport.requests import AuthorizedSession
    if not settings.GOOGLE_WORKBOOK_ID: raise ValueError('Google workbook ID is not configured.')
    if not settings.GOOGLE_WORKBOOK_ID.replace('-', '').replace('_', '').isalnum(): raise ValueError('Invalid workbook ID.')
    credentials, _ = default(scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    client = AuthorizedSession(credentials)
    try:
        ranges = [f"'{name}'!A1:Z10000" for name in RAW_TABS.values()]
        response = client.get(f'https://sheets.googleapis.com/v4/spreadsheets/{settings.GOOGLE_WORKBOOK_ID}/values:batchGet',
                              params={'ranges': ranges, 'valueRenderOption': 'UNFORMATTED_VALUE'}, timeout=30)
        response.raise_for_status()
        result = response.json().get('valueRanges', [])
        if len(result) != len(ranges): raise ValueError('Google returned an incomplete response set.')
        tabs = {name: item.get('values', []) for name, item in zip(RAW_TABS.values(), result)}
        if any(len(v) >= 10000 for v in tabs.values()): raise ValueError('Source reached the 10,000 row boundary; narrow the academic session.')
        return inspect_and_import(tabs, session, actor, digest(tabs))
    finally: client.close()
