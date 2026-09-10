---
id: audit-orchestrator
name: AI Discoverability Audit Orchestrator
version: 1.0.0
description: >
  Master orchestrator that coordinates the AI Discoverability audit. 
  It runs both Source Selection and Quote Feasibility sub-auditors, 
  merges and deduplicates their findings, handles severity escalation, 
  computes a composite score, and exports a standardized JSON report.
entrypoint: scripts/orchestrate.py
dependencies:
  - source-selection-auditor
  - quote-feasibility-auditor
tags:
  - orchestrator
  - ai-readiness
  - reporting
---

# AI Discoverability Audit Orchestrator

This skill coordinates sub-audits to generate a unified AI Discoverability benchmark report.
