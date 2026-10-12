import {spawn,execFileSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {isIP} from 'node:net';
import {fileURLToPath} from 'node:url';
const base=path.dirname(process.env.OPENCLAW_STATE_DIR);
const python=path.join(base,'..','local-agent','standalone-venv','Scripts','python.exe');
const log=path.join(base,'workstation-actions.jsonl');
const counts=new Map();
export default {id:'local-workstation',name:'Local workstation tools',register(api){
  api.on('before_tool_call',(event,ctx)=>{
    const key=ctx.sessionKey||ctx.runId||'local';
    const n=(counts.get(key)||0)+1; counts.set(key,n);
    fs.appendFileSync(log,JSON.stringify({time:new Date().toISOString(),run:key,tool:event.toolName,call:n})+'\n');
    if(n>16)return {block:true,blockReason:'Hard limit of 16 tool calls reached. Stop and report partial progress.'};
    try {
      const mib=Number(execFileSync('nvidia-smi',['--query-gpu=memory.used','--format=csv,noheader,nounits'],{encoding:'utf8',timeout:3000,windowsHide:true}).trim().split('\n')[0]);
      fs.appendFileSync(log,JSON.stringify({time:new Date().toISOString(),gpuMiB:mib,run:key})+'\n');
      if(mib*1048576>7000000000)return {block:true,blockReason:'Total GPU memory exceeds the configured 7 GB ceiling. Stop this task.'};
    }catch {return {block:true,blockReason:'GPU memory check unavailable; stop instead of running an unmeasured action.'};}
    if(event.toolName==='browser'){
      const p=event.params||{};
      const address=p.targetUrl||p.url;
      if(['open','navigate'].includes(p.action)&&!address)return {block:true,blockReason:'Navigation needs targetUrl or url. Use action open with the exact HTTPS publisher URL from the task.'};
      if(address){
        try{
          const u=new URL(address);
          if(isIP(u.hostname.replace(/^\[|\]$/g,'')))return {block:true,blockReason:'Use the publisher HTTPS domain, not an IP address. Do not invent IP-based URLs. Indian news domains are now permitted.'};
          if(u.protocol==='http:'&&u.port==='443')return {block:true,blockReason:'HTTP cannot use HTTPS port 443. Use the normal https:// publisher URL.'};
        }catch{return {block:true,blockReason:'Invalid URL. Use the normal publisher HTTPS domain.'};}
      }
      if(['upload','dialog','download','evaluate'].includes(p.action)||p.kind==='evaluate')return {block:true,blockReason:'This action is disabled in this local setup.'};
    }
  });
  api.registerTool({name:'workstation',label:'Local coding workspace, VS Code and Notepad',description:'Create and edit files only inside the dedicated task workspace, run bounded Python/Node/npm/npx/git commands there, and open a generated file or project in VS Code or Notepad. Never accesses personal files.',parameters:{type:'object',properties:{action:{type:'string',enum:['save','write','read','run_python','run_command','notepad_show','vscode_show']},filename:{type:'string'},content:{type:'string'},command:{type:'array',items:{type:'string'},maxItems:20}},required:['action'],additionalProperties:false},async execute(id,args){
    const result=await new Promise((resolve,reject)=>{
      const child=spawn(python,[path.join(base,'local-tools','workstation.py')],{cwd:base,windowsHide:true,stdio:['pipe','pipe','pipe']});
      let out='',err='';const timer=setTimeout(()=>{child.kill();reject(Error('Workstation operation exceeded 75 seconds'));},75000);
      child.stdout.on('data',d=>{out+=d;if(out.length>100000)child.kill();});child.stderr.on('data',d=>err+=d);
      child.on('error',e=>{clearTimeout(timer);reject(e)});child.on('close',code=>{clearTimeout(timer);if(code!==0)reject(Error(err.slice(-2000)||out));else resolve(out)});
      child.stdin.end(JSON.stringify(args));
    });
    fs.appendFileSync(log,JSON.stringify({time:new Date().toISOString(),tool:'workstation',arguments:args,result})+'\n');
    return {content:[{type:'text',text:result}]};
  }});
  api.registerTool({name:'news_digest',label:'Visible India news digest',description:'Visit five verified major Indian newspaper homepages in visible Chrome and extract one current visible headline per accessible publisher. Use this once for India-news or five-newspaper requests.',parameters:{type:'object',properties:{},additionalProperties:false},async execute(){
    const result=await new Promise((resolve,reject)=>{
      const child=spawn(python,[path.join(base,'local-tools','news_digest.py')],{cwd:base,windowsHide:true,stdio:['ignore','pipe','pipe']});
      let out='',err='';const timer=setTimeout(()=>{child.kill();reject(Error('News digest exceeded 100 seconds'));},100000);
      child.stdout.on('data',d=>{out+=d;if(out.length>100000)child.kill();});child.stderr.on('data',d=>err+=d);
      child.on('error',e=>{clearTimeout(timer);reject(e)});child.on('close',code=>{clearTimeout(timer);if(code!==0)reject(Error(err.slice(-3000)||out));else resolve(out)});
    });
    fs.appendFileSync(log,JSON.stringify({time:new Date().toISOString(),tool:'news_digest',result:JSON.parse(result)})+'\n');
    return {content:[{type:'text',text:result}]};
  }});
  api.registerTool({name:'desktop',label:'Visible supported Windows app control',description:'Launch an approved local app; list, focus and inspect supported windows; visibly click an inspected control, type text, or use an approved hotkey. Supports VS Code, Notepad, Explorer, Calculator, Paint, Word, Excel, PowerPoint and PDF readers when installed. Inspect first and use its current control index. Sensitive login, credential, payment, messaging, deletion and elevated-system actions are blocked.',parameters:{type:'object',properties:{action:{type:'string',enum:['launch_app','list_windows','focus','inspect','click_control','type_text','hotkey']},app:{type:'string',enum:['vscode','notepad','explorer','calculator','paint','word','excel','powerpoint']},window:{type:'string'},control_index:{type:'integer',minimum:0},text:{type:'string'},replace:{type:'boolean'},keys:{type:'string'}},required:['action'],additionalProperties:false},async execute(id,args){
    const result=await new Promise((resolve,reject)=>{
      const child=spawn(python,[path.join(base,'local-tools','desktop.py')],{cwd:base,windowsHide:true,stdio:['pipe','pipe','pipe']});
      let out='',err='';const timer=setTimeout(()=>{child.kill();reject(Error('Desktop operation exceeded 20 seconds'));},20000);
      child.stdout.on('data',d=>{out+=d;if(out.length>150000)child.kill();});child.stderr.on('data',d=>err+=d);
      child.on('error',e=>{clearTimeout(timer);reject(e)});child.on('close',code=>{clearTimeout(timer);if(code!==0)reject(Error(err.slice(-3000)||out));else resolve(out)});
      child.stdin.end(JSON.stringify(args));
    });
    fs.appendFileSync(log,JSON.stringify({time:new Date().toISOString(),tool:'desktop',arguments:{...args,text:args.text?`<${args.text.length} characters>`:undefined},result:JSON.parse(result)})+'\n');
    return {content:[{type:'text',text:result}]};
  }});
}};
