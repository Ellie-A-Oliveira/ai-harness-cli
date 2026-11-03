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

This first version intentionally uses lexical retrieval and the local Codex CLI. That keeps setup simple while leaving clear seams for embeddings, reranking, and remote stores later.
