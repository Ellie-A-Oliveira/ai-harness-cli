from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_IGNORES = {".git", ".venv", "node_modules", "dist", "build", "__pycache__", ".pytest_cache", ".harness", "runs"}
TEXT_SUFFIXES = {".md", ".mdx", ".txt", ".rst", ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".json", ".yaml", ".yml", ".toml", ".sql"}
TOKEN_RE = re.compile(r"[a-zA-Z0-9_'-]+")


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
    lines = ["You are working inside an AI Harness workspace.", "Use the retrieved context as evidence, but inspect the repository before changing files.", "", f"Task: {task}", "", "Retrieved context:"]
    if not context:
        lines.append("(No matching indexed context. Work from the repository and say what you inspected.)")
    for item in context:
        lines.extend([f"\n--- {item['source']}:{item['path']} (score {item['score']}) ---", item["content"]])
    return "\n".join(lines)


def codex_available() -> str | None:
    return shutil.which("codex")
