# Phase 59 Decision Record

## Approved local portfolio policy

- Accepted format: PDF only.
- Limits: 10 MB per file, 100 pages, 2,000,000 extracted characters, a 200:1 extracted-size ceiling, and a 15-second local parser timeout.
- Data: synthetic or non-sensitive business content only. Real personal data, regulated data, PHI, PCI data, government identifiers, credentials, secrets, and equivalent sensitive content are not accepted.
- Retention: rejected and unapproved originals expire after 7 days; approved originals expire after 30 days; approved extracted content remains until tenant archive/delete. Legal hold overrides deletion and expiry.

These decisions apply to the local portfolio workflow. They do not approve Azure resources, object storage, hosted malware scanning, paid services, premium licences, or Marketplace purchases.

## Deferred external decisions

Production object storage, encryption-key ownership, a hosted malware scanner, and the connected isolated-worker runtime remain external-integration decisions behind the financial-safety gate. No provider has been selected or connected.
