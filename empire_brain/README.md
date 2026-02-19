# EMPIRE_BRAIN

Central knowledge and memory architecture for the AIEmpire system.

This directory is designed to be synced to iCloud at:
`~/Library/Mobile Documents/com~apple~CloudDocs/EMPIRE_BRAIN/`

## Structure

```
empire_brain/
├── memory/
│   ├── chats/       # Chat history imports for context continuity
│   └── knowledge/   # Extracted knowledge, facts, decisions
├── projects/        # Active project files and tracking
├── assets/          # Reusable assets (templates, images, configs)
├── revenue/         # Revenue tracking, reports, financial data
└── legacy/          # Inheritance documentation, business continuity
```

## Sync Instructions (macOS)

To enable iCloud sync, create a symlink:
```bash
ln -s ~/AIEmpire-Core/empire_brain ~/Library/Mobile\ Documents/com~apple~CloudDocs/EMPIRE_BRAIN
```

This gives you mobile access to all empire data via the Files app on iOS/iPadOS.
