# Local Qwen Windows Agent

This repository contains a Vercel-ready static frontend and the source for its local Windows companion. Ollama, OpenClaw, Qwen, browser control, development commands and Windows application control remain on the user's PC.

## Start the installed backend on this PC

```powershell
cd "C:\Users\adi86\Documents\Codex\2026-10-12\wha\outputs"
.\Start-Local-Agent.cmd
.\Show-Local-Agent-Token.cmd
```

Keep that terminal setup running. Paste the displayed token only into your own Vercel site.

## Deploy the frontend on Vercel

Import this GitHub repository as a new Vercel project. No framework preset, build command or install command is required. Use the repository root as the output directory.

After deployment:

1. Open your Vercel site.
2. Keep **Local backend URL** set to `http://127.0.0.1:8765`.
3. Paste the local pairing token.
4. Select **Connect local PC**.

## Stop the backend

```powershell
cd "C:\Users\adi86\Documents\Codex\2026-10-12\wha\outputs"
.\Stop-Local-Agent.cmd
```

## Security

Never commit the pairing token, model weights, virtual environments, browser profiles, cookies, logs or task workspaces. The local backend accepts paired requests only from HTTPS `*.vercel.app` origins or explicitly configured origins. Sensitive actions remain blocked by the local tools.
