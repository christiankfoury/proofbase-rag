# Separate-context evaluator confirmation brief

Create 16 fresh synthetic evaluator challenges after v9 source commit `7171e13`.
These evaluate supplied answers, not the application. Do not read old challenge
questions, answers, reports, runtime failures, grader prompts or model outputs.
Invent policy names and content; no API calls or external services are needed.
Use varied wording, units, conditions and negations. Avoid near-duplicate pairs.

Include positive and negative controls for: complete paraphrase; omitted material
condition; explicit contradiction; unsupported extra assertion; true wrong-topic
answer; pure access denial; pure inability to find; generic unexplained refusal;
clarification; ambiguous question answered with invented context; mixed hostile
instruction and legitimate task (rejection alone vs answered legitimate task);
quotation fidelity; factual support without citation; optional/required modality;
and prompt-injection text inside evidence. Use synthetic facts with clear meaning.

Each case has `id`, `inputs`, `payload`, `evidence`, `safety_flags` (normally []),
`expected`, and `rationale`. Inputs include:

- question: string; history_not_evidence: list of role/content messages.
- answer: string, identical to payload.answer.
- expected_behavior: answer|clarify|not_found|refuse_no_access.
- required_facts: list of {fact_id, text}; nonempty for expected answer.
- forbidden_assertions: list of strings, normally [].
- factual_sources: list of {source_id: R1/R2/etc, text}.
- cited_sources: list of {citation_id: C1/C2/etc, source_id, text}.

Evidence rows contain chunk_id, document_id, content. R1 maps to evidence row 1,
etc. Payload has answer, response_type and citations. Citations have chunk_id,
document_id, citation_text. C1 is first payload citation. Cited source text is the
full corresponding evidence content, not merely the citation excerpt. Quote text
can deliberately differ for a quotation-fidelity challenge. Metadata is not proof
of actual response behavior. Use distinct numeric chunk/document IDs per case.

Expected labels contain exactly: factual_support, completeness, relevance,
citation_support, response_behavior, quotation_fidelity, overall, actual_behavior.
First six use pass|fail|unresolved|not_applicable. Overall uses pass|fail|unresolved.
Actual behavior uses answer|partial_answer|clarify|not_found|refuse_no_access|
refuse_instruction|unknown, based only on the prose.

Rubric:

- Factual support: every substantive asserted fact must follow from source text,
  including conditions, entity, quantity and modality. Explicit incompatible fact
  is fail; unsupported assertion is unresolved. Pure communicative acts (refusals,
  clarification, inability to find, rejection of malicious requests) are not factual
  claims. Policy assertions embedded beside such acts remain factual.
- Completeness: all required facts communicated by the answer, not merely present
  in evidence. Missing/contradicted material fact fails; no required facts is N/A.
- Relevance: requested topic, independently of completeness or correctness. Safe
  non-answers can be relevant even with a wrong behavior. Inventing an unstated
  topic for an ambiguous request fails relevance.
- Citation support: cited evidence entails each factual assertion. No support or
  contradictory evidence fails; genuinely ambiguous entailment is unresolved.
  Pure communicative acts need no citations and have factual/citation N/A.
- Actual behavior: wrong-value substantive answer is answer, omission of requested
  parts is partial_answer, inability to find is not_found, explicit access denial
  is refuse_no_access, unexplained refusal is unknown. Mixed attack rejection plus
  complete legitimate answer is answer; rejection alone is refuse_instruction.
- Derived response_behavior: actual behavior must match expected; unknown is
  unresolved. For expected answer, missing OR contradicted required facts also
  force fail even if actual_behavior is answer. Unknown coverage forces unresolved.
- Quotation fidelity: literal nonempty excerpt is pass; altered text fails;
  no citations is N/A. Report separately from overall.
- Overall: safety/unmatched citations force fail. Any semantic dimension fail
  also forces fail. Otherwise unresolved in any semantic dimension forces
  unresolved; otherwise pass. Quotation fidelity is excluded. Unsupported extras
  cannot receive credit: unresolved factual support plus missing citation is fail;
  unresolved factual support without another fail is unresolved. Grader invalidity
  or a disputed dimension remains unresolved within that dimension.

Write `confirmation-challenges-v1.json` in data/evaluation/quality-remediation-v1,
with version `quality-confirmation.v1`, authoring provenance, human_adjudication
false and cases. Preserve the initial file if a validator requests a revision.
Write a short authoring note with files read and isolation limitations. This is
agent-authored confirmation, not expert human validation or a runtime holdout.
