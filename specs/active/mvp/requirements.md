# Requirements — VYVY Text Investigation MVP

## R1 — Text input

The system shall accept one text field between 10 and 12,000 characters.

## R2 — Fast Check

The system shall return a risk band, score, red flags and immediate actions without requiring external search.

## R3 — Intake

The system shall summarize text, identify domain/intent, extract entities and produce search-ready claims.

## R4 — Classification

The system shall identify one or more scam patterns and whether immediate warning is required.

## R5 — Evidence

The system shall search through a provider adapter and normalize returned results. It shall not fabricate evidence.

## R6 — Source credibility

The system shall score source credibility and relevance using explainable rules.

## R7 — Expert analysis

Four expert roles shall return typed assessments. Independent experts should execute concurrently.

## R8 — Behavioral analysis

The system shall detect manipulation patterns and produce a behavioral risk score.

## R9 — Judge

The Judge shall reject unsupported findings, preserve disagreements and identify missing evidence.

## R10 — Verification

The system shall calculate final risk and confidence deterministically.

## R11 — Safety

The system shall provide safe, non-confrontational, practical next steps.

## R12 — Report

The system shall return a structured report and Markdown representation.

## R13 — Partial operation

The system shall return partial results when optional providers fail.

## R14 — Mock Mode

The system shall support deterministic, clearly labeled offline demo fixtures.

## R15 — Privacy

The MVP shall not persist user text.

## R16 — Scope exclusion

The MVP shall not include OCR, images, files, PDF parsing, authentication, database, extension, admin dashboard or realtime monitoring.
