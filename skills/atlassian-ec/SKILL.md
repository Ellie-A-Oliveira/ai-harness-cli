---
name: atlassian-ec
description: Connect an agent to the user's Atlassian E-commerce project (EC), retrieve Jira and Confluence context, and keep local harness knowledge grounded in the event-commerce-platform repository.
---

# Atlassian EC project skill

## Mandatory harness usage

Every agent session must use the harness CLI for all work, including sessions started from a registered application repository. Do not work directly from an agent session that bypasses the harness.

At session start, run:

```bash
harness doctor
harness index
```

Use `harness ask` for project context and `harness codex` to launch grounded implementation work. Each registered repository must keep the harness guidance available through its `AGENTS.md` or equivalent agent instructions.

## Connection

- Site: `$ATLASSIAN_URL`
- Cloud ID: `$ATLASSIAN_CLOUD_ID` when required by the connected API
- Jira project: `$ATLASSIAN_PROJECT_KEY`
- Jira board: `$ATLASSIAN_BOARD_ID` when required

Never put access tokens, cookies, or personal credentials in this repository.

## Connected-account workflow

When running inside Codex/ChatGPT with the Atlassian connector:

1. Call `getAccessibleAtlassianResources` once and cache the returned cloud ID.
2. Use `search` for broad Jira + Confluence discovery.
3. Use `searchJiraIssuesUsingJql` for project-scoped work, normally `project = EC ORDER BY updated DESC`.
4. Fetch important issues with `getJiraIssue` and documentation with `getConfluenceContent`.
5. Read first. Before changing Jira or Confluence, show the proposed target and change.

If the account has no issues or Confluence spaces, record that fact rather than fabricating requirements.

## Local fallback

Set these variables outside the repo and run:

```bash
python3 -m harness --root . atlassian snapshot
```

Required: `ATLASSIAN_URL`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`, and `ATLASSIAN_PROJECT_KEY`. Optional: `ATLASSIAN_CLOUD_ID` and `ATLASSIAN_BOARD_ID`.

This writes `knowledge/atlassian/jira-issues.json` and keeps credentials out of source control.

## Context reconciliation

Treat `knowledge/architecture.md`, `knowledge/code-patterns.md`, and `knowledge/project-context.md` as local-repository evidence. Treat `knowledge/atlassian/*` as remote evidence. When they disagree, report the discrepancy and prefer the newest explicit project decision, with its Jira/Confluence URL, over an inferred local pattern.

## Engineering guardrails

- Inspect the owning service and contract files before proposing changes.
- Preserve `eventId`, `occurredAt`, and `correlationId` on events.
- Keep ownership boundaries: order orchestrates, inventory owns reservations, product owns catalog data, and contracts define compatibility.
- Add or update a contract test whenever an event schema changes.
- Prefer additive, backward-compatible event changes and explicit compensation.
- Treat demo in-memory data, local credentials, and simulated payment behavior as non-production.
