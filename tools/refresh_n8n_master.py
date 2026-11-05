"""Local read-only bridge: keep Google credentials inside n8n, never print marks."""
import json
import os
from pathlib import Path
import subprocess
import sys


def extract_result(output):
    decoder = json.JSONDecoder()
    for index, character in enumerate(output):
        if character != '{' or (index and output[index - 1] not in '\r\n'):
            continue
        try:
            result, _ = decoder.raw_decode(output[index:])
        except ValueError:
            continue
        if not isinstance(result, dict):
            continue
        data = result.get('data', {}).get('resultData', {})
        if data.get('error'):
            raise ValueError('n8n Google read failed; reconnect the Google account in n8n if needed.')
        runs = data.get('runData', {}).get('Read Master', [])
        if runs:
            payload = runs[-1].get('data', {}).get('main', [[]])[0][0].get('json', {})
            if isinstance(payload.get('valueRanges'), list):
                return payload
    raise ValueError('The reader returned no verified Google response.')


def refresh():
    cli = Path(os.environ.get('OBE_N8N_CLI', str(Path(os.environ.get('APPDATA', '')) / 'npm/node_modules/n8n/bin/n8n')))
    destination = Path(os.environ['OBE_MASTER_SNAPSHOT'])
    environment = dict(os.environ, N8N_RUNNERS_BROKER_PORT='5689')
    response = subprocess.run(['node', str(cli), 'execute', '--id=OBEReadOnlyLocal01', '--rawOutput'],
                              capture_output=True, timeout=110, env=environment, encoding='utf-8', errors='replace')
    if response.returncode:
        raise ValueError('n8n reader did not complete successfully.')
    payload = extract_result(response.stdout)
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload), encoding='utf-8')
    temporary.replace(destination)


if __name__ == '__main__':
    try:
        refresh()
    except (ValueError, OSError, KeyError, IndexError, subprocess.SubprocessError):
        print('Google read failed. Check n8n availability and Google authorization.', file=sys.stderr)
        sys.exit(1)
    print('Google master read completed.')
