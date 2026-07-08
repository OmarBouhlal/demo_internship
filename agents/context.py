from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_FILES = [
    "README.md",
    "tables.sql",
    "requirements.txt",
    "docker-compose.yml",
    "Dockerfile",
    "scrapper.py",
    "etl_pipeline.py",
    "backend/main.py",
    "frontend/dashboard.py",
]


@dataclass(frozen=True)
class ProjectContext:
    root: Path
    files: dict[str, str]

    def as_prompt_block(self) -> str:
        parts: list[str] = []
        for rel_path, content in self.files.items():
            parts.append(f"### {rel_path}\n{content}")
        return "\n\n".join(parts)


def load_project_context(root: Path, max_chars_per_file: int = 8000) -> ProjectContext:
    files: dict[str, str] = {}
    for rel_path in PROJECT_FILES:
        path = root / rel_path
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + "\n... [truncated]"
        files[rel_path] = content
    return ProjectContext(root=root, files=files)

