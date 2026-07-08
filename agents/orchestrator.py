from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agents.config import AgentConfig, get_api_key
from agents.context import ProjectContext, load_project_context
from agents.llm import GeminiTextGenerator
from agents.phases import PHASES


@dataclass(frozen=True)
class AgentRunResult:
    phase_outputs: dict[str, str]
    report_path: Path
    output_dir: Path


class WorkflowState(TypedDict, total=False):
    topic: str
    repo_context: str
    output_dir: str
    exploration: str
    objective: str
    analysis: str
    architecture: str
    implementation: str
    deployment: str
    phase_outputs: dict[str, str]
    report_path: str


class AgentOrchestrator:
    def __init__(self, root: Path, config: AgentConfig | None = None) -> None:
        self.root = root
        self.config = config or AgentConfig()
        self.output_dir = self.config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        api_key = get_api_key()
        self.generator = GeminiTextGenerator(api_key=api_key, model=self.config.model)
        self.context = load_project_context(root)
        self.graph = self._build_graph()

    def run(self, topic: str) -> AgentRunResult:
        initial_state: WorkflowState = {
            "topic": topic,
            "repo_context": self.context.as_prompt_block(),
            "output_dir": str(self.output_dir),
            "phase_outputs": {},
        }
        final_state = self.graph.invoke(initial_state)
        phase_outputs = final_state.get("phase_outputs", {})
        report_path_value = final_state.get("report_path")
        if not report_path_value:
            raise RuntimeError("The LangGraph workflow did not produce a report path.")
        report_path = Path(report_path_value)
        return AgentRunResult(
            phase_outputs=phase_outputs,
            report_path=report_path,
            output_dir=self.output_dir,
        )

    def _build_graph(self) -> StateGraph[WorkflowState]:
        graph: StateGraph[WorkflowState] = StateGraph(WorkflowState)

        for phase in PHASES:
            graph.add_node(phase.key, self._make_phase_node(phase))

        graph.add_node("final_report", self._final_report_node)

        graph.add_edge(START, PHASES[0].key)
        for current, nxt in zip(PHASES, PHASES[1:]):
            graph.add_edge(current.key, nxt.key)
        graph.add_edge(PHASES[-1].key, "final_report")
        graph.add_edge("final_report", END)

        return graph.compile()

    def _make_phase_node(self, phase):
        def node(state: WorkflowState) -> WorkflowState:
            prompt = phase.prompt_builder(state)
            result = self.generator.generate(
                instructions=phase.instructions,
                prompt=prompt,
            ).text
            self._write_phase_file(phase.output_filename, phase.title, result)

            phase_outputs = dict(state.get("phase_outputs", {}))
            phase_outputs[phase.key] = result
            return {
                phase.key: result,
                "phase_outputs": phase_outputs,
            }

        return node

    def _final_report_node(self, state: WorkflowState) -> WorkflowState:
        topic = state["topic"]
        phase_outputs = state.get("phase_outputs", {})
        report_path = self._write_final_report(topic, phase_outputs)
        return {"report_path": str(report_path)}

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
