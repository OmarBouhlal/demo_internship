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
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    google_key = os.getenv("GOOGLE_API_KEY", "").strip()

    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        os.environ.pop("GOOGLE_API_KEY", None)
        return gemini_key

    if google_key:
        os.environ["GOOGLE_API_KEY"] = google_key
        os.environ.pop("GEMINI_API_KEY", None)
        return google_key

    api_key = ""
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY or GOOGLE_API_KEY is required to run the agent workflow."
        )
    return api_key
