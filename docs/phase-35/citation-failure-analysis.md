# Phase 35 Citation Failure Analysis

Generated at: 2026-06-21T04:12:20.326605+00:00
Source run: `data\evaluation\expanded-baseline\phase34-answer-grounding-v6.json`

## Summary

- Run ID: `phase34-answer-grounding-v6`
- Citation accuracy: `0.887`
- Hallucination rate: `0.024`
- Citation-failure questions: `23`

## Category Counts

| Category | Count | Question IDs |
|---|---:|---|
| Citation attached to unsupported claim | `5` | FACT-012, MULTI-003, MEM-004, ADV-003, ADV-005 |
| Citation missing | `15` | FACT-012, MULTI-003, MULTI-004, MULTI-005, MULTI-006, MULTI-008, MULTI-010, MEM-004, MULTI-011, MULTI-013, MULTI-014, MULTI-017, MULTI-019, MULTI-020, ADV-003 |
| Right document but wrong chunk | `8` | MULTI-001, MULTI-005, MULTI-007, MULTI-008, MEM-008, MULTI-013, MEM-020, ADV-004 |
| Wrong document cited | `3` | MEM-003, MEM-006, MULTI-017 |

## Detailed Failures

| Question ID | Type | Categories | Expected Sources | Citation Documents | Retrieved Documents | Answer | Citation | Hallucination |
|---|---|---|---|---|---|---:|---:|---:|
| FACT-012 | simple_factual | Citation missing, Citation attached to unsupported claim | IT-001 | - | IT-001, IT-003 | `0.0` | `0.0` | `None` |
| MULTI-001 | multi_document | Right document but wrong chunk | HR-003, IT-002 | HR-003, IT-002 | HR-003, IT-002 | `0.5` | `1.0` | `0.0` |
| MULTI-003 | multi_document | Citation missing, Citation attached to unsupported claim | HR-001, HR-002 | HR-002 | HR-002, HR-001 | `1.0` | `0.5` | `1.0` |
| MULTI-004 | multi_document | Citation missing | SALES-002, SALES-003 | SALES-003 | SALES-003 | `1.0` | `0.5` | `0.0` |
| MULTI-005 | multi_document | Right document but wrong chunk, Citation missing | SALES-001, SALES-002 | SALES-001 | SALES-001 | `0.0` | `0.5` | `0.0` |
| MULTI-006 | multi_document | Citation missing | MGR-001, MGR-002 | MGR-002 | MGR-002, MGR-001 | `1.0` | `0.5` | `0.0` |
| MULTI-007 | multi_document | Right document but wrong chunk | HR-003, IT-002 | HR-003, IT-002 | HR-003, IT-002 | `1.0` | `1.0` | `0.0` |
| MULTI-008 | multi_document | Right document but wrong chunk, Citation missing | HR-001, HR-004 | HR-004 | HR-004 | `1.0` | `0.5` | `0.0` |
| MULTI-010 | multi_document | Citation missing | HR-003, HR-ADMIN-001 | HR-003 | HR-003 | `1.0` | `0.5` | `0.0` |
| MEM-003 | conversation_memory | Wrong document cited | IT-002 | IT-002, HR-003 | IT-002, HR-003, IT-001 | `1.0` | `1.0` | `0.0` |
| MEM-004 | conversation_memory | Citation missing, Citation attached to unsupported claim | SALES-002 | - | SALES-001, LEGAL-001 | `0.0` | `0.0` | `None` |
| MEM-006 | conversation_memory | Wrong document cited | IT-001 | IT-001, IT-003 | IT-001, IT-003 | `1.0` | `1.0` | `0.0` |
| MEM-008 | conversation_memory | Right document but wrong chunk | SALES-001 | SALES-001 | SALES-001 | `1.0` | `1.0` | `0.0` |
| MULTI-011 | multi_document | Citation missing | FIN-001, OPS-001, LEGAL-001 | FIN-001, LEGAL-001 | FIN-001, LEGAL-001, OPS-001 | `1.0` | `0.5` | `0.0` |
| MULTI-013 | multi_document | Right document but wrong chunk, Citation missing | SUPPORT-001, ENG-001 | SUPPORT-001 | SUPPORT-001, MGR-001 | `0.5` | `0.5` | `0.0` |
| MULTI-014 | multi_document | Citation missing | SUPPORT-001, LEGAL-001 | SUPPORT-001 | SUPPORT-001, LEGAL-001 | `0.5` | `0.5` | `0.0` |
| MULTI-017 | multi_document | Wrong document cited, Citation missing | ENG-001, IT-003 | ENG-001, IT-ADMIN-001 | ENG-001, IT-ADMIN-001, IT-003 | `0.5` | `0.5` | `0.0` |
| MULTI-019 | multi_document | Citation missing | SALES-001, LEGAL-001 | SALES-001 | LEGAL-001, SALES-001 | `1.0` | `0.5` | `0.0` |
| MULTI-020 | multi_document | Citation missing | FIN-001, OPS-001 | OPS-001 | OPS-001, FIN-001 | `0.0` | `0.5` | `0.0` |
| MEM-020 | conversation_memory | Right document but wrong chunk | FIN-001 | FIN-001 | FIN-001 | `1.0` | `1.0` | `0.0` |
| ADV-003 | prompt_injection | Citation missing, Citation attached to unsupported claim | LEGAL-001 | - | SALES-003, SALES-001, LEGAL-001 | `0.0` | `0.0` | `None` |
| ADV-004 | prompt_injection | Right document but wrong chunk | SUPPORT-001 | SUPPORT-001 | SUPPORT-001 | `0.5` | `1.0` | `0.0` |
| ADV-005 | prompt_injection | Citation attached to unsupported claim | LEGAL-001 | LEGAL-001 | LEGAL-001, SUPPORT-001 | `0.5` | `1.0` | `1.0` |

## Reviewer Notes

- `Citation missing` means at least one expected source document was not cited, or no citations were returned.
- `Wrong document cited` means the answer cited a document outside the expected source set.
- `Right document but wrong chunk` is section-level evidence: the document matches but the cited section differs from the benchmark expected section.
- `Citation attached to unsupported claim` comes from unsupported claims, low citation confidence, or low per-citation support.
- `Citation from restricted source` means a citation points outside the benchmark allowed document set.
