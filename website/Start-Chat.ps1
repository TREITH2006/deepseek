$ErrorActionPreference = 'Stop'
$env:TEMP = Join-Path $PSScriptRoot 'temp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
& (Join-Path $PSScriptRoot 'standalone-venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'chat_server.py')
