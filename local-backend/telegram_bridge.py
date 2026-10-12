"""Local Telegram-to-OpenClaw bridge. Secrets remain in local files. MIT."""
import json, pathlib, socket, textwrap, time, urllib.parse, urllib.request, uuid, zipfile

ROOT=pathlib.Path(__file__).resolve().parent
TOKEN=(ROOT/'telegram-token.txt').read_text(encoding='utf-8').strip()
CHAT_ID=(ROOT/'telegram-chat-id.txt').read_text(encoding='utf-8').strip()
OFFSET_FILE=ROOT/'telegram-offset.txt'
API=f'https://api.telegram.org/bot{TOKEN}/'
_getaddrinfo=socket.getaddrinfo
def _ipv4_only(host,port,*args,**kwargs):
    answers=_getaddrinfo(host,port,*args,**kwargs);ipv4=[answer for answer in answers if answer[0]==socket.AF_INET]
    return ipv4 or answers
socket.getaddrinfo=_ipv4_only

def telegram(method,data=None,timeout=70):
    body=urllib.parse.urlencode(data or {}).encode()
    with urllib.request.urlopen(urllib.request.Request(API+method,data=body),timeout=timeout) as response:return json.load(response)
def send(text):
    for chunk in (text[i:i+3900] for i in range(0,len(text),3900)): telegram('sendMessage',{'chat_id':CHAT_ID,'text':chunk})
def run_agent(task):
    payload=json.dumps({'task_id':uuid.uuid4().hex,'messages':[{'role':'user','content':task}]}).encode()
    request=urllib.request.Request('http://127.0.0.1:8765/api/agent',data=payload,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=220) as response:return json.load(response)['content']
def make_pdf(title,text,path):
    lines=[]
    for paragraph in (title+'\n\n'+text).splitlines() or ['']:
        lines.extend(textwrap.wrap(paragraph,92,replace_whitespace=False) or [''])
    pages=[lines[i:i+48] for i in range(0,len(lines),48)] or [[]]
    objects=[];kids=[]
    font_id=3
    objects.extend([b'',b'',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'])
    for page in pages:
        stream=['BT /F1 10 Tf 45 790 Td 13 TL']
        for line in page:
            safe=line.encode('latin-1','replace').decode('latin-1').replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            stream.append(f'({safe}) Tj T*')
        stream.append('ET');data='\n'.join(stream).encode('latin-1')
        content_id=len(objects)+1;objects.append(f'<< /Length {len(data)} >>\nstream\n'.encode()+data+b'\nendstream')
        page_id=len(objects)+1;kids.append(page_id);objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>'.encode())
    objects[0]=b'<< /Type /Catalog /Pages 2 0 R >>';objects[1]=f'<< /Type /Pages /Count {len(kids)} /Kids [{" ".join(f"{kid} 0 R" for kid in kids)}] >>'.encode()
    output=bytearray(b'%PDF-1.4\n');offsets=[0]
    for index,obj in enumerate(objects,1):offsets.append(len(output));output.extend(f'{index} 0 obj\n'.encode()+obj+b'\nendobj\n')
    xref=len(output);output.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:output.extend(f'{offset:010d} 00000 n \n'.encode())
    output.extend(f'trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode());path.write_bytes(output)
def send_document(path,caption):
    boundary='----LocalAgent'+uuid.uuid4().hex;parts=[]
    def field(name,value):parts.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()])
    field('chat_id',CHAT_ID);field('caption',caption[:900]);data=path.read_bytes()
    media='application/pdf' if path.suffix.lower()=='.pdf' else 'application/zip'
    parts.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{path.name}"\r\nContent-Type: {media}\r\n\r\n'.encode(),data,b'\r\n',f'--{boundary}--\r\n'.encode()])
    urllib.request.urlopen(urllib.request.Request(API+'sendDocument',data=b''.join(parts),headers={'Content-Type':f'multipart/form-data; boundary={boundary}'}),timeout=70).read()
def workspace_snapshot():
    workspace=ROOT.parent/'openclaw'/'workspace'/'tasks'
    return workspace,{path.resolve():path.stat().st_mtime_ns for path in workspace.rglob('*') if path.is_file() and path.stat().st_size<=20*1024*1024}
def zip_created_files(before):
    workspace,after=workspace_snapshot();changed=[path for path,stamp in after.items() if before.get(path)!=stamp]
    if not changed:return None
    archive=ROOT/'telegram-code-files.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as output:
        for path in changed:
            try:output.write(path,path.relative_to(workspace))
            except (OSError,ValueError):pass
    return archive if archive.exists() and archive.stat().st_size else None
def main():
    offset=int(OFFSET_FILE.read_text() or 0) if OFFSET_FILE.exists() else 0
    while True:
        try:
            updates=telegram('getUpdates',{'offset':offset,'timeout':50,'allowed_updates':'["message"]'})['result']
            for update in updates:
                offset=update['update_id']+1;OFFSET_FILE.write_text(str(offset),encoding='utf-8')
                message=update.get('message') or {}
                if str(message.get('chat',{}).get('id'))!=CHAT_ID:continue
                task=(message.get('text') or '').strip()
                if not task:send('Send a text task. Voice notes are not enabled in this bridge yet.');continue
                send('Task accepted by the local agent. I will send the verified result when it finishes.')
                try:
                    _,before=workspace_snapshot();result=run_agent(task);send(result)
                    if any(word in task.lower() for word in ('code','python','javascript','program','coding')):
                        report=ROOT/'telegram-code-result.pdf';make_pdf('Local Agent Coding Task',f'TASK\n{task}\n\nRESULT\n{result}',report);send_document(report,'Coding task report generated locally.')
                        archive=zip_created_files(before)
                        if archive:send_document(archive,'Complete files created or changed by this coding task.')
                except Exception as error:send('Task failed locally: '+str(error)[:500])
        except Exception:time.sleep(4)
if __name__=='__main__':main()
