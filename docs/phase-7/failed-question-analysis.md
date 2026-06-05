# Phase 7 Failed Question Analysis

Generated at: 2026-06-05T01:50:38.486301+00:00

Failed questions: 13

| Question ID | Expected Behavior | Actual Response | Failure Type | Citation Confidence | Answer Confidence | Recommended Fix |
|---|---|---|---|---:|---:|---|
| FACT-008 | answer | answer | incomplete_answer | 0.863 | 0.863 | Improve answer completeness scoring or prompt the model to include all required expected-answer facts. |
| FACT-010 | answer | answer | incomplete_answer | 0.793 | 0.793 | Improve answer completeness scoring or prompt the model to include all required expected-answer facts. |
| FACT-012 | answer | not_found | answer_not_generated | 0.0 | 0.65 | Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved. |
| MULTI-001 | answer | not_found | answer_not_generated | 0.453 | 0.65 | Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved. |
| MULTI-003 | answer | partial_answer | unsupported_answer | 0.548 | 0.398 | Tighten answer prompt and lower confidence when citation validation is weak. |
| MULTI-004 | answer | partial_answer | wrong_citation | 0.573 | 0.573 | Improve citation formatting and require the model to cite the exact supporting chunk. |
| MULTI-005 | answer | partial_answer | multi_document_failure | 0.602 | 0.602 | Add query decomposition or multi-document retrieval logic. |
| MULTI-006 | answer | partial_answer | wrong_citation | 0.589 | 0.589 | Improve citation formatting and require the model to cite the exact supporting chunk. |
| MULTI-007 | answer | partial_answer | unsupported_answer | 0.554 | 0.404 | Tighten answer prompt and lower confidence when citation validation is weak. |
| MULTI-008 | answer | partial_answer | wrong_citation | 0.525 | 0.375 | Improve citation formatting and require the model to cite the exact supporting chunk. |
| MULTI-010 | answer | partial_answer | unsupported_answer | 0.55 | 0.4 | Tighten answer prompt and lower confidence when citation validation is weak. |
| MEM-003 | answer_with_memory | partial_answer | unsupported_answer | 0.688 | 0.538 | Tighten answer prompt and lower confidence when citation validation is weak. |
| MEM-004 | answer_with_memory | not_found | answer_not_generated | 0.346 | 0.65 | Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved. |

## Detailed Items

### FACT-008

- Question: Who must approve a regular work location change?
- Expected source document: ['HR-003']
- Actual citations: [{'document_id': 'HR-003', 'section_heading': 'Approval Requirements', 'confidence': 0.863}]
- Retrieval success: 1.0
- Failure type: incomplete_answer
- Recommended fix: Improve answer completeness scoring or prompt the model to include all required expected-answer facts.

### FACT-010

- Question: What is the annual wellness stipend amount?
- Expected source document: ['HR-004']
- Actual citations: [{'document_id': 'HR-004', 'section_heading': 'Wellness Stipend', 'confidence': 0.793}]
- Retrieval success: 1.0
- Failure type: incomplete_answer
- Recommended fix: Improve answer completeness scoring or prompt the model to include all required expected-answer facts.

### FACT-012

- Question: Are employees allowed to share passwords or MFA codes?
- Expected source document: ['IT-001']
- Actual citations: []
- Retrieval success: 1.0
- Failure type: answer_not_generated
- Recommended fix: Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved.

### MULTI-001

- Question: If I work remotely, what approval and device security expectations apply?
- Expected source document: ['HR-003', 'IT-002']
- Actual citations: [{'document_id': 'HR-003', 'section_heading': 'Approval Requirements', 'confidence': 0.417}, {'document_id': 'HR-003', 'section_heading': 'Security Expectations', 'confidence': 0.528}, {'document_id': 'IT-002', 'section_heading': 'Remote Work', 'confidence': 0.435}, {'document_id': 'IT-002', 'section_heading': 'Personal Devices', 'confidence': 0.481}, {'document_id': 'IT-002', 'section_heading': 'Company Devices', 'confidence': 0.405}]
- Retrieval success: 1.0
- Failure type: answer_not_generated
- Recommended fix: Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved.

### MULTI-003

- Question: Who should I contact for PTO questions and what is the basic vacation entitlement?
- Expected source document: ['HR-001', 'HR-002']
- Actual citations: [{'document_id': 'HR-002', 'section_heading': 'Vacation Entitlement', 'confidence': 0.787}, {'document_id': 'HR-001', 'section_heading': 'Employee Support Channels', 'confidence': 0.309}]
- Retrieval success: 1.0
- Failure type: unsupported_answer
- Recommended fix: Tighten answer prompt and lower confidence when citation validation is weak.

