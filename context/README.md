# Context Folder

Drop reference documents here before running build sessions. Claude reads these when building rule logic, parsers, and QC checks.

## What's Here

| Folder | Contents |
|---|---|
| `guidelines/uspap/` | 2024 USPAP Standards 1-4 |
| `guidelines/gse/` | Freddie Mac SG 5600-Property (10-20-2025), UAD 3.6 Supplement (updated 06-03-2026), UAD3.6 Condition and Quality Rating Definitions, ANSI Z765-2021 Square Footage standard |
| `rule-references/QC_rules/` | Appendix H-1 Compliance Rules.xlsx, Appendix H-2 UAD Compliance Rules Update Report.xlsx — primary source for rule engine logic |
| `rule-references/uad-3.6/` | 36blank.pdf (blank UAD 3.6 form), Appendix A-1 (URAR Delivery Specification), Appendix C-1 (URAR Layout), Appendix E (Report Style Guide), Appendix F-1 (URAR Reference Guide), Appendix G-1, GSE_UAD_3.6.0_v1.3_schema/ (MISMO XSD) |
| `sample-reports/1004/` | GSE Appendix D-1 sample scenarios — SF1-5, SF5A, Condo1-2, Coop1, MH1, 2-4 unit (x2), scenario matrix, combined PDF |

Note: sample scenarios for condo/coop/2-4 unit/manufactured home are currently bundled under `1004/` as delivered in the GSE source package, not split into `1073/`, `1025/` by property type. Fine as-is — split out later only if it gets in the way during rule-writing.

## Privacy Rule
All current files are GSE-published reference/sample materials — no real borrower data. Keep it that way: never add real appraisal reports with borrower names, SSNs, loan numbers, or unredacted property addresses.
