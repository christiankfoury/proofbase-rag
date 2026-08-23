# Phase 47 Coverage Matrix

## Locked Category Distribution

| Category | Development | Holdout | Total |
| --- | ---: | ---: | ---: |
| Factual robustness | 11 | 4 | 15 |
| Multi-document claim coverage | 10 | 5 | 15 |
| Multi-turn memory | 10 | 5 | 15 |
| Ambiguity boundaries | 7 | 3 | 10 |
| Permission and scope | 10 | 5 | 15 |
| Missing information and abstention | 7 | 3 | 10 |
| Prompt injection and adversarial behavior | 7 | 3 | 10 |
| Conflicting or versioned sources | 4 | 1 | 5 |
| Uploaded-document and project isolation | 4 | 1 | 5 |
| **Total** | **70** | **30** | **100** |

The holdout was independently authored after runtime commit `50e149c` and independently reviewed before hashing. Its SHA-256 is `10d93cfb229813499721a973ceadabd9045c47b2e5eee29e4dca0ee01b1afb4f`.

## Development Coverage

| Dimension | Counts |
| --- | --- |
| Roles | Employee 22; Sales Representative 16; Manager 19; HR Admin 4; IT Admin 9 |
| Difficulty | Easy 11; medium 36; hard 23 |
| Expected behavior | Answer 48; clarify 7; not found 9; refuse no access 6 |
| Permission parity | Five materially equivalent authorized/blocked pairs |
| Static corpus | All 19 synthetic document IDs represented |
| Fixture-backed | Four cases covering pending review, approved retrieval, strict department scope, and cross-project isolation |
| Stability slice | 20 cases: five multi-document, five memory, five permission, three adversarial, two uploaded/project-isolation |

The role distribution is intentionally not uniform because document access is role-dependent. Coverage checks ensure all five roles and all required behaviors appear without inventing permissions that do not exist.

## Holdout Coverage

| Dimension | Counts |
| --- | --- |
| Roles | Employee 11; Sales Representative 6; Manager 6; HR Admin 4; IT Admin 3 |
| Difficulty | Easy 2; medium 10; hard 18 |
| Expected behavior | Answer 19; clarify 4; not found 3; refuse no access 4 |
| Scope | Global 4; project 6; strict department 20 |
| Expected source count | Zero 4; one 20; two 2; three 2; four 2 |
| Conversation depth | Zero turns 25; two 1; four 2; six 1; eight 1 |
| Permission coverage | Two exact-intent authorized/blocked pairs plus one explicit restricted-source expectation |
| Static corpus | All 19 synthetic document IDs represented |
| Fixture-backed | One cross-project membership boundary case |

The holdout is intentionally hard-skewed and contains only two easy cases. It has one fixture-backed project-isolation case, so it does not establish broad uploaded-document or production multi-tenant reliability.
