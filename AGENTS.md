# Agent Instructions

This repository is the shared AI Harness. Every agent session must use the harness CLI for all work.

Start with `harness doctor`, `harness index`, and `harness ask`. Launch implementation through `harness codex`. Before shell execution, run `harness security check-command "<command>"` and follow [knowledge/security-requirements.md](knowledge/security-requirements.md).

Use Conventional Commits for every commit; validate with `harness security check-commit "<message>"`.
