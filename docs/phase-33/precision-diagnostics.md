# Phase 33 Precision Diagnostics

Generated at: 2026-06-21T01:18:21.341757+00:00

## Scope

- Input run: `phase32-expanded-retrieval`.
- Input artifact: `data/evaluation/expanded-baseline/phase32-expanded-retrieval.json`.
- Method: local replay of the saved Phase 32 retrieved chunk order with smaller top-k cuts.
- Network/API use: none.
- This is diagnostic evidence only; it does not prove a live retrieval improvement.

## Top-K Replay

| Top K | Precision@k | Source Recall | All-Sources Hit | MRR | Failed Source Questions | Precision Target | Recall Gate | MRR Gate |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 0.922 | 0.804 | 0.689 | 0.922 | 28 | pass | fail | fail |
| 2 | 0.778 | 0.935 | 0.889 | 0.950 | 10 | pass | fail | pass |
| 3 | 0.700 | 0.967 | 0.944 | 0.954 | 5 | fail | pass | pass |
| 4 | 0.647 | 0.972 | 0.956 | 0.954 | 4 | fail | pass | pass |
| 5 | 0.616 | 0.978 | 0.967 | 0.954 | 3 | fail | pass | pass |

## Saved Top-5 Lexical Rerank Replay

This replay applies the Phase 33 lexical reranker to the saved top-5 chunks from Phase 32. It cannot evaluate chunks outside that saved top-5 pool.

| Top K | Precision@k | Source Recall | All-Sources Hit | MRR | Failed Source Questions | Precision Target | Recall Gate | MRR Gate |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 0.944 | 0.826 | 0.711 | 0.944 | 26 | pass | fail | fail |
| 2 | 0.800 | 0.913 | 0.856 | 0.956 | 13 | pass | fail | pass |
| 3 | 0.730 | 0.950 | 0.922 | 0.959 | 7 | fail | pass | pass |
| 4 | 0.686 | 0.950 | 0.922 | 0.959 | 7 | fail | pass | pass |
| 5 | 0.616 | 0.978 | 0.967 | 0.961 | 3 | fail | pass | pass |

## Findings

- Highest replayed precision is top-1 at `0.922`, but recall is `0.804`.
- Best replayed cut that keeps recall and MRR gates is top-3 with Precision@k `0.700`.
- Saved top-5 lexical rerank replay reaches Precision@k `0.730` at top-3 with recall `0.950`.
- A top-k-only change does not meet all Phase 33 targets. The next implementation step needs a ranking or filtering change verified by a live retrieval run.
- Permission leakage is not measured by this replay; Phase 33 completion still requires the permission safety check or an equivalent live safety run.

## Failed Questions At Best Gated Cut

MULTI-004, MULTI-005, MULTI-008, MEM-004, MULTI-012
