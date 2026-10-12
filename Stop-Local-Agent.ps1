$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath($PSScriptRoot)+'\'
$owned=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like ('*'+$root+'*') -and $_.Name -in @('node.exe','chrome.exe','python.exe') }
foreach($proc in $owned){Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue}
try { Invoke-RestMethod 'http://127.0.0.1:11439/api/generate' -Method Post -ContentType 'application/json' -Body '{"model":"qwen3.5:4b","keep_alive":0}' -TimeoutSec 15 | Out-Null }catch{}
Write-Host 'Agent and chat stopped; Qwen unloaded. Your ordinary Ollama service and other browser profiles remain available.'
