from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agents.config import AgentConfig, get_api_key
from agents.context import ProjectContext, load_project_context
from agents.llm import OpenAITextGenerator
from agents.phases import PHASES


@dataclass(frozen=True)
class AgentRunResult:
    phase_outputs: dict[str, str]
    report_path: Path
    output_dir: Path


class AgentOrchestrator:
    def __init__(self, root: Path, config: AgentConfig | None = None) -> None:
        self.root = root
        self.config = config or AgentConfig()
        self.output_dir = self.config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        api_key = get_api_key()
        self.generator = OpenAITextGenerator(api_key=api_key, model=self.config.model)
        self.context = load_project_context(root)

    def run(self, topic: str) -> AgentRunResult:
        state: dict[str, str] = {
            "topic": topic,
            "repo_context": self.context.as_prompt_block(),
        }
        phase_outputs: dict[str, str] = {}

        for phase in PHASES:
            prompt = phase.prompt_builder(state)
            result = self.generator.generate(
                instructions=phase.instructions,
                prompt=prompt,
            ).text
            phase_outputs[phase.key] = result
            state[phase.key] = result
            self._write_phase_file(phase.output_filename, phase.title, result)

        report_path = self._write_final_report(topic, phase_outputs)
        return AgentRunResult(
            phase_outputs=phase_outputs,
            report_path=report_path,
            output_dir=self.output_dir,
        )

    def _write_phase_file(self, filename: str, title: str, content: str) -> None:
        path = self.output_dir / filename
        path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")

    def _write_final_report(self, topic: str, phase_outputs: dict[str, str]) -> Path:
        path = self.output_dir / "cahier_de_charge.md"
        sections = [f"# Cahier de charge\n\n## Sujet\n{topic}\n"]
        for phase in PHASES:
            sections.append(f"## {phase.title}\n\n{phase_outputs.get(phase.key, '')}\n")
        path.write_text("\n".join(sections), encoding="utf-8")
        return path

