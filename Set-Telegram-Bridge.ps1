$ErrorActionPreference='Stop'
$chat=Join-Path $PSScriptRoot 'local-agent'
if(-not (Test-Path $chat)){$chat=Join-Path $PSScriptRoot 'local-backend'}
$token=Read-Host 'Paste the NEW Telegram bot token' -AsSecureString
$pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
try{$plain=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)}finally{[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)}
$chatId=Read-Host 'Enter your numeric Telegram chat ID'
if($plain -notmatch '^\d+:[A-Za-z0-9_-]{20,}$'){throw 'The bot token format is invalid.'}
if($chatId -notmatch '^-?\d+$'){throw 'The Telegram chat ID must be numeric.'}
[IO.File]::WriteAllText((Join-Path $chat 'telegram-token.txt'),$plain,(New-Object Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $chat 'telegram-chat-id.txt'),$chatId,(New-Object Text.UTF8Encoding($false)))
Write-Host 'Telegram bridge credentials saved locally. Restart the local agent.'
