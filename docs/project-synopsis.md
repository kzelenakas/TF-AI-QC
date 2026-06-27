# TF AI-QC — Project Synopsis

**Project:** True Footage AI-Powered Appraisal Quality Control Platform
**Owner:** Kevin Zelenakas, Quality Development Specialist
**Organization:** True Footage
**Date:** June 27, 2026
**Status:** Pre-development — awaiting IT/legal hosting decision

---

## Problem Statement

True Footage's QA team reviews residential appraisal reports for USPAP compliance, GSE overlay requirements, and internal quality standards before loan delivery. As report volume grows and UAD 3.6 becomes mandatory (November 2, 2026), manual review creates three compounding problems:

1. **Speed** — Manual review of a full URAR takes 45–90 minutes. Volume spikes create backlogs that delay loan closings.
2. **Consistency** — Different reviewers catch different things. There is no systematic enforcement of the full UAD 3.6 rule set across every report.
3. **Coaching lag** — Appraiser feedback is reactive. Patterns across multiple reports from the same appraiser are not visible until problems accumulate.

---

## What TF AI-QC Does

TF AI-QC is an internal web application that automates the first-pass quality review of residential appraisal reports submitted in UAD 3.6 format.

### Core Functions

**1. Report Ingestion**
Accepts UAD 3.6 appraisal reports in XML or PDF format. Parses and stores structured report data for analysis.

**2. Automated Compliance Checking**
Runs reports against three rule layers:
- **GSE hard rules** — Fannie Mae and Freddie Mac's published UAD 3.6 Compliance API (709 URAR rules + 102 Restricted Report rules, updated May 14, 2026)
- **USPAP compliance flags** — scope of work, certification language, report type requirements
- **Internal quality checks** — True Footage-specific standards for market analysis, comp selection, adjustment support, and narrative quality

**3. Quality Scoring**
Scores each report across five dimensions: comparable selection, adjustment support, market analysis, narrative quality, and reconciliation. Produces an overall quality score with dimension-level detail.

**4. Revision Workflow**
Generates structured revision requests from failed checks. Routes requests to the appraiser, tracks response, and logs resolution. Eliminates manual revision request drafting.

**5. Appraiser Performance Tracking**
Aggregates findings by appraiser over time. Surfaces recurring issue patterns for coaching and training prioritization.

---

## Who Uses It

| User | Role |
|------|------|
| **QA Reviewers** | Run compliance checks, review AI findings, approve or override, issue revision requests |
| **Appraisers** | Receive revision requests, submit corrections |
| **QDS / Kevin** | Monitor appraiser performance trends, manage rules, review coaching data |
| **Management** | Dashboard visibility into QA throughput, appraiser quality scores, revision rates |

---

## Business Impact

| Metric | Current State | Target |
|--------|--------------|--------|
| First-pass review time | 45–90 min/report | Under 15 min/report |
| Consistency of rule enforcement | Reviewer-dependent | 100% of UAD 3.6 rules checked on every report |
| Revision request drafting | Manual, 10–20 min each | Auto-generated from failed checks |
| Appraiser coaching | Reactive, per-report | Proactive, pattern-based across reports |
| UAD 3.6 compliance | Manual tracking | Automated before submission to UCDP |

---

## Regulatory Context

- **UAD 3.6 mandatory deadline:** November 2, 2026 — all appraisal reports on loans sold to Fannie Mae or Freddie Mac must use UAD 3.6
- **GLBA / FTC Safeguards Rule:** Appraisal reports contain NPI (borrower name, property address, loan data). Any system processing this data must meet GLBA data security requirements
- **USPAP:** All automated findings must be positioned as tools supporting — not replacing — the licensed appraiser's judgment

---

## What This Is Not

- Not a replacement for licensed appraisers or QA reviewers — it is a first-pass tool that flags issues for human review
- Not a valuation tool — it does not produce or modify value opinions
- Not a submission tool — it validates before UCDP submission but does not submit

---

## Success Criteria

1. 100% of UAD 3.6 hard rules checked on every report before submission
2. QA first-pass review time reduced by 60% or more
3. Revision request drafting time eliminated
4. Appraiser performance trends visible in dashboard within 30 days of launch
5. Zero NPI exposure incidents
