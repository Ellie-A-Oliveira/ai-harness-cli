#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys

ISSUE_RE = re.compile(r"^[A-Z][A-Z0-9]+-[0-9]+$")
KINDS = {"feature", "bug", "hotfix", "release"}


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def branch_name(kind: str, issue: str, summary: str) -> str:
    if kind not in KINDS:
        raise ValueError(f"type must be one of: {', '.join(sorted(KINDS))}")
    if not ISSUE_RE.fullmatch(issue):
        raise ValueError("issue must match PROJECT-123 with an uppercase Jira project key")
    description = slugify(summary)
    if not description:
        raise ValueError("summary must contain at least one letter or number")
    return f"{kind}/{issue}-{description}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a trunk-based Jira branch name")
    parser.add_argument("--type", required=True, choices=sorted(KINDS), dest="kind")
    parser.add_argument("--issue", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    try:
        print(branch_name(args.kind, args.issue, args.summary))
    except ValueError as exc:
        print(f"branch-name: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
