$ErrorActionPreference='Stop'
$chat=Join-Path $PSScriptRoot 'local-agent'
if(-not (Test-Path $chat)){$chat=Join-Path $PSScriptRoot 'local-backend'}
$token=Read-Host 'Paste the NEW Telegram bot token' -AsSecureString
$pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
try{$plain=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)}finally{[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)}
if($plain -notmatch '^\d+:[A-Za-z0-9_-]{20,}$'){throw 'The bot token format is invalid.'}
$api='https://api.telegram.org/bot'+$plain+'/'
$identity=Invoke-RestMethod ($api+'getMe') -TimeoutSec 15
if(-not $identity.ok){throw 'Telegram rejected this bot token.'}
$pairCode='PAIR-'+(Get-Random -Minimum 100000 -Maximum 999999)
Write-Host ('Open Telegram, find @'+$identity.result.username+', press Start, and send this exact pairing code:')
Write-Host $pairCode -ForegroundColor Cyan
Write-Host 'Waiting up to two minutes for the pairing message...'
$chatId=$null;$offset=0
for($attempt=0;$attempt -lt 24 -and -not $chatId;$attempt++){
  $updates=Invoke-RestMethod ($api+'getUpdates?timeout=5&offset='+$offset) -TimeoutSec 10
  foreach($update in $updates.result){
    $offset=[long]$update.update_id+1
    if($update.message.text -eq $pairCode){$chatId=[string]$update.message.chat.id;break}
  }
}
if(-not $chatId){throw 'Pairing timed out. Run this setup again and send the displayed code.'}
[IO.File]::WriteAllText((Join-Path $chat 'telegram-token.txt'),$plain,(New-Object Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $chat 'telegram-chat-id.txt'),$chatId,(New-Object Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $chat 'telegram-offset.txt'),[string]$offset,(New-Object Text.UTF8Encoding($false)))
Write-Host ('Telegram account paired with @'+$identity.result.username+'. Restart the local agent.') -ForegroundColor Green
