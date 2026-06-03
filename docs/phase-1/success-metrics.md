# Success Metrics

The project should show measurable improvement across versions. Use placeholders like X% to Y% until real benchmark runs produce actual values.

## Retrieval Metrics

| Metric | What It Measures | Why It Matters | How To Calculate | Good Result |
|---|---|---|---|---|
| Retrieval hit rate | Whether the expected source appears in top-k | Proves the system can find the right evidence | `% benchmark questions where gold doc appears in top-k` | Improve from X% to Y% |
| Precision@k | How many retrieved chunks are relevant | Reduces noisy context | `relevant retrieved chunks / k` | Higher than baseline by X-Y percentage points |
| Recall@k | Whether enough relevant evidence is retrieved | Important for complete answers | `retrieved relevant chunks / total gold relevant chunks` | Improve across versions |
| MRR | Rank of first correct source | Measures search usefulness | `average reciprocal rank of first gold source` | Correct source moves closer to rank 1 |

## Answer Quality Metrics

| Metric | What It Measures | Why It Matters | How To Calculate | Good Result |
|---|---|---|---|---|
| Answer accuracy | Whether final answer is factually correct | Main user trust metric | Human or LLM-judge rubric against gold answer | Improve from X% to Y% |
| Faithfulness | Whether answer is supported by retrieved context | Detects hallucination | Judge each claim against cited sources | High faithfulness, improving by version |
| Hallucination rate | Unsupported claims in final answer | Core enterprise risk | `% answers with unsupported material claims` | Decrease from X% to Y% |
| Citation accuracy | Whether citations support the answer | Makes answers auditable | `% citations that contain the stated fact` | Improve from X% to Y% |
| Citation coverage | Whether key claims have citations | Prevents uncited policy claims | `% key claims linked to source chunks` | High coverage for policy answers |

## Permission and Security Metrics

| Metric | What It Measures | Why It Matters | How To Calculate | Good Result |
|---|---|---|---|---|
| Refusal accuracy | Correct refusal when answer is unavailable or unauthorized | Prevents unsafe answers | `% restricted or unanswerable questions refused correctly` | Improve from X% to Y% |
| Permission leakage rate | Unauthorized restricted information exposure | Critical enterprise trust metric | `% unauthorized test cases that reveal restricted content` | Trend toward 0% |
| Role filter correctness | Whether retrieval respects user permissions | Prevents hidden context leaks | Compare retrieved docs against role visibility metadata | 0 unauthorized docs retrieved |

## System Performance Metrics

| Metric | What It Measures | Why It Matters | How To Calculate | Good Result |
|---|---|---|---|---|
| Latency | Time from question to answer | Affects usability | Track p50 and p95 response time | p50/p95 improve or stay acceptable |
| Cost per answer | OpenAI and infrastructure cost per response | Production readiness | Sum token and retrieval cost per request | Stable or reduced across versions |
| Token usage | Prompt, completion, and context size | Helps optimize retrieval | Log tokens per answer | Lower tokens without quality loss |

## Product and User Feedback Metrics

| Metric | What It Measures | Why It Matters | How To Calculate | Good Result |
|---|---|---|---|---|
| Feedback score | User rating of helpfulness | Human usefulness signal | 1-5 rating or thumbs up/down | Improve from X to Y |
| Answer accepted rate | Whether user finds answer sufficient | Demo-friendly value metric | `% answers marked accepted` | Improve across benchmark/demo runs |
| Escalation rate | How often assistant cannot answer | Measures coverage gaps | `% responses that refuse or ask user to contact a team` | Appropriate, not artificially low |
