from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AgentConfig:
    model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    output_dir: Path = Path(os.getenv("AGENT_OUTPUT_DIR", "generated_reports"))


def get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required to run the agent workflow."
        )
    return api_key

