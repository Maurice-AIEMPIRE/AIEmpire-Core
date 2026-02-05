# Claude Intake

Drop files here to be ingested by automations.
Recommended format: one note per file, named like:
- 2026-02-05_claude_topic.md

Keep it clean:
- Short paragraphs
- Clear titles
- Action items at the end if possible


Run ingestion:
```bash
python3 -m automation.ingest --source folder --path claude_intake --execute
```
