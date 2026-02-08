# 🤖 Agents

Agent-Definitionen, Prompts, Rollen und Policies für das AI Empire System.

## Struktur

```
agents/
├── prompts/          # System-Prompts für verschiedene Agenten
├── roles/            # Rollen-Definitionen (z.B. Content-Agent, Research-Agent)
├── policies/         # Verhaltensregeln und Constraints
└── README.md
```

## Verwendung

Jeder Agent wird durch eine YAML-Datei definiert:

```yaml
name: content-agent
model: claude-3-sonnet
role: Content-Erstellung für X/Twitter
constraints:
  - max_tokens: 4096
  - language: de
  - tone: professional
```

## Bestehende Agenten

Siehe auch: `atomic-reactor/tasks/` für Task-basierte Agenten-Konfigurationen.
