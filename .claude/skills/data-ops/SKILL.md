# DATA OPS — Team Coordinator (D01-D10)

## Purpose
Manages the data pipeline: ingest raw files, normalize naming, extract text (OCR), deduplicate, tag entities/dates, build search index, cross-link documents, QA, and export.

## Triggers
- New files added to `data/inbox/`
- `[INGEST]` command
- Request for data inventory, search, or export

## Team Agents
- **D01 Data_Intake**: File inventory & classification
- **D02 Data_NormalizeNaming**: `YYYY-MM-DD_TYPE_DESCRIPTION.ext` convention
- **D03 Data_OCRExtract**: Text extraction from PDFs, images, scans
- **D04 Data_Dedupe**: Duplicate and near-duplicate detection
- **D05 Data_Tagging**: Entity extraction (people, dates, amounts, companies)
- **D06 Data_Indexer**: Search index / embeddings (ChromaDB)
- **D07 Data_CrossLink**: Relationship mapping between documents
- **D08 Data_QA**: Quality verification of all processed data
- **D09 Data_ExportManager**: Bundle exports (MD/PDF/ZIP)
- **D10 Data_Dashboards**: Status tables, pipeline overview

## Pipeline
1. **Intake** (D01): Scan `data/inbox/`, create `data/processed/INVENTORY.md`
2. **Normalize** (D02): Rename files per convention, move to `data/processed/`
3. **Extract** (D03): OCR images/scans, extract text from PDFs → `data/processed/`
4. **Dedupe** (D04): Flag duplicates → `data/processed/DEDUPE_REPORT.md`
5. **Tag** (D05): Extract entities → `data/index/TAGS.json`
6. **Index** (D06): Build/update search index → `data/index/INDEX_STATUS.md`
7. **CrossLink** (D07): Map relationships → `data/processed/CROSSLINK_MAP.md`
8. **QA** (D08): Verify all processed correctly
9. **Export** (D09): Bundle for delivery → `data/exports/`
10. **Dashboard** (D10): Update overview → `data/processed/DASHBOARD.md`

## Naming Convention
```
YYYY-MM-DD_TYPE_DESCRIPTION.ext
Examples:
2024-01-15_CONTRACT_firma-x-servicevertrag.pdf
2024-03-01_EMAIL_beschwerde-an-firma-x.pdf
2024-05-20_INVOICE_rechnung-q1-2024.pdf
```

## File Types
CONTRACT, EMAIL, INVOICE, SCREENSHOT, TESTIMONY, REPORT, PHOTO, CERTIFICATE, LETTER, OTHER

## Quality Gate
- Every file in `data/processed/` must be in INVENTORY.md
- Every file must have tags in TAGS.json
- No duplicate files (DEDUPE_REPORT must show 0 active duplicates)
- Naming convention must be followed 100%
