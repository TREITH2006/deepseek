"""Show a separate agent pointer over managed Chrome without moving Windows cursor. MIT."""
import json,os,pathlib,psutil,subprocess,sys
from pywinauto import Desktop
args=json.load(sys.stdin)
state=pathlib.Path(os.environ['OPENCLAW_STATE_DIR']).resolve();profile=str(state/'browser'/'openclaw'/'user-data').lower();pids=set()
for process in psutil.process_iter(['pid','name','cmdline']):
    try:
        line=' '.join(process.info['cmdline'] or []).lower()
        if process.info['name'].lower()=='chrome.exe' and profile in line and '--type=' not in line:pids.add(process.pid)
    except (psutil.Error,AttributeError):pass
windows=[window for window in Desktop(backend='uia').windows() if window.process_id() in pids and window.class_name()=='Chrome_WidgetWin_1']
if len(windows)!=1:raise RuntimeError('Exactly one setup-owned Chrome window is required')
window=windows[0];window.restore();window.set_focus();rect=window.rectangle()
ratio=float(args['dpr']);border=max(0,(float(args['outerWidth'])-float(args['innerWidth']))/2)
x=round(rect.left+(border+float(args['x']))*ratio);y=round(rect.top+(float(args['outerHeight'])-float(args['innerHeight'])-border+float(args['y']))*ratio)
helper=pathlib.Path(__file__).with_name('agent_pointer.py')
subprocess.run([sys.executable,str(helper)],input=json.dumps({'x':x,'y':y}),text=True,capture_output=True,timeout=3,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=True)
result={'agent_pointer_shown':True,'target':[x,y],'system_cursor_moved':False}
print(json.dumps(result))
