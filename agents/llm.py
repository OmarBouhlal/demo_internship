from __future__ import annotations

import time
from dataclasses import dataclass

from google import genai
from google.genai import types
from google.genai.errors import ServerError


@dataclass
class LLMResponse:
    text: str


class GeminiTextGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, instructions: str, prompt: str) -> LLMResponse:
        response = self._generate_with_retries(instructions, prompt)

        text = getattr(response, "text", "") or self._extract_text_from_output(response)
        return LLMResponse(text=text.strip())

    def _generate_with_retries(self, instructions: str, prompt: str):
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                return self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        systemInstruction=instructions,
                        temperature=0.2,
                        maxOutputTokens=4096,
                    ),
                )
            except ServerError as exc:
                last_error = exc
                status_code = getattr(exc, "status_code", None)
                if status_code not in {429, 503} or attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        raise last_error or RuntimeError("Gemini generation failed unexpectedly.")

    @staticmethod
    def _extract_text_from_output(response: object) -> str:
        chunks: list[str] = []
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                if getattr(part, "text", None):
                    chunks.append(str(getattr(part, "text")))
        if not chunks and getattr(response, "text", None):
            chunks.append(str(getattr(response, "text")))
        return "".join(chunks)
