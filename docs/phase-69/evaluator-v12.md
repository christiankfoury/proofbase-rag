# Evaluator v12 prepared; budget gate blocked

V11 completed 20/24 exact challenges and 3/3 exact audit probes, still failed.
V12 is prepared locally, not executed. No original expectations or reducers change.

The claim stage now receives question/history only to resolve conversational
references. It still receives no required facts, expected behavior or response
metadata, and source evidence remains mandatory for factual and cited support.
Prompts require contiguous verbatim answer spans and discourage reconstructing
atomic sentences by adding subjects/punctuation. Review explicitly equates missing
cited support with the citation-support failure dimension.

This candidate uses full `gpt-5.4-2026-03-05`, medium reasoning, 4096 completion
tokens per call including reasoning. Prices checked 2026-09-19 at
https://developers.openai.com/api/docs/models/gpt-5.4 : USD 2.50/M input and
USD 15.00/M output. No cache discount assumed. Raw requests/responses and all
prior model rates are retained for replay; complete v11 ledger prefix is protected.

Current conservative cumulative spend is USD 2.13692667 under approved USD 5.
Available: USD 2.86307333. Full 75-call v12 reservation: **USD 7.72026250**.
It exceeds current headroom by USD 4.85718917; required cumulative capacity is
USD 9.85718917. Proposed ceiling USD 10 is a USD 5 increase, including all prior
spend. This is a worst-case token reservation, not a quoted expected charge.
The code and ledger still enforce USD 5; no extra authorization has been assumed.

Eight local tests pass, including full attempt refusal without writes or calls
when headroom is insufficient, mixed-history preservation, reasoning-token cost,
and context/gold separation. The next action requires explicit approval under
[the handoff cost constraints](../roadmap/post-phase-68-quality-remediation-handoff.md#cost-and-safety-constraints).
Subsequent confirmation, development and holdout stages still require their own
preflights. No generalization, application-quality or human-adjudication claim.
