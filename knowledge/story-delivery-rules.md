# Story Delivery Rules

Stories are planned before implementation and implemented only after explicit user approval.

- Every story must have a real Jira issue key.
- Work types are `feature`, `bug`, `hotfix`, and `release`.
- All affected repositories use the same trunk-based branch name: `<type>/<JIRA-KEY>-<short-kebab-description>`.
- Use Conventional Commits and validate them through the harness.
- Do not push branches or write to Jira/Confluence unless separately authorized.
- Stop on dirty worktrees, ambiguous scope, missing trunk branches, invalid issue keys, or branch collisions.
