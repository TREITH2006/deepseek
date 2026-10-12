"""MIT licensed local helper. Deliberately limits generated code and file scope."""
import ast, ctypes, json, os, pathlib, shutil, subprocess, sys, time
from ctypes import wintypes
ROOT=pathlib.Path(__file__).resolve().parents[1]/'workspace'/'tasks'
ROOT.mkdir(parents=True,exist_ok=True)

def move_pointer(rect):
    target=(int((rect.left+rect.right)/2),int((rect.top+rect.bottom)/2))
    point=wintypes.POINT();user32=ctypes.windll.user32;user32.GetCursorPos(ctypes.byref(point));start=(point.x,point.y)
    for step in range(1,61):
        t=step/60;t=t*t*(3-2*t)
        user32.SetCursorPos(round(start[0]+(target[0]-start[0])*t),round(start[1]+(target[1]-start[1])*t));time.sleep(.02)
    time.sleep(.3)
a=json.load(sys.stdin)
action=a['action']
name=a.get('filename','')
p=(ROOT/name).resolve() if name else ROOT.resolve()
if name and (p==ROOT.resolve() or ROOT.resolve() not in p.parents): raise ValueError('Path outside task workspace')
if any(part.startswith('.') for part in pathlib.Path(name).parts): raise ValueError('Hidden paths are disabled')
if action=='save':
    text=a.get('content','')
    if len(text)>50000: raise ValueError('File too large')
    with p.open('x',encoding='utf-8') as f: f.write(text)
    result={'saved':str(p),'characters':len(text)}
elif action=='write':
    text=a.get('content','')
    if len(text)>100000: raise ValueError('File too large')
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text,encoding='utf-8')
    result={'written':str(p),'characters':len(text)}
elif action=='read':
    result={'filename':name,'content':p.read_text(encoding='utf-8')[:50000]}
elif action=='run_python':
    if p.suffix!='.py': raise ValueError('Python file required')
    source=p.read_text(encoding='utf-8')
    tree=ast.parse(source)
    allowed={'math','statistics','decimal','fractions','json','csv','datetime','random','itertools','collections'}
    for n in ast.walk(tree):
        if isinstance(n,ast.Import) and any(x.name not in allowed for x in n.names): raise ValueError('Unsupported import')
        if isinstance(n,ast.ImportFrom) and (n.level or n.module not in allowed): raise ValueError('Unsupported import')
        if isinstance(n,ast.Attribute) and n.attr.startswith('_'): raise ValueError('Private attributes disabled')
        if isinstance(n,ast.Attribute) and n.attr not in {'sqrt','isqrt','ceil','floor','gcd','lcm','sin','cos','tan','pi','e','log','log10','exp','factorial','comb','perm','mean','median','stdev','variance','Decimal','Fraction','dumps','loads','date','datetime','timedelta','today','now','year','month','day','total_seconds','chain','product','combinations','permutations','accumulate','count','repeat','islice'}: raise ValueError('Unsupported attribute or method')
        if isinstance(n,ast.Name) and (n.id.startswith('__') or n.id in {'open','exec','eval','compile','input','getattr','setattr','delattr','globals','locals','vars','breakpoint','help','exit','quit'}): raise ValueError('Unsupported operation')
    proc=subprocess.run([sys.executable,'-I',str(p)],cwd=ROOT,capture_output=True,text=True,timeout=10)
    result={'exit_code':proc.returncode,'stdout':proc.stdout[:12000],'stderr':proc.stderr[:4000]}
elif action=='notepad_show':
    if p.suffix not in {'.txt','.md'}: raise ValueError('Text file required')
    from pywinauto import Desktop
    before={w.handle for w in Desktop(backend='uia').windows()}
    subprocess.Popen(['notepad.exe',str(p)])
    win=None
    for _ in range(24):
        for w in Desktop(backend='uia').windows():
            if name.lower() in w.window_text().lower() and (w.handle not in before): win=w;break
        if win: break
        time.sleep(.3)
    if win is None: raise RuntimeError('New Notepad document window was not identified; existing windows untouched')
    win.set_focus()
    edits=win.descendants(control_type='Edit') or win.descendants(control_type='Document')
    if not edits: raise RuntimeError('Notepad editor unavailable')
    editor=edits[0]
    move_pointer(editor.rectangle())
    try: text=editor.get_value()
    except Exception:
        try: text=editor.iface_text.DocumentRange.GetText(-1)
        except Exception: text=editor.window_text()
    expected=p.read_text(encoding='utf-8')
    result={'window_title':win.window_text(),'editor_text':text[:12000],'verified':expected.strip() in text.strip()}
elif action=='run_command':
    command=a.get('command')
    if not isinstance(command,list) or not 1<=len(command)<=20 or not all(isinstance(x,str) and 0<len(x)<=500 for x in command): raise ValueError('command must be a short argument array')
    exe=pathlib.Path(command[0]).name.lower()
    aliases={'python':'python.exe','python.exe':'python.exe','node':'node.exe','node.exe':'node.exe','npm':'npm.cmd','npm.cmd':'npm.cmd','npx':'npx.cmd','npx.cmd':'npx.cmd','git':'git.exe','git.exe':'git.exe'}
    if exe not in aliases: raise ValueError('Only Python, Node, npm, npx and git are allowed')
    resolved=shutil.which(aliases[exe]) or shutil.which(command[0])
    if not resolved: raise ValueError('Requested development command is not installed')
    proc=subprocess.run([resolved,*command[1:]],cwd=p if p.is_dir() else p.parent,capture_output=True,text=True,timeout=60,env={**os.environ,'CI':'1','NO_COLOR':'1'})
    result={'command':command,'exit_code':proc.returncode,'stdout':proc.stdout[:30000],'stderr':proc.stderr[:10000]}
elif action=='vscode_show':
    if not p.exists(): raise ValueError('Create the file or project before opening it')
    code=shutil.which('code.cmd') or shutil.which('code') or pathlib.Path(os.environ.get('LOCALAPPDATA',''))/'Programs'/'Microsoft VS Code'/'bin'/'code.cmd'
    if not pathlib.Path(code).exists(): raise ValueError('VS Code command is not installed')
    from pywinauto import Desktop
    before={w.handle for w in Desktop(backend='uia').windows()}
    subprocess.Popen([str(code),'--new-window',str(p)],cwd=ROOT)
    win=None
    for _ in range(40):
        candidates=[w for w in Desktop(backend='uia').windows() if w.handle not in before and w.class_name()=='Chrome_WidgetWin_1' and 'visual studio code' in w.window_text().lower()]
        if candidates: win=candidates[0];break
        time.sleep(.25)
    if win is not None:
        win.restore();win.set_focus();time.sleep(.3);move_pointer(win.rectangle())
    result={'opened_in_vscode':str(p),'exists':True,'visible_pointer_moved':win is not None}
else: raise ValueError('Unsupported action')
print(json.dumps(result,ensure_ascii=False))
