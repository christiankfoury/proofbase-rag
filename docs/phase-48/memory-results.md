# Phase 9 Memory Evaluation Results

Generated at: 2026-08-23T22:17:48.451690+00:00

## Run Summary

- Memory benchmark questions: 20
- Retrieval mode: vector_lexical_rerank
- Chunking strategy: section_based
- Top K: 5
- Follow-up detection accuracy: 1.000
- Query rewrite quality: 1.000
- Memory answer accuracy: 1.000
- Memory citation accuracy: 1.000
- Memory response type accuracy: 1.000
- Memory permission leakage: 0.000
- Hallucination rate on follow-ups: 0.000
- Average final confidence: 0.852
- Input tokens: 25073
- Output tokens: 4959
- Estimated cost: 0.017963

## Question Results

| Question ID | Follow-up | Rewritten Question | Detection | Rewrite Quality | Answer Acc | Citation Acc | Response Type | Leakage |
|---|---|---|---:|---:|---:|---:|---:|---:|
| MEM-001 | Can I carry any unused days into next year? | Can I carry any unused days into next year? Context: PTO and Leave Policy. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-002 | What if it is fewer than 15 business days? | What if it is fewer than 15 business days? Context: Remote and Hybrid Work Policy. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-003 | Can I download restricted data to it? | Can I download restricted data to it? Context: Device and BYOD Security Policy. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-004 | How long does it usually take? | How long does it usually take? Context: Product Positioning and FAQ. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-005 | When does that happen? | When does the formal performance review cycle happen? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-006 | Can I paste confidential data into them? | Can I paste confidential data into them? Context: acceptable use. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-007 | What types of data does it include? | What types of data does it include? Context: I am asking about the Confidential data classification level.. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-008 | What needs to be done before reaching it? | What needs to be done before reaching it? Context: I am asking about the proposal stage in the sales process.. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-009 | How often should they happen? | How often should they happen? Context: I am asking about one-on-one meeting expectations for managers.. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-010 | Does it roll over at the end of the year? | Does it roll over at the end of the year? Context: I am asking about the wellness stipend.. | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-011 | Does it need a receipt? | Do expenses above USD 25 require a receipt? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-012 | When will it be reimbursed? | When are approved expense reports reimbursed if submitted at least five business days before payroll close? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-013 | How far ahead should I book it? | How far ahead should employees book business travel? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-014 | How long do we keep them after expiration? | How long are customer contracts retained after expiration? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-015 | Can it happen on Friday? | Can production deployments happen on Friday? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-016 | How often are updates required for that tier? | How often are status updates required for Enterprise support customers? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-017 | Who starts it? | Who initiates new-hire equipment? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-018 | Can I send ours after confirming the entity name? | Can Sales send Northstar's standard mutual NDA after confirming the recipient legal entity name? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-019 | What fields must it return? | What fields must public API endpoint error shapes return? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-020 | Who approves it above that limit? | Who approves office supplies purchases above the standard limit? | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |

## Notes

- Memory is used only to rewrite/clarify the current query.
- Prior assistant answers are not treated as source evidence.
- Retrieval still applies current-role permission filtering before generation.
- Semantic rewrite quality is approximated by expected-source retrieval success.
