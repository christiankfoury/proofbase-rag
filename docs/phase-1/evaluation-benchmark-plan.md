# Evaluation and Benchmark Plan

## Strategy

The benchmark must exist before the chatbot implementation. It defines what "better" means and prevents the project from becoming a subjective demo.

The first benchmark should contain 60 questions. This is large enough to cover enterprise behaviors without becoming too heavy for a solo developer.

## Benchmark Distribution

| Category | Count | Purpose |
|---|---:|---|
| HR policy | 15 | Tests common employee policy answers and citation grounding |
| IT/security policy | 10 | Tests controlled answers around security and acceptable use |
| Sales knowledge | 10 | Tests sales enablement retrieval and approved positioning |
| Manager-only | 10 | Tests role-specific access and sensitive management content |
| Permission/refusal | 10 | Tests unauthorized access and no-answer behavior |
| Missing or ambiguous information | 5 | Tests refusal and uncertainty handling |

## Benchmark Item Schema

Each benchmark item should include:

- `id`
- `category`
- `user_role`
- `question`
- `expected_behavior`
- `expected_answer_summary`
- `gold_document_ids`
- `gold_chunk_ids`
- `required_citation_ids`
- `should_refuse`
- `refusal_reason`
- `permission_sensitive`
- `evaluation_tags`

## Example Benchmark Items

| ID | Category | Role | Question | Expected Behavior | Gold Source |
|---|---|---|---|---|---|
| HR-001 | HR policy | Employee | How many vacation days do full-time employees get? | Answer with PTO policy citation | PTO policy |
| HR-002 | HR policy | Employee | Can I work remotely from another province? | Answer with remote work policy citation or state approval requirements | Remote work policy |
| IT-001 | IT/security | Employee | Can I use my personal laptop for company work? | Answer with device security policy citation | Device security policy |
| SALES-001 | Sales | Sales Representative | How should I respond to price objections? | Answer from sales playbook with citation | Sales objection playbook |
| MGR-001 | Manager-only | Manager | How should I document performance issues? | Answer with manager handbook citation | Manager handbook |
| PERM-001 | Permission/refusal | Employee | What is the promotion calibration process? | Refuse because manager-only content is not accessible | Manager handbook |
| NOANS-001 | Missing info | Employee | What is the company's policy for sabbaticals? | Refuse or state no policy found | None |

## How Evaluation Guides Development

- If hit rate is low, improve chunking, metadata, search, or hybrid retrieval.
- If precision is low, improve filters, ranking, or query rewriting.
- If answer accuracy is low but retrieval is good, improve prompting and answer constraints.
- If citation accuracy is low, improve citation extraction and validation.
- If permission tests fail, fix authorization before adding features.
- If latency or cost is high, reduce context size or optimize retrieval.

## Recruiter Demo Angle

The benchmark gives the project a clear story:

1. Define realistic enterprise questions.
2. Run baseline RAG.
3. Identify failures in retrieval, citations, refusals, latency, or cost.
4. Improve retrieval and prompts.
5. Show measurable gains in an evaluation dashboard.
