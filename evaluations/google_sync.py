"""Optional read-only Google Sheets adapter, using a server-side credential file."""
from django.conf import settings
from .master_sync import READ_TABS, import_master
from .services import digest

def sync_google(session, actor):
    import json, subprocess, sys
    from pathlib import Path
    if settings.OBE_N8N_BRIDGE:
        if not settings.OBE_MASTER_SNAPSHOT:
            raise ValueError('The local Google bridge snapshot is not configured.')
        try:
            subprocess.run([sys.executable, settings.OBE_N8N_BRIDGE], check=True,
                           capture_output=True, timeout=120)
            payload = json.loads(Path(settings.OBE_MASTER_SNAPSHOT).read_text(encoding='utf-8'))
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise ValueError('Live Google read failed. Check n8n and its Google authorization.') from error
        result = payload.get('valueRanges', [])
        if payload.get('spreadsheetId') != settings.GOOGLE_WORKBOOK_ID:
            raise ValueError('The reader returned a different workbook.')
        tabs = validated_tabs(result)
        return import_master(tabs, session, actor, digest(tabs))
    from google.auth import default
    from google.auth.transport.requests import AuthorizedSession
    if not settings.GOOGLE_WORKBOOK_ID: raise ValueError('Google workbook ID is not configured.')
    if not settings.GOOGLE_WORKBOOK_ID.replace('-', '').replace('_', '').isalnum(): raise ValueError('Invalid workbook ID.')
    credentials, _ = default(scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    client = AuthorizedSession(credentials)
    try:
        ranges = [f"'{name}'!A1:Z10000" for name in READ_TABS]
        response = client.get(f'https://sheets.googleapis.com/v4/spreadsheets/{settings.GOOGLE_WORKBOOK_ID}/values:batchGet',
                              params={'ranges': ranges, 'valueRenderOption': 'UNFORMATTED_VALUE'}, timeout=30)
        response.raise_for_status()
        result = response.json().get('valueRanges', [])
        tabs = validated_tabs(result)
        return import_master(tabs, session, actor, digest(tabs))
    finally: client.close()


def validated_tabs(result):
    if len(result) != len(READ_TABS):
        raise ValueError('Google returned an incomplete response set.')
    tabs = {}
    for name, item in zip(READ_TABS, result):
        actual = item.get('range', '').rsplit('!', 1)[0].strip("'").replace("''", "'")
        if actual != name:
            raise ValueError('Google returned an unexpected worksheet order.')
        values = item.get('values', [])
        if values:
            headers = values[0]
            identity = next((i for i, h in enumerate(headers) if str(h).strip() in ('Seat Number', 'Seat Number / Roll Number')), None)
            if identity is None:
                raise ValueError('Source worksheet has no student identity column.')
            def occupied(row):
                return len(row) > identity and row[identity] is not None and bool(str(row[identity]).strip())
            if len(values) >= 10000 and occupied(values[-1]):
                raise ValueError('Source reached the 10,000 row boundary; narrow the academic session.')
            # Existing sheets extend formulas into rows with no student identity.
            values = list(values)
            while len(values) > 1 and not occupied(values[-1]):
                values.pop()
        tabs[name] = values
    return tabs
