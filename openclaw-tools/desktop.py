"""Bounded visible Windows application control for locally generated work. MIT."""
import ctypes, json, os, psutil, sys, time
from ctypes import wintypes
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

args=json.load(sys.stdin)
action=args['action']
ALLOWED={'code.exe','notepad.exe'}
BLOCKED_WORDS={'password','passcode','otp','verification code','payment','checkout','bank','sign in','login'}

def windows():
    found=[]
    for w in Desktop(backend='uia').windows():
        try:
            pid=w.process_id(); proc=psutil.Process(pid).name().lower(); title=w.window_text().strip()
            if proc in ALLOWED and title and w.is_visible(): found.append((w,proc,title))
        except Exception: pass
    return found

def get_window():
    needle=args.get('window','').strip().lower()
    matches=[x for x in windows() if needle and needle in x[2].lower()]
    if len(matches)!=1: raise ValueError('Specify text matching exactly one supported VS Code or Notepad window')
    w,proc,title=matches[0]
    if any(word in title.lower() for word in BLOCKED_WORDS): raise ValueError('Sensitive or credential window is blocked')
    w.restore();w.set_focus();time.sleep(.25)
    return w,proc,title

def controls(w):
    items=[]
    allowed_types={'Button','Edit','Document','MenuItem','TabItem','ListItem','TreeItem','ComboBox','Text'}
    for c in w.descendants():
        try:
            kind=c.element_info.control_type
            name=c.window_text().strip()
            if kind not in allowed_types or not c.is_visible() or not c.is_enabled(): continue
            r=c.rectangle()
            if r.width()<=1 or r.height()<=1: continue
            items.append((c,{'index':len(items),'name':name[:180],'type':kind,'rect':[r.left,r.top,r.right,r.bottom]}))
            if len(items)>=160: break
        except Exception: pass
    return items

def move_pointer(rect):
    target=(int((rect.left+rect.right)/2),int((rect.top+rect.bottom)/2))
    point=wintypes.POINT();user32=ctypes.windll.user32;user32.GetCursorPos(ctypes.byref(point));start=(point.x,point.y)
    for step in range(1,46):
        t=step/45;t=t*t*(3-2*t)
        user32.SetCursorPos(round(start[0]+(target[0]-start[0])*t),round(start[1]+(target[1]-start[1])*t));time.sleep(.02)
    time.sleep(.25)

if action=='list_windows':
    result={'windows':[{'title':title,'process':proc} for _,proc,title in windows()]}
elif action=='focus':
    _,proc,title=get_window();result={'focused':title,'process':proc}
elif action=='inspect':
    w,proc,title=get_window();result={'window':title,'process':proc,'controls':[item for _,item in controls(w)]}
elif action in {'click_control','type_text'}:
    w,proc,title=get_window();items=controls(w);index=args.get('control_index')
    if not isinstance(index,int) or index<0 or index>=len(items): raise ValueError('Use a control_index returned by inspect')
    control,meta=items[index]
    if any(word in (title+' '+meta['name']).lower() for word in BLOCKED_WORDS): raise ValueError('Sensitive or credential control is blocked')
    move_pointer(control.rectangle())
    control.click_input();time.sleep(.25)
    if action=='type_text':
        text=args.get('text','')
        if not isinstance(text,str) or len(text)>4000: raise ValueError('Text must be at most 4000 characters')
        if args.get('replace',False): send_keys('^a{BACKSPACE}')
        # Send Unicode keystrokes directly; no clipboard or hidden paste buffer.
        INPUT_KEYBOARD=1;KEYEVENTF_UNICODE=4;KEYEVENTF_KEYUP=2
        class KEYBDINPUT(ctypes.Structure): _fields_=[('wVk',wintypes.WORD),('wScan',wintypes.WORD),('dwFlags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ctypes.POINTER(ctypes.c_ulong))]
        class INPUT(ctypes.Structure): _fields_=[('type',wintypes.DWORD),('ki',KEYBDINPUT)]
        for ch in text:
            for flags in (KEYEVENTF_UNICODE,KEYEVENTF_UNICODE|KEYEVENTF_KEYUP):
                inp=INPUT(INPUT_KEYBOARD,KEYBDINPUT(0,ord(ch),flags,0,None));ctypes.windll.user32.SendInput(1,ctypes.byref(inp),ctypes.sizeof(inp))
        result={'window':title,'control':meta,'typed_characters':len(text)}
    else: result={'window':title,'clicked':meta}
elif action=='hotkey':
    w,proc,title=get_window();keys=args.get('keys','')
    permitted={'^s','^f','^p','^`','{ESC}','{ENTER}','{F5}','^+p'}
    if keys not in permitted: raise ValueError('Hotkey is not in the approved development set')
    send_keys(keys);result={'window':title,'hotkey':keys}
else: raise ValueError('Unsupported action')
print(json.dumps(result,ensure_ascii=False))
