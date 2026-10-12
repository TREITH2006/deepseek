"""Move the real Windows pointer to a target in this setup's Chrome only. MIT."""
import ctypes,json,os,pathlib,sys,time
from ctypes import wintypes
import psutil
from pywinauto import Desktop
args=json.load(sys.stdin)
state=pathlib.Path(os.environ['OPENCLAW_STATE_DIR']).resolve()
profile=str(state/'browser'/'openclaw'/'user-data').lower()
pids=set()
for p in psutil.process_iter(['pid','name','cmdline']):
    try:
        line=' '.join(p.info['cmdline'] or []).lower()
        if p.info['name'].lower()=='chrome.exe' and profile in line and '--type=' not in line:pids.add(p.pid)
    except (psutil.Error,AttributeError):pass
windows=[w for w in Desktop(backend='uia').windows() if w.process_id() in pids and w.class_name()=='Chrome_WidgetWin_1']
if len(windows)!=1:raise RuntimeError('Exactly one setup-owned Chrome window is required')
win=windows[0]
hwnd=win.handle
u=ctypes.windll.user32
# Restore a minimized browser and force this setup-owned window to the front.
u.ShowWindow(hwnd,9)  # SW_RESTORE
# A short topmost toggle reliably exposes the controlled window even when
# Windows' foreground-lock policy rejects an ordinary SetForegroundWindow.
SWP_NOMOVE,SWP_NOSIZE,SWP_SHOWWINDOW=0x0002,0x0001,0x0040
flags=SWP_NOMOVE|SWP_NOSIZE|SWP_SHOWWINDOW
u.SetWindowPos(hwnd,-1,0,0,0,0,flags)   # HWND_TOPMOST
u.SetWindowPos(hwnd,-2,0,0,0,0,flags)   # HWND_NOTOPMOST
u.BringWindowToTop(hwnd)
u.SetForegroundWindow(hwnd)
win.set_focus()
time.sleep(.15)
rect=win.rectangle()
ratio=float(args['dpr']);border=max(0,(float(args['outerWidth'])-float(args['innerWidth']))/2)
x=round(rect.left+(border+float(args['x']))*ratio)
y=round(rect.top+(float(args['outerHeight'])-float(args['innerHeight'])-border+float(args['y']))*ratio)
if not(rect.left<=x<rect.right and rect.top<=y<rect.bottom):raise ValueError('Target outside Chrome window')
point=wintypes.POINT();u.GetCursorPos(ctypes.byref(point));start=(point.x,point.y)
for i in range(1,61):
    t=i/60;t=t*t*(3-2*t)
    u.SetCursorPos(round(start[0]+(x-start[0])*t),round(start[1]+(y-start[1])*t));time.sleep(.025)
time.sleep(.35)
u.GetCursorPos(ctypes.byref(point))
result={'from':start,'to':[point.x,point.y],'target':[x,y],'verified':abs(point.x-x)<=2 and abs(point.y-y)<=2}
with (state.parent/'visible-pointer-actions.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
if not result['verified']:raise RuntimeError('Pointer did not reach target')
print(json.dumps(result))
