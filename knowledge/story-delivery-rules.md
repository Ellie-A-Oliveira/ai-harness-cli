# Story Delivery Rules

Stories are planned before implementation and implemented only after explicit user approval.

- Every story must have a real Jira issue key.
- Work types are `feature`, `bug`, `hotfix`, and `release`.
- All affected repositories use the same trunk-based branch name: `<type>/<JIRA-KEY>-<short-kebab-description>`.
- Use Conventional Commits and validate them through the harness.
- Do not push branches or write to Jira/Confluence unless separately authorized.
- Stop on dirty worktrees, ambiguous scope, missing trunk branches, invalid issue keys, or branch collisions.
- Registered application repositories may be nested under a parent workspace; identify the owning Git checkout and its origin before branching or opening a PR.
- A dirty bootstrap checkout may proceed only after explicit user authorization; preserve unrelated untracked content and stage only the approved story scope.
