# Phase 62 Internal Security Prechecks

Status: local internal prechecks, not an independent assessment.

## Completed locally

| Area | Method | Result |
| --- | --- | --- |
| targeted static analysis | Python AST scan for builtin `eval`/`exec`, unsafe pickle/YAML loads, and `shell=True` | passed; Redis server-side `EVAL` is not Python code execution |
| source/build/image secret scan | Phase 60 high-confidence repository/build-context scanner plus Python and minimal-image filesystem paths | passed for the repository and rebuilt API/web images |
| authorization | Phase 56 identity, Phase 57 filter-free RLS/mutation, API admin denial | passed |
| tenant isolation | direct runtime-role and tenant-pair suites | passed |
| local DAST smoke | TestClient health, response headers, admin denial, bounded validation/no echo | passed |
| adversarial controls | Phase 52 request, Phase 53 evidence, Phase 54 validator, Phase 55 hard-gate suites | passed against visible development evidence; sealed holdouts were not executed |
| container configuration | Compose parse, local image build, Dockerfile assertion, and image config inspection | rebuilt API=`proofbase`, web=`node`; root-runtime finding remediated |
| dependency inventory | npm lockfile v3 and Python requirement inventory | web reproducible; Python packages are not fully pinned |

## Findings

| ID | Severity | Status | Finding / disposition |
| --- | --- | --- | --- |
| P62-CONTAINER-001 | High | verified closed | API and web runtime images previously defaulted to root. Dedicated `proofbase`/`node` users were added; both images rebuilt and their configured users were inspected. |
| P62-HEADERS-001 | Medium | remediated, retest passed | API responses lacked an explicit local baseline for cache, content type, framing, referrer, permissions, and CSP headers. |
| P62-DEPENDENCY-001 | Medium | open | Python requirements are ranges/unpinned. Pinning plus an update policy is required before a reproducible production build claim. |
| P62-CVE-001 | Medium | open | No current Python/npm vulnerability-database scan was run; installed tools do not include `pip-audit`, Bandit, Semgrep, Trivy, or Grype and this phase does not install/connect them. |
| P62-IMAGE-001 | Medium | open | No current container CVE/SBOM/signature scanner is available. Phase 60 verifies secret absence, not package vulnerability status. |
| P62-DAST-001 | Medium | open | Local TestClient negative tests are not a network/proxy/TLS/browser DAST assessment. |
| P62-EXTERNAL-001 | Informational | external gate | Hosted OIDC, storage/scanner/worker, managed secrets, SIEM/paging, and Azure remain unconnected and unclaimed. |

There are no unresolved internally identified critical/high findings after the non-root image remediation. This is not evidence that an independent assessor will find none.
