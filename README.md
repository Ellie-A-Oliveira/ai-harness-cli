# AI Harness

`harness` is a small, dependency-free CLI for centralizing AI harness work and local RAG knowledge, with an optional handoff to the installed Codex CLI.

## Quick start

```bash
cd ai-harness
python3 -m harness init ~/ai-workspace
python3 -m harness --root ~/ai-workspace add ~/projects/my-rag-repo
python3 -m harness --root ~/ai-workspace index
python3 -m harness --root ~/ai-workspace ask "How does retrieval work?"
python3 -m harness --root ~/ai-workspace codex "Improve the retrieval ranking and add tests"
```

The `codex` command retrieves relevant local context, writes a grounded prompt, and runs `codex exec` from the workspace root. It does not require an API key when Codex is already authenticated.

## Mandatory session rule

Every agent session must use this CLI for all work, including sessions launched inside any registered repository. Start with `harness doctor` and `harness index`, retrieve context with `harness ask`, and launch implementation through `harness codex`. Do not bypass the harness with direct agent work.

## Workspace layout

```text
workspace/
├── .harness/config.json
├── .harness/index.json
├── sources.json
└── runs/                 # prompts and responses from `codex`
```

Sources remain in place; the CLI registers their paths and indexes text into a local, git-friendly JSON index. Do not add secrets or generated credentials to indexed source paths.

## Commands

- `init PATH` creates a workspace.
- `add PATH` registers a local repository or document directory.
- `list` shows registered sources and indexed file counts.
- `index` rebuilds the local lexical index.
- `ask QUESTION` returns the best matching chunks with file citations.
- `codex TASK` sends the task plus retrieved context to `codex exec`.
- `doctor` checks the workspace and Codex installation.
- `atlassian configure` stores non-secret EC project connection metadata.
- `atlassian snapshot` refreshes Jira issue context when REST credentials are available.
- `security show` prints the command and agent security policy.
- `security check-command COMMAND` classifies a command before execution.

This first version intentionally uses lexical retrieval and the local Codex CLI. That keeps setup simple while leaving clear seams for embeddings, reranking, and remote stores later.

The `skills/atlassian-ec/SKILL.md` skill documents the connected Atlassian workflow and reconciles remote context with the local `knowledge/` files. Set `ATLASSIAN_URL`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`, and `ATLASSIAN_PROJECT_KEY` outside the repository; `ATLASSIAN_CLOUD_ID` and `ATLASSIAN_BOARD_ID` are optional.

Security policy is stored in `config/security-policy.json`. It includes the pre-approved prefixes `git pull`, `git switch`, `npx next dev`, and `npm run build`, safe read-only/test commands, blocked destructive/shell-control patterns, and actions that require explicit approval. The CLI performs preflight classification; OS sandboxing and user approvals remain authoritative.

All repositories use Conventional Commits. Validate messages with `harness security check-commit "feat(cli): add command preflight"` before committing.