### MULTI-004

- Question: How should I position Northstar against BI tools while avoiding prohibited claims?
- Expected source document: ['SALES-002', 'SALES-003']
- Actual citations: [{'document_id': 'SALES-003', 'section_heading': 'Positioning Against Generic BI Tools', 'confidence': 0.632}, {'document_id': 'SALES-003', 'section_heading': 'Prohibited Claims', 'confidence': 0.513}]
- Retrieval success: 1.0
- Failure type: wrong_citation
- Recommended fix: Improve citation formatting and require the model to cite the exact supporting chunk.

### MULTI-005

- Question: Before a deal moves to proposal, what sales-stage and implementation constraints should I check?
- Expected source document: ['SALES-001', 'SALES-002']
- Actual citations: [{'document_id': 'SALES-001', 'section_heading': 'Sales Stages', 'confidence': 0.53}, {'document_id': 'SALES-001', 'section_heading': 'Handoff Rules', 'confidence': 0.674}]
- Retrieval success: 0.0
- Failure type: multi_document_failure
- Recommended fix: Add query decomposition or multi-document retrieval logic.

### MULTI-006

- Question: How should a manager handle ongoing performance concerns?
- Expected source document: ['MGR-001', 'MGR-002']
- Actual citations: [{'document_id': 'MGR-002', 'section_heading': 'Performance Improvement Process', 'confidence': 0.657}, {'document_id': 'MGR-002', 'section_heading': 'Performance Documentation', 'confidence': 0.52}]
- Retrieval success: 1.0
- Failure type: wrong_citation
- Recommended fix: Improve citation formatting and require the model to cite the exact supporting chunk.

### MULTI-007

- Question: If I use a personal device for remote work, what are the remote-work and device rules?
- Expected source document: ['HR-003', 'IT-002']
- Actual citations: [{'document_id': 'IT-002', 'section_heading': 'Personal Devices', 'confidence': 0.608}, {'document_id': 'IT-002', 'section_heading': 'Remote Work', 'confidence': 0.496}, {'document_id': 'HR-003', 'section_heading': 'Security Expectations', 'confidence': 0.559}]
- Retrieval success: 1.0
- Failure type: unsupported_answer
- Recommended fix: Tighten answer prompt and lower confidence when citation validation is weak.

### MULTI-008

- Question: What should I do if I need benefits help and also want to use my learning budget?
- Expected source document: ['HR-001', 'HR-004']
- Actual citations: [{'document_id': 'HR-004', 'section_heading': 'Benefits Support', 'confidence': 0.498}, {'document_id': 'HR-004', 'section_heading': 'Learning Budget', 'confidence': 0.552}]
- Retrieval success: 1.0
- Failure type: wrong_citation
- Recommended fix: Improve citation formatting and require the model to cite the exact supporting chunk.

### MULTI-010

- Question: How should HR handle a cross-border remote work exception?
- Expected source document: ['HR-003', 'HR-ADMIN-001']
- Actual citations: [{'document_id': 'HR-ADMIN-001', 'section_heading': 'Escalation Paths', 'confidence': 0.48}, {'document_id': 'HR-003', 'section_heading': 'Cross-Border Work', 'confidence': 0.619}, {'document_id': 'HR-003', 'section_heading': 'Approval Requirements', 'confidence': 0.552}]
- Retrieval success: 1.0
- Failure type: unsupported_answer
- Recommended fix: Tighten answer prompt and lower confidence when citation validation is weak.

### MEM-003

- Question: Can I download restricted data to it?
- Expected source document: ['IT-002']
- Actual citations: [{'document_id': 'IT-002', 'section_heading': 'Personal Devices', 'confidence': 0.909}, {'document_id': 'IT-003', 'section_heading': 'Storage Rules', 'confidence': 0.466}]
- Retrieval success: 1.0
- Failure type: unsupported_answer
- Recommended fix: Tighten answer prompt and lower confidence when citation validation is weak.

### MEM-004

- Question: How long does it usually take?
- Expected source document: ['SALES-002']
- Actual citations: [{'document_id': 'SALES-002', 'section_heading': 'Industry Use Cases', 'confidence': 0.276}, {'document_id': 'SALES-001', 'section_heading': 'Approved Talk Track', 'confidence': 0.416}]
- Retrieval success: 1.0
- Failure type: answer_not_generated
- Recommended fix: Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved.
