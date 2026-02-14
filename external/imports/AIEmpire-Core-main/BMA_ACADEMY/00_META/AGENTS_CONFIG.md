# Agent Squad Configuration

This document defines the specialized Agent Squads for the BMA Knowledge Fortress.

## Squad 1: Architecture & Structure
**Focus**: Organizing the file system and maintaining integrity.
- **Chief Architect**: Enforces adherence to `STRUCTURE.md`.
- **Database Designer**: Manages metadata schemas (JSON/YAML sidecars).
- **Folder Strategist**: Renames and moves files to optimal locations.
- **Taxonomy Expert**: Applies consistent tagging (e.g., `#Esser`, `#Troubleshooting`).

## Squad 2: Data Mining & Extraction
**Focus**: Analyzing raw files.
- **Data Scout**: recursively scans `01_RAW_IMPORT` for valuable assets.
- **PDF Analyzer**: Extracts text and structure from PDF plans/procols.
- **CAD Parser**: Extracts layer info and device counts from DWG/DXF.
- **Code Extractor**: Parses loop configuration files.
- **Quality Checker**: Flags corrupted or irrelevant files.

## Squad 3: Knowledge Synthesis
**Focus**: Creating usable content.
- **Knowledge Curator**: Compiles extracted data into Wiki pages.
- **Case Study Writer**: Turns project folders into `README.md` stories (Challenge -> Solution).
- **FAQ Generator**: Identifies common questions from `01_RAW_IMPORT` communications.

## Squad 4: Quality & Reporting
**Focus**: Monitoring the process.
- **Sprint Reporter**: Aggregates daily progress logs.
- **Quality Auditor**: Randomly checks structured data against RAW.

## Usage
Each squad should be configured in OpenClaw with specific access rights to their respective domains (e.g., Squad 2 only reads `01_RAW` and writes to `02_ANALYZED`).
