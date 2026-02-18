# LAUNCHD Consolidation Report

- Generated: 2026-02-18T22:37:37+01:00
- Mode: apply

| Function Group | Label | Role | Action |
|---|---|---|---|
| openclaw_gateway | `ai.openclaw.gateway` | canonical | keep |
| openclaw_gateway | `com.aiempire.guardian` | fallback | keep_as_fallback |
| openclaw_gateway | `com.openclaw.process-guardian` | shadow | disabled |
| telegram_router | `application.ru.keepcoder.Telegram.12052570.12053473` | shadow | disabled |
| telegram_router | `com.empire.telegrambot` | fallback | keep_as_fallback |
| youtube_autopilot | `com.maurice.youtube-shorts` | shadow | disabled |
| n8n | `com.ai-empire.n8n` | canonical | keep |
