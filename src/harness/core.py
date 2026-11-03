from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import urllib.error
import urllib.request
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_IGNORES = {".git", ".venv", "node_modules", "dist", "build", "__pycache__", ".pytest_cache", ".harness", "runs"}
TEXT_SUFFIXES = {".md", ".mdx", ".txt", ".rst", ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".json", ".yaml", ".yml", ".toml", ".sql"}
TOKEN_RE = re.compile(r"[a-zA-Z0-9_'-]+")
CONVENTIONAL_COMMIT_RE = re.compile(r"^(?P<type>feat|fix|docs|refactor|test|chore|build|ci|perf|revert|style)(\([a-z0-9._/-]+\))?(?P<breaking>!)?: .+")


class HarnessError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Workspace:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.meta = self.root / ".harness"
        self.config_path = self.meta / "config.json"
        self.sources_path = self.root / "sources.json"
        self.index_path = self.meta / "index.json"
        self.atlassian_config_path = self.root / "config" / "atlassian-ec.json"
        self.atlassian_snapshot_path = self.root / "knowledge" / "atlassian" / "jira-issues.json"
        self.security_policy_path = self.root / "config" / "security-policy.json"

    def require(self) -> None:
        if not self.config_path.exists():
            raise HarnessError(f"Not an AI Harness workspace: {self.root}. Run `harness init {self.root}` first.")

    def config(self) -> dict:
        self.require()
        return json.loads(self.config_path.read_text())

    def sources(self) -> list[dict]:
        if not self.sources_path.exists():
            return []
        return json.loads(self.sources_path.read_text())

    def save_sources(self, sources: list[dict]) -> None:
        self.sources_path.write_text(json.dumps(sources, indent=2) + "\n")

    def init(self) -> None:
        self.meta.mkdir(parents=True, exist_ok=True)
        (self.root / "runs").mkdir(exist_ok=True)
        if not self.config_path.exists():
            self.config_path.write_text(json.dumps({"version": 1, "created_at": now(), "chunk_size": 1200, "top_k": 6}, indent=2) + "\n")
        if not self.sources_path.exists():
            self.save_sources([])
        self.configure_atlassian()
        self.configure_security()

    def configure_security(self) -> None:
        self.security_policy_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.security_policy_path.exists():
            self.security_policy_path.write_text(json.dumps({
                "version": 1,
                "approved_prefixes": ["git pull", "git switch", "npx next dev", "npm run build"],
                "safe_read_only_prefixes": ["pwd", "ls", "rg", "git status", "git diff", "git log", "git show", "git branch", "git rev-parse", "find", "sed", "head", "tail", "python3 -m unittest", "npm test"],
                "blocked_prefixes": ["sudo", "rm", "rmdir", "git reset --hard", "git checkout --", "git clean", "dd", "mkfs", "chmod 777", "kill", "pkill"],
                "blocked_shell_tokens": [";", "&&", "||", "|", ">", "<", "`", "$(", "\\n"],
                "requires_explicit_approval": ["network access", "package installation", "credential access", "destructive file operations", "external writes", "publishing or messaging"],
                "notes": "This policy is a preflight check and documentation. OS sandboxing and user approval remain authoritative."
            }, indent=2) + "\n")

    def security_policy(self) -> dict:
        self.require()
        self.configure_security()
        return json.loads(self.security_policy_path.read_text())

    def check_command(self, command: str) -> dict:
        policy = self.security_policy()
        command = command.strip()
        if not command:
            raise HarnessError("Command cannot be empty.")
        if "\n" in command or any(token in command for token in policy["blocked_shell_tokens"]):
            return {"status": "blocked", "reason": "shell control or substitution token detected", "command": command}
        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            return {"status": "blocked", "reason": f"invalid shell quoting: {exc}", "command": command}

        def matches(prefix: str) -> bool:
            expected = shlex.split(prefix)
            return tokens[:len(expected)] == expected

        if any(matches(prefix) for prefix in policy["blocked_prefixes"]):
            return {"status": "blocked", "reason": "blocked command prefix", "command": command}
        if any(matches(prefix) for prefix in policy["approved_prefixes"]):
            return {"status": "approved", "reason": "pre-approved command prefix", "command": command}
        if any(matches(prefix) for prefix in policy["safe_read_only_prefixes"]):
            return {"status": "safe_read_only", "reason": "read-only or test command", "command": command}
        return {"status": "requires_approval", "reason": "command is not in the approved policy", "command": command}

    def check_commit_message(self, message: str) -> dict:
        candidate = message.strip().splitlines()[0] if message.strip() else ""
        if CONVENTIONAL_COMMIT_RE.match(candidate):
            return {"status": "valid", "message": candidate, "reason": "matches Conventional Commits"}
        return {"status": "invalid", "message": candidate, "reason": "use type(scope): description, for example feat(cli): add command preflight"}

    def configure_atlassian(self) -> None:
        self.atlassian_config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.atlassian_config_path.exists():
            self.atlassian_config_path.write_text(json.dumps({
                "site_url_env": "ATLASSIAN_URL",
                "cloud_id_env": "ATLASSIAN_CLOUD_ID",
                "project_key_env": "ATLASSIAN_PROJECT_KEY",
                "board_id_env": "ATLASSIAN_BOARD_ID",
                "email_env": "ATLASSIAN_EMAIL",
                "api_token_env": "ATLASSIAN_API_TOKEN",
                "auth": "environment variables or connected Atlassian MCP",
                "last_snapshot_at": None
            }, indent=2) + "\n")

    def atlassian_settings(self) -> dict:
        required = {name: os.getenv(name) for name in ("ATLASSIAN_URL", "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN", "ATLASSIAN_PROJECT_KEY")}
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise HarnessError("Missing Atlassian environment variables: " + ", ".join(missing) + ". Set them outside the repository or use the connected Atlassian MCP.")
        return {
            "site_url": required["ATLASSIAN_URL"].rstrip("/"),
            "project_key": required["ATLASSIAN_PROJECT_KEY"],
            "cloud_id": os.getenv("ATLASSIAN_CLOUD_ID"),
            "board_id": os.getenv("ATLASSIAN_BOARD_ID"),
            "email": required["ATLASSIAN_EMAIL"],
            "api_token": required["ATLASSIAN_API_TOKEN"],
        }

    def atlassian_snapshot(self) -> int:
        self.require()
        self.configure_atlassian()
        settings = self.atlassian_settings()
        url = f"{settings['site_url']}/rest/api/3/search?jql=project%3D{settings['project_key']}%20ORDER%20BY%20updated%20DESC&maxResults=100&fields=summary,description,status,issuetype,priority,assignee,labels,updated,created"
        request = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "Authorization": "Basic " + base64.b64encode(f"{settings['email']}:{settings['api_token']}".encode()).decode(),
        })
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode())
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise HarnessError(f"Atlassian snapshot failed: {exc}") from exc
        issues = payload.get("issues", [])
        self.atlassian_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.atlassian_snapshot_path.write_text(json.dumps({"project": {key: value for key, value in settings.items() if key not in {"email", "api_token"}}, "fetched_at": now(), "issues": issues}, indent=2) + "\n")
        config = json.loads(self.atlassian_config_path.read_text())
        config["last_snapshot_at"] = now()
        self.atlassian_config_path.write_text(json.dumps(config, indent=2) + "\n")
        return len(issues)

    def add(self, path: Path, name: str | None = None) -> dict:
        self.require()
        path = path.expanduser().resolve()
        if not path.exists():
            raise HarnessError(f"Source does not exist: {path}")
        sources = self.sources()
        key = str(path)
        existing = next((source for source in sources if source["path"] == key), None)
        if existing:
            return existing
        source = {"name": name or path.name, "path": key, "added_at": now()}
        sources.append(source)
        self.save_sources(sources)
        return source

    def iter_files(self) -> Iterable[tuple[dict, Path]]:
        for source in self.sources():
            path = Path(source["path"])
            paths = [path] if path.is_file() else path.rglob("*")
            for file_path in paths:
                if not file_path.is_file() or file_path.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                if any(part in DEFAULT_IGNORES for part in file_path.parts):
                    continue
                yield source, file_path

    def index(self) -> int:
        self.require()
        chunk_size = int(self.config().get("chunk_size", 1200))
        records = []
        for source, file_path in self.iter_files():
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            relative = str(file_path.relative_to(Path(source["path"]))) if Path(source["path"]).is_dir() else file_path.name
            for offset in range(0, len(text), chunk_size):
                content = text[offset:offset + chunk_size].strip()
                if content:
                    records.append({"source": source["name"], "path": relative, "offset": offset, "content": content})
        self.index_path.write_text(json.dumps({"indexed_at": now(), "chunks": records}, indent=2) + "\n")
        return len(records)

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        self.require()
        if not self.index_path.exists():
            self.index()
        data = json.loads(self.index_path.read_text())
        q = set(token.lower() for token in TOKEN_RE.findall(query))
        scored = []
        for chunk in data.get("chunks", []):
            tokens = [token.lower() for token in TOKEN_RE.findall(chunk["content"])]
            score = sum(tokens.count(token) for token in q)
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1]["path"], item[1]["offset"]))
        limit = top_k or int(self.config().get("top_k", 6))
        return [dict(chunk, score=score) for score, chunk in scored[:limit]]

    def codex(self, task: str, top_k: int | None = None, model: str | None = None) -> tuple[int, str]:
        self.require()
        context = self.search(task, top_k)
        prompt = build_prompt(task, context)
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = self.root / "runs"
        run_dir.mkdir(exist_ok=True)
        (run_dir / f"{run_id}.prompt.md").write_text(prompt)
        command = ["codex", "exec", "--sandbox", "workspace-write", "--skip-git-repo-check"]
        if model:
            command += ["--model", model]
        command.append(prompt)
        try:
            result = subprocess.run(command, cwd=self.root, text=True, capture_output=True)
        except FileNotFoundError as exc:
            raise HarnessError("Codex CLI was not found on PATH.") from exc
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        (run_dir / f"{run_id}.output.txt").write_text(output)
        return result.returncode, output


def build_prompt(task: str, context: list[dict]) -> str:
    lines = ["You are working inside an AI Harness workspace.", "MANDATORY: use the harness CLI for all work in this session. Start with `harness doctor`, use `harness ask`/`harness index` for context, run `harness security check-command` before shell commands, and make changes only through a harness-launched workflow. Do not bypass the harness with direct agent work.", "Use the retrieved context as evidence, but inspect the repository before changing files.", "", f"Task: {task}", "", "Retrieved context:"]
    if not context:
        lines.append("(No matching indexed context. Work from the repository and say what you inspected.)")
    for item in context:
        lines.extend([f"\n--- {item['source']}:{item['path']} (score {item['score']}) ---", item["content"]])
    return "\n".join(lines)


def codex_available() -> str | None:
    return shutil.which("codex")
