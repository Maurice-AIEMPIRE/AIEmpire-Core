# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

## My Setup

### SSH - iPhone
- Connection: Mac → iPhone (via USB oder WiFi)
- Script: `./scripts/fix_ssh_iphone.sh` (Auto-Diagnose + Reparatur)
- USB: `iproxy 2222 22 && ssh -p 2222 root@localhost`
- WiFi: `ssh root@<IPHONE_IP>`
- Config in .env: `IPHONE_SSH_USER`, `IPHONE_SSH_IP`, `IPHONE_SSH_PORT`, `IPHONE_USB_PORT`

---

Add whatever helps you do your job. This is your cheat sheet.
