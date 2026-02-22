# HEARTBEAT.md — Proactive Work Queue

## Reverse Prompt (when idle)
When nothing else needs attention, ask yourself:
- "Based on what I know about Maurice and his goals, what is the next best task?"
- "What system is underperforming or broken that I could fix right now?"
- "What quick win (<15 min) would move revenue forward?"
Post findings to main session with [reverse-prompt] prefix.

## Periodic Checks (rotate through, 2-4x/day)
- [ ] Git status — uncommitted changes? stale branches?
- [ ] Memory files — anything from yesterday that needs follow-up?
- [ ] System health — Ollama running? Redis up? CRM responding?
- [ ] Revenue pipeline — any Gumroad sales? Fiverr inquiries?

## DO NOT CHECK
- Email (security risk — prompt injection vector)
- Direct X/Twitter API (bot detection risk)

## When to reach out
- Revenue event (sale, lead, inquiry)
- System down or degraded
- Reverse prompt found high-impact opportunity
- It's been >8h since any interaction

## When to stay quiet (HEARTBEAT_OK)
- Late night (23:00-08:00) unless urgent
- Nothing new since last check
- Last check was <30 minutes ago
