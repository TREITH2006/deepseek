"""Bounded, visible five-publisher India news check. MIT licensed."""
import json, os, pathlib, subprocess, sys, time
from playwright.sync_api import sync_playwright

BASE=pathlib.Path(os.environ['OPENCLAW_STATE_DIR']).resolve().parent
SITES=[
    ('The Hindu','https://www.thehindu.com/'),
    ('The Indian Express','https://indianexpress.com/'),
    ('Hindustan Times','https://www.hindustantimes.com/'),
    ('Times of India','https://timesofindia.indiatimes.com/'),
    ('Deccan Herald','https://www.deccanherald.com/'),
]
SKIP={'news','latest news','india news','home','top news','trending','latest','more','photos','videos','live'}

def ensure_browser():
    try:
        import urllib.request
        urllib.request.urlopen('http://127.0.0.1:18802/json/version',timeout=2).read()
    except Exception:
        env=dict(os.environ,OPENCLAW_STATE_DIR=str(BASE/'state'),OPENCLAW_CONFIG_PATH=str(BASE/'state'/'openclaw.json'))
        subprocess.run([str(BASE/'runtime'/'openclaw.cmd'),'browser','start','--json'],cwd=BASE,env=env,capture_output=True,text=True,timeout=45,check=True)

def clean(values):
    seen=[]
    for value in values:
        text=' '.join(value.split()).strip(' |–—-')
        if 28<=len(text)<=240 and text.lower() not in SKIP and text not in seen:
            seen.append(text)
    return seen

ensure_browser()
results=[]
with sync_playwright() as pw:
    browser=pw.chromium.connect_over_cdp('http://127.0.0.1:18802',timeout=10000)
    context=browser.contexts[0]
    page=context.pages[0] if context.pages else context.new_page()
    for publisher,url in SITES:
        item={'publisher':publisher,'url':url,'accessible':False}
        try:
            page.bring_to_front()
            page.goto(url,wait_until='domcontentloaded',timeout=15000)
            page.wait_for_timeout(1200)
            headings=clean(page.locator('h1,h2,h3').all_inner_texts())
            dates=clean(page.locator('time').all_inner_texts())
            pointer_moved=False
            if headings:
                for node in page.locator('h1,h2,h3').all()[:30]:
                    if ' '.join(node.inner_text().split()).strip(' |–—-')==headings[0]:
                        box=node.bounding_box()
                        if box:
                            geometry=page.evaluate('()=>({outerWidth,innerWidth,outerHeight,innerHeight,dpr:devicePixelRatio})')
                            payload={**geometry,'x':box['x']+box['width']/2,'y':box['y']+box['height']/2}
                            moved=subprocess.run([sys.executable,str(BASE/'local-tools'/'visible_pointer.py')],input=json.dumps(payload),text=True,capture_output=True,timeout=10,env=os.environ)
                            pointer_moved=moved.returncode==0
                        break
            item.update(accessible=bool(headings),page_title=page.title()[:300],headline=headings[0] if headings else None,visible_time=dates[0] if dates else None,final_url=page.url,pointer_moved=pointer_moved)
        except Exception as error:
            item['error']=str(error).splitlines()[0][:300]
        results.append(item)
    browser.close()
print(json.dumps({'checked_at_local':time.strftime('%Y-%m-%d %H:%M:%S'),'results':results},ensure_ascii=False))
