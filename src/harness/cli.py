from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import HarnessError, Workspace, build_prompt, codex_available


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harness", description="Centralize local AI harness and RAG work, with Codex handoff.")
    p.add_argument("--root", type=Path, default=Path.cwd(), help="Harness workspace root (default: current directory)")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create a harness workspace")
    init.add_argument("path", type=Path)
    add = sub.add_parser("add", help="Register a local repository or directory")
    add.add_argument("path", type=Path)
    add.add_argument("--name")
    sub.add_parser("list", help="List registered sources")
    sub.add_parser("index", help="Build the local RAG index")
    ask = sub.add_parser("ask", help="Retrieve relevant context")
    ask.add_argument("question", nargs="+")
    ask.add_argument("--top-k", type=int)
    codex = sub.add_parser("codex", help="Run a grounded task with Codex")
    codex.add_argument("task", nargs="+")
    codex.add_argument("--top-k", type=int)
    codex.add_argument("--model")
    sub.add_parser("doctor", help="Check workspace and Codex availability")
    atlassian = sub.add_parser("atlassian", help="Manage configured Atlassian project context")
    atlassian_sub = atlassian.add_subparsers(dest="atlassian_command", required=True)
    atlassian_sub.add_parser("configure", help="Write EC project connection metadata")
    atlassian_sub.add_parser("snapshot", help="Fetch Jira issue context into knowledge/atlassian")
    security = sub.add_parser("security", help="Inspect and preflight the harness security policy")
    security_sub = security.add_subparsers(dest="security_command", required=True)
    security_sub.add_parser("show", help="Print the security policy")
    check = security_sub.add_parser("check-command", help="Classify a shell command before execution")
    check.add_argument("command_text", nargs="+")
    commit = security_sub.add_parser("check-commit", help="Validate a Conventional Commit message")
    commit.add_argument("message", nargs="+")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            workspace = Workspace(args.path)
            workspace.init()
            print(f"Initialized AI Harness workspace at {workspace.root}")
            return 0
        workspace = Workspace(args.root)
        if args.command == "add":
            source = workspace.add(args.path, args.name)
            print(f"Registered {source['name']}: {source['path']}")
        elif args.command == "list":
            for source in workspace.sources():
                print(f"{source['name']}\t{source['path']}")
        elif args.command == "index":
            count = workspace.index()
            print(f"Indexed {count} chunks into {workspace.index_path}")
        elif args.command == "ask":
            results = workspace.search(" ".join(args.question), args.top_k)
            if not results:
                print("No matching context found.")
            for item in results:
                print(f"\n[{item['source']}:{item['path']} | score={item['score']}]\n{item['content']}")
        elif args.command == "codex":
            code, output = workspace.codex(" ".join(args.task), args.top_k, args.model)
            print(output, end="" if output.endswith("\n") else "\n")
            return code
        elif args.command == "doctor":
            workspace.require()
            print(json.dumps({"workspace": str(workspace.root), "codex": codex_available() or "not found", "sources": len(workspace.sources()), "index": workspace.index_path.exists()}, indent=2))
        elif args.command == "atlassian":
            if args.atlassian_command == "configure":
                workspace.configure_atlassian()
                print(f"Configured Atlassian EC metadata in {workspace.atlassian_config_path}")
            else:
                count = workspace.atlassian_snapshot()
                print(f"Wrote {count} Jira issues to {workspace.atlassian_snapshot_path}")
        elif args.command == "security":
            if args.security_command == "show":
                print(json.dumps(workspace.security_policy(), indent=2))
            elif args.security_command == "check-command":
                result = workspace.check_command(" ".join(args.command_text))
                print(json.dumps(result, indent=2))
                if result["status"] == "blocked":
                    return 2
            else:
                result = workspace.check_commit_message(" ".join(args.message))
                print(json.dumps(result, indent=2))
                if result["status"] == "invalid":
                    return 2
        return 0
    except HarnessError as exc:
        print(f"harness: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
