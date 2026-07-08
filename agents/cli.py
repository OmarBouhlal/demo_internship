from __future__ import annotations

import argparse
from pathlib import Path

from agents.orchestrator import AgentOrchestrator


DEFAULT_TOPIC = "Reporting Automatisé des Achats Publiques (Holding)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the full agent-based deliverables for the project."
    )
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help="Project topic to feed into the orchestrator.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    orchestrator = AgentOrchestrator(root=Path(args.root).resolve())
    result = orchestrator.run(args.topic)
    print(f"Generated agent deliverables in: {result.output_dir}")
    print(f"Final report: {result.report_path}")


if __name__ == "__main__":
    main()

