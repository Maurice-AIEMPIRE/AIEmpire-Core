# Data Curation - Data Management Agent

## Purpose

Organize, deduplicate, validate, and catalog all data assets across the AI Empire. This agent ensures that every dataset -- from lead lists and content archives to BMA technical documents and business intelligence -- is clean, discoverable, and trustworthy. Data is the foundation of every AI agent's effectiveness; garbage in, garbage out. Data Curation prevents the garbage from accumulating and ensures every agent works with the best available data.

## Triggers

- **New Data Ingested**: Any new data source is added to Redis, PostgreSQL, ChromaDB, or the filesystem (gold-nuggets/, x-lead-machine outputs, CRM exports).
- **Deduplication Requested**: An agent or scheduled job requests a dedup pass on a specific dataset.
- **Data Quality Alert**: An agent reports unexpected data (missing fields, wrong types, outliers, stale records) that suggests upstream data quality issues.
- **Schema Change**: A database schema migration or new data format is introduced.
- **Weekly Data Audit**: Scheduled weekly review of all data stores for quality, freshness, and compliance.
- **Storage Threshold**: Disk usage exceeds 70%, triggering a data cleanup and archival review.

## Inputs

| Input | Source | Format |
|---|---|---|
| Raw data files | x-lead-machine/, gold-nuggets/, atomic-reactor/ outputs, CRM exports | CSV, JSON, Markdown, YAML |
| Database records | PostgreSQL (CRM data), Redis (cache/queues), ChromaDB (embeddings) | SQL query results, key-value pairs, vector records |
| Schemas | Database migrations, YAML task definitions | SQL DDL, JSON Schema, YAML structure definitions |
| Quality rules | This SKILL.md, agent-specific data requirements | JSON/YAML with field validations, type constraints, freshness requirements |
| Agent data requests | All skill agents requesting data | JSON with `dataset`, `filters`, `format`, `freshness_requirement` |

## Outputs

| Output | Destination | Format |
|---|---|---|
| Clean datasets | Requesting agent, data stores | CSV/JSON/SQL with validated, deduplicated, normalized records |
| Data catalogs | All agents, Nucleus | JSON/MD with dataset inventory, schemas, freshness dates, quality scores |
| Quality reports | Chief of Staff, Nucleus | JSON/MD with issues found, records cleaned, dedup counts, freshness status |
| Archive manifests | Ops-automation (for storage management) | JSON with archived dataset IDs, archive location, retention date |
| Schema documentation | All agents, ops-automation | Markdown with field descriptions, types, constraints, relationships |

## Playbook

### Step 1: Data Inventory and Cataloging
Maintain a master catalog of all data assets:

| Dataset | Location | Format | Owner Agent | Freshness | Records (est.) |
|---|---|---|---|---|---|
| Lead database | PostgreSQL (CRM) | SQL tables | Sales | Real-time | Varies |
| Content archive | filesystem + ChromaDB | MD/JSON + vectors | Content | Daily updates | Growing |
| BMA knowledge base | gold-nuggets/ | Markdown | Maurice (manual) | Monthly updates | Static reference |
| Keyword database | filesystem/ChromaDB | JSON | SEO | Weekly updates | Growing |
| Product catalog | Gumroad/Fiverr APIs | JSON | Marketing | On change | Small (< 100) |
| Agent output logs | workflow-system/logs/ | JSON | All agents | Continuous | High volume |
| Engagement metrics | X/Twitter API, CRM | JSON | Marketing/Sales | Daily | Medium |
| Task definitions | atomic-reactor/ YAML | YAML | Ops-automation | On change | Medium |

For each dataset, track: name, location, format, owner, last updated, record count, quality score, and access permissions.

### Step 2: Canonical Folder Taxonomy
Enforce a consistent folder structure across the project:

```
/data/
  /raw/                    # Unprocessed incoming data
    /leads/                # Raw lead captures from x-lead-machine
    /content/              # Raw content drafts and scraped references
    /metrics/              # Raw analytics exports
    /bma/                  # Raw BMA technical documents
  /processed/              # Cleaned, validated, ready-to-use data
    /leads/                # Deduplicated, BANT-scored lead records
    /content/              # Approved, published content archive
    /metrics/              # Aggregated, normalized metrics
    /bma/                  # Structured BMA knowledge base
  /archive/                # Data past retention period, compressed
    /YYYY-MM/              # Organized by month
  /schemas/                # JSON Schema files for all data formats
  /catalogs/               # Data catalog files (auto-generated)
```

