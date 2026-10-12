# Local Qwen Windows Agent

This repository contains a Vercel-ready static frontend and the source for its local Windows companion. Ollama, OpenClaw, Qwen, browser control, development commands and Windows application control remain on the user's PC.

The frontend also supports local voice interaction. Press **Start talking**, speak a task, then press **Stop and run**. Faster-Whisper transcribes the recording on the PC, the existing bounded agent executes it, live progress remains visible, and Piper reads the final result aloud. Audio is limited to 60 seconds and is not retained.

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
5. Allow microphone access when using **Start talking**.

## Stop the backend

```powershell
cd "C:\Users\adi86\Documents\Codex\2026-10-12\wha\outputs"
.\Stop-Local-Agent.cmd
```

## Security

Never commit the pairing token, model weights, virtual environments, browser profiles, cookies, logs or task workspaces. The local backend accepts paired requests only from HTTPS `*.vercel.app` origins or explicitly configured origins. Sensitive actions remain blocked by the local tools.
# Telegram bridge

The optional Telegram bridge runs on this PC and sends text tasks through the same local OpenClaw agent. Coding tasks return the structured result, a PDF report, and a ZIP containing files created or changed by that task.

1. Revoke any bot token that was pasted into a chat or shared elsewhere.
2. Generate a replacement token and find your numeric Telegram chat ID.
3. Run `Set-Telegram-Bridge.ps1` locally and enter both values at its private prompts.
4. Restart with `Start-Local-Agent.cmd`.

The token, chat ID, update offset, task logs, and generated result files stay local and are excluded from Git.
