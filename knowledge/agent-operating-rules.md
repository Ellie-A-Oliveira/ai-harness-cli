# Agent Operating Rules

These rules are mandatory shared knowledge for every agent session:

1. Use the harness CLI for all work, including sessions launched inside registered repositories.
2. Start each session with `harness doctor` and `harness index`.
3. Use `harness ask` before forming an implementation plan or answering project questions.
4. Use `harness codex` to launch grounded coding work; do not bypass the harness with direct agent edits.
5. Keep credentials and environment-specific connection values outside the repository.
6. Cite local files and Atlassian sources when stating project facts, and label assumptions.
7. Run `harness security check-command "<command>"` before any shell command.
8. Treat `blocked` commands as prohibited. Treat `requires_approval` commands as requiring explicit user approval before execution.
9. Never place secrets, tokens, cookies, private keys, or sensitive personal data in commands, prompts, logs, indexed sources, or generated files.
10. All harness CLI commands, non-destructive `git ...` commands, and repository toolchain commands are pre-approved, including environment-prefixed forms: Maven/Spring Boot (`mvn`, `./mvnw`), Node/NestJS (`npm`, `npx`, `nest`), Python/FastAPI (`python3 -m venv`, `pip`, `uvicorn`, `pytest`), and Docker (`docker`, `docker compose`). Destructive Git commands remain blocked.
11. Use Conventional Commits for every repository: `type(scope): description`, such as `feat(cli): add command preflight` or `fix(index): ignore generated files`.
12. Run `harness security check-commit "<message>"` before committing.
