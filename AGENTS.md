# Project invariants

Build a consent-first identity-protection product.

Read docs/prd.md, docs/architecture.md, docs/threat-model.md,
and contracts/openapi.yaml before changing relevant modules.

## Non-negotiable constraints
- Never query an unverified or unauthorized identifier.
- Never expose another tenant's or subject's data.
- Never store leaked passwords, session cookies, or authentication tokens.
- Never log raw email, phone, PAN, Aadhaar, provider queries, or evidence.
- Never scrape government portals.
- Never bypass authentication, CAPTCHA, paywalls, or source restrictions.
- Never present mock intelligence as production data.
- Never claim universal Aadhaar, PAN, or dark-web coverage.
- Never enable an unapproved provider capability.
- Never run production migrations or destructive commands without approval.

## Engineering requirements
- Python business logic must be typed.
- Validate inputs and provider responses.
- Use explicit transactions.
- Use transactional outbox for durable asynchronous side effects.
- Consumers must tolerate duplicates and out-of-order delivery.
- Re-check authorization before provider calls, persistence, and alerts.
- Add tests with every behavior change.
- Keep API contracts synchronized with implementation.
- Record architectural deviations in docs/decisions.
- Do not weaken security tests to make a build pass.

## Completion evidence
For every task report:
1. Requirement IDs implemented.
2. Files changed.
3. Tests added.
4. Commands actually executed.
5. Results actually observed.
6. Remaining blockers.
7. Security and privacy impact.

Never claim tests passed unless they were executed.
Never claim production readiness while launch gates remain open.
