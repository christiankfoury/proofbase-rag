# Personas and Access Model

## Roles

The MVP uses five roles:

- Employee
- Sales Representative
- Manager
- HR Admin
- IT/Admin

## Document Categories

| Category | Examples | Default Visibility |
|---|---|---|
| HR Public | Employee handbook, PTO policy, benefits guide, remote work policy | Employee, Sales Representative, Manager, HR Admin, IT/Admin |
| IT Public | Acceptable use, MFA policy, device security, data classification | Employee, Sales Representative, Manager, HR Admin, IT/Admin |
| Sales Enablement | Sales playbooks, product FAQs, objection handling, approved battlecards | Sales Representative, Manager |
| Manager Only | Manager handbook, performance review guide, escalation process, team planning docs | Manager |
| HR Admin | HR process docs, policy maintenance docs, sensitive HR operations | HR Admin |
| IT Admin | Security standards, privileged access review, incident response summaries | IT/Admin |

## Persona Matrix

| Persona | Needs | Can Access | Cannot Access | Example Questions | Good Agent Behavior | Bad Agent Behavior |
|---|---|---|---|---|---|---|
| Employee | Clear answers about general policies and internal processes | Public HR policies, onboarding docs, benefits summaries, basic IT policies | Manager-only docs, sales strategy, HR admin records, security incident procedures | "How many vacation days do I get?" "What is the remote work policy?" | Answers only from accessible docs, cites policy sections, says when policy is unclear | Invents policy, cites inaccessible docs, gives manager-only details |
| Sales Representative | Fast access to sales collateral, product positioning, objections, and approved pricing guidance | Sales playbooks, public product docs, approved competitive battlecards | HR admin docs, manager compensation docs, restricted finance docs | "How do we position against Competitor A?" "What objections should I expect in healthcare?" | Uses approved sales docs, warns when information is outdated or missing | Reveals internal financial strategy or unsupported claims |
| Manager | Answers about team processes, performance guidance, escalation paths, and manager-only policies | Employee docs plus manager handbook, performance review process, team planning docs | HR admin private records, security admin docs, confidential legal docs | "How do I handle a performance improvement plan?" | Cites manager-only sources and refuses for non-manager users | Gives manager-only answers to employees |
| HR Admin | Policy maintenance, employee policy lookup, validation of HR source coverage | HR policies, benefits docs, HR process docs, manager policy docs | IT admin secrets, unrelated sales-only strategy unless granted | "Which policy covers parental leave?" "Which docs mention termination process?" | Identifies source documents and gaps; avoids giving legal advice beyond policy | Overstates legal compliance or exposes employee-specific data |
| IT/Admin | Security and system policy answers; access troubleshooting | IT policies, security standards, access control docs, incident response summaries | HR private records, sales strategy unless granted | "What is the MFA policy?" "How are privileged accounts reviewed?" | Gives controlled security guidance with citations; refuses sensitive operational details when restricted | Reveals incident procedures or secrets to unauthorized users |

## Permission Rules

- Retrieval must apply role filters before documents or chunks are sent to the LLM.
- The LLM must never receive unauthorized chunks as hidden context.
- A user may receive a refusal because the content is unavailable, unsupported, or outside their permissions.
- Refusals should not reveal restricted facts.
- Benchmarks must include explicit permission leakage tests for each restricted category.
