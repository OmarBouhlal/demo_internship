from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI


@dataclass
class LLMResponse:
    text: str


class OpenAITextGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, instructions: str, prompt: str) -> LLMResponse:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
        )

        text = getattr(response, "output_text", None)
        if not text:
            text = self._extract_text_from_output(response)

        return LLMResponse(text=text.strip())

    @staticmethod
    def _extract_text_from_output(response: object) -> str:
        chunks: list[str] = []
        output = getattr(response, "output", []) or []
        for item in output:
            if getattr(item, "type", None) != "message":
                continue
            for content in getattr(item, "content", []) or []:
                content_type = getattr(content, "type", None)
                if content_type in {"output_text", "text"}:
                    chunks.append(getattr(content, "text", ""))
        return "".join(chunks)

