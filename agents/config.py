from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AgentConfig:
    model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    output_dir: Path = Path(os.getenv("AGENT_OUTPUT_DIR", "generated_reports"))


def get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY or GOOGLE_API_KEY is required to run the agent workflow."
        )
    return api_key