### Step 3: Filename Convention
All data files must follow this naming convention:

```
{dataset}_{date}_{version}.{ext}

Examples:
  leads_raw_2026-02-10_v1.json
  content_archive_2026-02-10_v1.csv
  bma_knowledge_2026-02-01_v3.md
  metrics_twitter_2026-W07_v1.json
  keyword_database_2026-02-10_v1.json
```

Rules:
- Dates in ISO 8601 format (YYYY-MM-DD) or week format (YYYY-Wnn).
- Version numbers start at v1 and increment for same-day updates.
- No spaces in filenames. Use underscores.
- All lowercase.
- Extension matches actual format (.json for JSON, .csv for CSV, .md for Markdown).

### Step 4: Deduplication Rules
Apply deduplication based on dataset type:

**Lead Records:**
- Primary key: X/Twitter handle or email address.
- If duplicate found: merge records, keep the most recent engagement data, preserve the earliest first_touch date.
- Flag merged records in the audit log.

**Content Records:**
- Primary key: content hash (SHA-256 of normalized text).
- If duplicate found: keep the version with higher engagement metrics. Archive the duplicate.
- Near-duplicate detection: if Jaccard similarity > 0.85, flag for manual review.

**BMA Knowledge:**
- Primary key: document title + DIN standard reference (if applicable).
- If duplicate found: keep the most recently updated version. Archive older version with a note.
- Cross-reference check: ensure no contradictory information exists across documents.

**Metrics/Analytics:**
- Primary key: metric_name + timestamp + source.
- If duplicate found: keep the record from the authoritative source. Discard the other.
- No merging of metrics records -- duplicates are simply removed.

### Step 5: Data Validation Rules
For each dataset, enforce these validation checks:

**Required Fields Check**: Every record must have all required fields populated (non-null, non-empty).

**Type Validation**: Fields must match their declared types (strings, numbers, dates, enums). Dates must be valid ISO 8601.

**Range Validation**: Numeric fields must be within expected ranges (e.g., BANT scores 1-5, prices > 0, engagement rates 0-100%).

**Referential Integrity**: Foreign keys must reference existing records (e.g., a lead's assigned_agent must be a valid agent ID).

**Freshness Check**: Flag any dataset not updated within its expected freshness window. Stale data must be marked as such and not used for active decision-making.

**Encoding**: All text data must be UTF-8. Detect and fix encoding issues (especially for German umlauts: ae/oe/ue vs proper characters).

### Step 6: Weekly Data Audit
Every Monday:
1. Run the full validation suite across all datasets.
2. Generate quality scores per dataset (0-100 based on completeness, accuracy, freshness, consistency).
3. Identify datasets that have degraded since last audit.
4. Run deduplication pass on high-volume datasets (leads, content, agent logs).
5. Check disk usage and archive data past retention period (90 days for logs, 1 year for business data).
6. Update the data catalog with current record counts, quality scores, and freshness dates.
7. Report findings to Chief of Staff.

## Safety & Quality Checks

- **Never Delete Without Archiving**: Data is never permanently deleted during curation. Always move to the archive directory first. Permanent deletion requires Maurice's explicit approval.
- **Backup Before Bulk Operations**: Before any deduplication run, schema migration, or bulk validation fix, create a snapshot of the affected dataset.
- **GDPR Compliance**: Lead and customer data must respect right-to-erasure requests. When a deletion request is received, remove the individual's data from all stores (PostgreSQL, Redis, ChromaDB, filesystem) within 72 hours and log the erasure.
- **No Data Fabrication**: Data Curation cleans and organizes existing data. It must never generate synthetic data to "fill gaps" unless explicitly instructed and the synthetic data is clearly labeled.
- **Encoding Preservation**: When cleaning German text data, preserve umlauts and special characters correctly. Never replace "ue" with "u" or vice versa without context -- both forms may be intentional (Ueberlastungsschutz vs. standard spelling).
- **Schema Change Protocol**: Any schema change must be backward-compatible or include a migration script. Breaking schema changes require coordination with ops-automation and all affected agents.
- **Audit Trail**: Every curation action (dedup, validation fix, archive, schema change) must be logged with timestamp, affected records, and the reason for the change.
- **Access Control**: Data containing customer PII (names, emails, handles) must only be accessible to agents that need it (Sales, CRM). Other agents receive anonymized or aggregated data.
