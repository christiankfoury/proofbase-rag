# Phase 9 Memory Evaluation Results

Generated at: 2026-06-05T02:45:56.243710+00:00

## Run Summary

- Memory benchmark questions: 5
- Retrieval mode: vector_only
- Chunking strategy: section_based
- Top K: 5
- Follow-up detection accuracy: 1.000
- Query rewrite quality: 1.000
- Memory answer accuracy: 1.000
- Memory citation accuracy: 1.000
- Memory response type accuracy: 1.000
- Memory permission leakage: 0.000
- Hallucination rate on follow-ups: 0.000
- Average final confidence: 0.777

## Question Results

| Question ID | Follow-up | Rewritten Question | Detection | Rewrite Quality | Answer Acc | Citation Acc | Response Type | Leakage |
|---|---|---|---:|---:|---:|---:|---:|---:|
| MEM-001 | Can I carry any unused days into next year? | Can employees carry unused vacation days into next year? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-002 | What if it is fewer than 15 business days? | For a temporary remote work location change, what happens if it is fewer than 15 business days? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-003 | Can I download restricted data to it? | Can an employee download restricted data to a personal device? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-004 | How long does it usually take? | What is the typical implementation range for standard deployments? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-005 | When does that happen? | When does the formal performance review cycle happen? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |

## Notes

- Memory is used only to rewrite/clarify the current query.
- Prior assistant answers are not treated as source evidence.
- Retrieval still applies current-role permission filtering before generation.
- Semantic rewrite quality is approximated by expected-source retrieval success.
