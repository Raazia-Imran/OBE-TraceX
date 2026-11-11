import os,sys,time,subprocess,urllib.request,webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def online(url):
    try:
        with urllib.request.urlopen(url,timeout=2) as response:return response.status==200
    except Exception:return False
def start(args):
    options={'cwd':ROOT,'env':dict(os.environ)}
    if os.name=='nt':options['creationflags']=subprocess.CREATE_NEW_CONSOLE
    return subprocess.Popen(args,**options)
def main():
    if online('http://127.0.0.1:8000/healthz/'):
        print('OBE-TraceX is already running.')
        if '--no-browser' not in sys.argv:webbrowser.open('http://127.0.0.1:8000/')
        return
    if not os.environ.get('OBE_DB_PATH'):
        real=ROOT/'private-data/real.sqlite3'
        if real.exists():os.environ['OBE_DB_PATH']=str(real)
    if not online('http://127.0.0.1:5678/healthz'):
        cli=Path(os.environ.get('OBE_N8N_CLI',str(Path(os.environ.get('APPDATA',''))/'npm/node_modules/n8n/bin/n8n')))
        if cli.exists():start(['node',str(cli),'start'])
        else:print('n8n was not found. The portal can still show saved records; live automation needs n8n.')
    python=str(ROOT/'.venv/Scripts/python.exe') if os.name=='nt' else sys.executable
    check=subprocess.run([python,'manage.py','migrate','--check'],cwd=ROOT)
    if check.returncode:
        print('Database migrations are required. Run manage.py migrate before starting.');sys.exit(1)
    start([python,'manage.py','runserver','127.0.0.1:8000','--noreload'])
    session=os.environ.get('OBE_LIVE_SESSION_ID','');coordinator=os.environ.get('OBE_SYNC_COORDINATOR','')
    if session.isdigit() and coordinator:start([python,'manage.py','watch_master','--session',session,'--coordinator',coordinator,'--interval','60'])
    for _ in range(30):
        if online('http://127.0.0.1:8000/healthz/'):
            print('OBE-TraceX is ready at http://127.0.0.1:8000/')
            if '--no-browser' not in sys.argv:webbrowser.open('http://127.0.0.1:8000/')
            return
        time.sleep(1)
    print('The portal is still starting. Check the server window for errors.');sys.exit(1)
if __name__=='__main__':main()
