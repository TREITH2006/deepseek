$ErrorActionPreference='Stop'
$base=$PSScriptRoot
$gateway=Join-Path $base 'openclaw'
$chat=Join-Path $base 'local-agent'
try { Invoke-WebRequest 'http://127.0.0.1:18791/' -TimeoutSec 2 | Out-Null }
catch {
  Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $gateway 'Start-OpenClaw.ps1')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $gateway 'gateway.out.log') -RedirectStandardError (Join-Path $gateway 'gateway.err.log')
  $ready=$false
  for($i=0;$i -lt 60;$i++) {try {Invoke-WebRequest 'http://127.0.0.1:18791/' -TimeoutSec 2 | Out-Null;$ready=$true;break} catch {Start-Sleep -Seconds 1}}
  if(-not $ready){throw 'OpenClaw did not start; see openclaw/gateway.err.log.'}
}
try { $health=Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 2; if($health.model -ne 'qwen3.5:4b'){throw 'Another app is using the chat port.'} }
catch {
  Start-Process (Join-Path $chat 'standalone-venv\Scripts\python.exe') -ArgumentList (Join-Path $chat 'chat_server.py') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $chat 'chat.out.log') -RedirectStandardError (Join-Path $chat 'chat.err.log')
  $ready=$false
  for($i=0;$i -lt 30;$i++){try{Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 2 | Out-Null;$ready=$true;break}catch{Start-Sleep -Seconds 1}}
  if(-not $ready){throw 'Chat did not start; see local-agent/chat.err.log.'}
}
if((Test-Path (Join-Path $chat 'telegram-token.txt')) -and (Test-Path (Join-Path $chat 'telegram-chat-id.txt'))){
  $bridge=Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*telegram_bridge.py*'}
  if(-not $bridge){Start-Process (Join-Path $chat 'standalone-venv\Scripts\python.exe') -ArgumentList (Join-Path $chat 'telegram_bridge.py') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $chat 'telegram.out.log') -RedirectStandardError (Join-Path $chat 'telegram.err.log')}
}
Start-Process 'http://127.0.0.1:8765/'
Write-Host 'Local agent ready. Choose Agent mode on the page. Use Stop-Local-Agent.cmd to stop the setup.'
