# Synthetic Document Writing Guidelines

## RAG-Friendly Structure

Write every synthetic document for retrieval and citation quality:

- Use clear headings and subheadings.
- Keep paragraphs focused on one policy point.
- Include concrete policy facts, limits, roles, and exceptions.
- Repeat key terms naturally, such as "remote work," "BYOD," "PTO," "manager approval," and "promotion calibration."
- Avoid long sections that mix unrelated topics.
- Include realistic ambiguity where useful, but label it clearly.
- Include overlapping information across documents so multi-document retrieval can be tested.
- Use consistent terminology across documents.
- Include document version and effective date in metadata.
- Avoid real names, real customer data, real security procedures, real confidential material, passwords, secrets, and exact pricing tables.

## Recommended Length

| Document Type | Target Length |
|---|---:|
| Public HR/IT documents | 700-1,200 words each |
| Sales documents | 800-1,300 words each |
| Manager/admin restricted documents | 700-1,100 words each |

For the first draft, shorter documents are acceptable if they contain enough concrete facts for benchmark design. Later phases can expand them before ingestion.

## Quality Checks

Each document should support at least:

- Three factual questions.
- One citation validation question.
- One refusal or ambiguity case if appropriate.

The full corpus should support:

- Multi-document questions across HR and IT.
- Multi-document questions across sales and product positioning.
- Permission-restricted questions for sales, manager, HR admin, and IT admin content.
- Missing-information questions for topics intentionally absent from the corpus.

## Citation Design

Prefer sections that can be cited directly:

- `## Eligibility`
- `## Approval Workflow`
- `## Data Classification Levels`
- `## Manager Responsibilities`

Avoid burying key facts in dense paragraphs. A good citation should make it obvious why the answer is supported.
