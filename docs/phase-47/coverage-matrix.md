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

Holdout cells remain pending until independently authored and validated after the runtime freeze.

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
