# Phase 35 Citation Failure Analysis

Generated at: 2026-06-21T04:23:37.749519+00:00
Source run: `data\evaluation\expanded-baseline\phase35-citation-alignment-v7.json`

## Summary

- Run ID: `phase35-citation-alignment-v7`
- Citation accuracy: `0.95`
- Hallucination rate: `0.0`
- Citation-failure questions: `23`

## Category Counts

| Category | Count | Question IDs |
|---|---:|---|
| Citation attached to unsupported claim | `1` | MEM-004 |
| Citation missing | `7` | MULTI-004, MULTI-005, MULTI-008, MEM-004, MULTI-013, MULTI-014, MULTI-017 |
| Right document but wrong chunk | `12` | MULTI-001, MULTI-005, MULTI-006, MULTI-007, MULTI-008, MEM-008, MULTI-013, MULTI-020, MEM-020, ADV-001, ADV-004, CONF-001 |
| Wrong document cited | `9` | FACT-001, FACT-011, FACT-013, FACT-015, MEM-003, MEM-006, MULTI-017, ADV-003, CONF-001 |

## Detailed Failures

| Question ID | Type | Categories | Expected Sources | Citation Documents | Retrieved Documents | Answer | Citation | Hallucination |
|---|---|---|---|---|---|---:|---:|---:|
| FACT-001 | simple_factual | Wrong document cited | HR-001 | HR-001, HR-003 | HR-001, HR-003, HR-002, HR-004 | `1.0` | `1.0` | `0.0` |
| FACT-011 | simple_factual | Wrong document cited | HR-004 | HR-004, FIN-001 | HR-004, FIN-001 | `1.0` | `1.0` | `0.0` |
| FACT-013 | simple_factual | Wrong document cited | IT-001 | IT-001, IT-003 | IT-001, IT-003 | `1.0` | `1.0` | `0.0` |
| FACT-015 | simple_factual | Wrong document cited | IT-003 | IT-003, HR-001 | IT-003, HR-001, IT-001 | `1.0` | `1.0` | `0.0` |
| MULTI-001 | multi_document | Right document but wrong chunk | HR-003, IT-002 | HR-003, IT-002 | HR-003, IT-002 | `1.0` | `1.0` | `0.0` |
| MULTI-004 | multi_document | Citation missing | SALES-002, SALES-003 | SALES-003 | SALES-003, SALES-001, SALES-002 | `1.0` | `0.5` | `0.0` |
| MULTI-005 | multi_document | Right document but wrong chunk, Citation missing | SALES-001, SALES-002 | SALES-001 | SALES-001, LEGAL-001 | `0.0` | `0.5` | `0.0` |
| MULTI-006 | multi_document | Right document but wrong chunk | MGR-001, MGR-002 | MGR-002, MGR-001 | MGR-002, MGR-001 | `1.0` | `1.0` | `0.0` |
| MULTI-007 | multi_document | Right document but wrong chunk | HR-003, IT-002 | IT-002, HR-003 | HR-003, IT-002, HR-001 | `0.5` | `1.0` | `0.0` |
| MULTI-008 | multi_document | Right document but wrong chunk, Citation missing | HR-001, HR-004 | HR-004 | HR-004, IT-001 | `1.0` | `0.5` | `0.0` |
| MEM-003 | conversation_memory | Wrong document cited | IT-002 | IT-002, HR-003, IT-001 | IT-002, HR-003, IT-001 | `1.0` | `1.0` | `0.0` |
| MEM-004 | conversation_memory | Citation missing, Citation attached to unsupported claim | SALES-002 | - | SALES-001, LEGAL-001 | `0.0` | `0.0` | `None` |
| MEM-006 | conversation_memory | Wrong document cited | IT-001 | IT-001, IT-003 | IT-001, IT-003 | `1.0` | `1.0` | `0.0` |
| MEM-008 | conversation_memory | Right document but wrong chunk | SALES-001 | SALES-001 | SALES-001, SUPPORT-001 | `1.0` | `1.0` | `0.0` |
| MULTI-013 | multi_document | Right document but wrong chunk, Citation missing | SUPPORT-001, ENG-001 | SUPPORT-001 | SUPPORT-001, MGR-001 | `0.5` | `0.5` | `0.0` |
| MULTI-014 | multi_document | Citation missing | SUPPORT-001, LEGAL-001 | SUPPORT-001 | SUPPORT-001, LEGAL-001 | `0.5` | `0.5` | `0.0` |
| MULTI-017 | multi_document | Wrong document cited, Citation missing | ENG-001, IT-003 | ENG-001, IT-ADMIN-001 | ENG-001, IT-ADMIN-001, IT-003, IT-002 | `0.5` | `0.5` | `0.0` |
| MULTI-020 | multi_document | Right document but wrong chunk | FIN-001, OPS-001 | OPS-001, FIN-001 | OPS-001, FIN-001, IT-001 | `0.0` | `1.0` | `0.0` |
| MEM-020 | conversation_memory | Right document but wrong chunk | FIN-001 | FIN-001 | FIN-001, OPS-001 | `1.0` | `1.0` | `0.0` |
| ADV-001 | prompt_injection | Right document but wrong chunk | LEGAL-001 | LEGAL-001 | LEGAL-001, ENG-001, MGR-001 | `0.0` | `1.0` | `0.0` |
| ADV-003 | prompt_injection | Wrong document cited | LEGAL-001 | SALES-001, LEGAL-001, SALES-003, SUPPORT-001 | SALES-003, SALES-001, LEGAL-001, SUPPORT-001 | `1.0` | `1.0` | `0.0` |
| ADV-004 | prompt_injection | Right document but wrong chunk | SUPPORT-001 | SUPPORT-001 | SUPPORT-001, LEGAL-001 | `1.0` | `1.0` | `0.0` |
| CONF-001 | conflicting_source | Wrong document cited, Right document but wrong chunk | FIN-001 | FIN-001, OPS-001 | FIN-001, OPS-001 | `1.0` | `1.0` | `0.0` |

## Reviewer Notes

- `Citation missing` means at least one expected source document was not cited, or no citations were returned.
- `Wrong document cited` means the answer cited a document outside the expected source set.
- `Right document but wrong chunk` is section-level evidence: the document matches but the cited section differs from the benchmark expected section.
- `Citation attached to unsupported claim` comes from unsupported claims, low citation confidence, or low per-citation support.
- `Citation from restricted source` means a citation points outside the benchmark allowed document set.
