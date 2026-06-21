# Phase 33 Precision Diagnostics

Generated at: 2026-06-21T01:53:55.398751+00:00

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
Reranker config: vector weight `1.0`, lexical weight `0.04`, same-document boost `0.03`.

| Top K | Precision@k | Source Recall | All-Sources Hit | MRR | Failed Source Questions | Precision Target | Recall Gate | MRR Gate |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 0.956 | 0.837 | 0.722 | 0.956 | 25 | pass | fail | pass |
| 2 | 0.828 | 0.907 | 0.844 | 0.961 | 14 | pass | fail | pass |
| 3 | 0.774 | 0.950 | 0.922 | 0.965 | 7 | pass | pass | pass |
| 4 | 0.706 | 0.961 | 0.944 | 0.965 | 5 | fail | pass | pass |
| 5 | 0.616 | 0.978 | 0.967 | 0.967 | 3 | fail | pass | pass |

## Findings

- Highest replayed precision is top-1 at `0.922`, but recall is `0.804`.
- Best replayed cut that keeps recall and MRR gates is top-3 with Precision@k `0.700`.
- Saved top-5 lexical rerank replay reaches Precision@k `0.774` at top-3 with recall `0.950`.
- The saved-artifact replay now clears the Phase 33 retrieval gates, but it is not a live retrieval result.
- The next implementation step still needs a live retrieval run and full permission safety verification before promotion.
- Permission leakage is not measured by this replay; Phase 33 completion still requires the permission safety check or an equivalent live safety run.

## Failed Questions At Best Gated Cut

MULTI-004, MULTI-005, MULTI-008, MEM-004, MULTI-012
