from __future__ import annotations

from dataclasses import dataclass

from google import genai


@dataclass
class LLMResponse:
    text: str


class GeminiTextGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, instructions: str, prompt: str) -> LLMResponse:
        response = self.client.interactions.create(
            model=self.model,
            input=(
                f"{instructions}\n\n"
                f"{prompt}"
            ),
        )

        text = getattr(response, "output_text", "") or self._extract_text_from_output(response)
        return LLMResponse(text=text.strip())

    @staticmethod
    def _extract_text_from_output(response: object) -> str:
        chunks: list[str] = []
        output = getattr(response, "output", None)
        if output:
            for item in output:
                if getattr(item, "type", None) != "message":
                    continue
                for content in getattr(item, "content", []) or []:
                    if getattr(content, "type", None) in {"output_text", "text"}:
                        chunks.append(getattr(content, "text", ""))
        if not chunks:
            text = getattr(response, "text", None)
            if text:
                chunks.append(str(text))
        return "".join(chunks)
