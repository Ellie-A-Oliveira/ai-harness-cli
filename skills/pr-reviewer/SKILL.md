---
name: pr-reviewer
description: Review pull requests across the registered repositories using the harness architecture, project context, code patterns, security requirements, and Atlassian story context; produce evidence-based findings without modifying code by default.
---

# Pull request reviewer

Use this skill when the user asks for a PR review, change review, diff review, or implementation validation for the event-commerce platform or another repository registered with the harness.

## Review setup

Every review session must use the harness CLI:

1. Run `harness doctor` and `harness index`.
2. Use `harness ask` to retrieve architecture, code patterns, project context, security requirements, and story-delivery rules.
3. Identify the Jira issue key from the PR title, branch, description, or linked issue. If present, retrieve the issue through the connected Atlassian workflow. Do not invent missing requirements.
4. Inspect the complete diff, surrounding code, tests, and relevant contracts in every affected repository.
5. Run `harness security check-command "<command>"` before any command and respect the policy classification.

For a GitHub PR, use the connected GitHub tools when available. For local review, use the repository's current diff and branch metadata. Review is read-only by default: do not edit files, post comments, approve, merge, push, or change Jira/Confluence.

## Review priorities

Review in this order:

1. Correctness and data integrity: broken behavior, incorrect state transitions, race conditions, error handling, and backward incompatibility.
2. Architecture ownership: order orchestration remains in `order-service`; inventory owns reservations; product owns catalog data; `event-contracts` owns compatibility; gateway concerns remain at the edge.
3. Event and API contracts: preserve `eventId`, `occurredAt`, and `correlationId`; check additive compatibility, idempotency, retries, compensation, validation, and HTTP semantics.
4. Reliability and operations: persistence boundaries, transaction behavior, outbox/inbox needs, RabbitMQ behavior, timeouts, observability, rollback, migrations, and failure recovery.
5. Security and privacy: secrets, unsafe inputs, authorization gaps, excessive permissions, credential leakage, unsafe shell commands, dependency risk, and sensitive data in logs or snapshots.
6. Tests and delivery: tests cover acceptance criteria and failure paths; contract changes have contract tests; generated artifacts and unrelated changes are absent; the branch and commit messages follow repository rules.

## Required project grounding

Read the relevant knowledge before deciding whether something is a finding:

- [architecture.md](../../knowledge/architecture.md): system boundaries and current implementation gaps.
- [code-patterns.md](../../knowledge/code-patterns.md): API, event, and prototype conventions.
- [project-context.md](../../knowledge/project-context.md): EC project identity and grounding limits.
- [security-requirements.md](../../knowledge/security-requirements.md): command, credential, external-system, and change controls.
- [story-delivery-rules.md](../../knowledge/story-delivery-rules.md): Jira key, branch, approval, and delivery rules.

If repository code contradicts the local knowledge, report the discrepancy and identify which source is newer or authoritative. If a Jira/Confluence decision contradicts local inference, prefer the explicit remote decision and cite it.

## Findings standard

Report only actionable findings supported by the diff and surrounding evidence. Each finding must include:

- Severity: `P0` blocker, `P1` high-risk correctness/security issue, `P2` normal defect or material maintainability issue, or `P3` minor improvement.
- Exact file and line or tight line range.
- What is wrong and why it matters in this architecture.
- A concrete remediation direction.
- Evidence: test, contract, knowledge file, or Jira/Confluence source.

Prioritize findings over praise. Do not report style preferences unless they violate a documented repository pattern or create risk. Do not report speculative issues without a plausible failure path.

## Review output

Use this structure:

```markdown
# PR review

Verdict: approve | request changes | blocked pending clarification

## Findings

### [P1] Short title

- Location: `repo/path/file.ext:line`
- Problem: ...
- Impact: ...
- Recommendation: ...
- Evidence: ...

## Coverage and open questions

- Reviewed repositories/files: ...
- Tests run: ...
- Missing evidence or unresolved questions: ...
```

If there are no actionable findings, say so explicitly and list what was checked. If the PR changes multiple repositories, give a separate coverage note for each repository and verify the shared branch name and Jira key.

## External review actions

Do not post GitHub review comments or approve/merge automatically. If the user explicitly requests inline comments, use the available GitHub review capability or the `::code-comment{...}` format for local files, preserving the finding severity and exact location. Never turn a review request into an implementation change without a separate user request.
