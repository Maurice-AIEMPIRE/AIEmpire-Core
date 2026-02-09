# Structure & Architecture

This document defines the 4-layer architecture of the BMA Knowledge Fortress.

## 00_META
Project-level documentation, configuration, and tracking.
- `README.md`: Project overview.
- `STRUCTURE.md`: This file.
- `ROADMAP.md`: Strategic plan.
- `AGENTS_CONFIG.md`: Definition of the Agent Squads.

## 01_RAW_IMPORT (The Landing Zone)
Untouched, original data.
- `from_codex_chat_X/`: Legacy AI exports.
- `tutorials/`: Collected learning materials.
- `documents/`: General docs.
- `_ARCHIVE/`: Processed items.

## 02_ANALYZED (The Processing Plant)
Intermediate outputs from Agent Squads.
- `patterns/`: Identified common problems/solutions.
- `duplicates/`: Logistics of redundant files.
- `gaps/`: identified missing knowledge areas.

## 03_KNOWLEDGE_BASE (The Fortress)
The clean, structured source of truth.
### Theory
- `normen/`: DIN 14675, VDE, VdS guidelines.
- `technologie/`: Sensor types, loop technology, etc.
- `best_practices/`: Proven methods.

### Practical
- `revisions/`: As-built documentation structure.
- `montage/`: Installation guides.
- `programming/`: System configuration logic.
- `maintenance/`: Service protocols.

### Cases
- Project-based case studies (2018-2024).

### FAQ
- Structured Q&A for the community/business.

## 04_PRODUCTS (The Output)
Client-facing deliverables.
- `online_course/`: Course modules.
- `community_content/`: Posts, articles.
- `consulting_templates/`: Checklists, reports.
- `ai_prompts/`: Refined prompts for future tasks.
