# ExtracterAgent

Pipeline ETL et dashboard pour les données du groupe Al Omrane.

## Prérequis

- Python 3.14+
- Docker and Docker Compose

## Configuration

1. Copy `.env.example` to `.env`
2. Set a real value for `DB_PASS`

## Local run

### With Docker

```bash
docker compose up --build
```

### Without Docker

```bash
pip install -r requirements.txt
```

Run the scraper to generate `al_omrane_group.csv`, then run the ETL to load it into PostgreSQL.

## Agent workflow

The project now includes an AI-agent pipeline for the written deliverables, orchestrated with LangGraph:

- exploration agent
- objective/specification agent
- analysis and conception agent
- architecture agent
- implementation agent
- deployment agent

Run it with:

```bash
python -m agents --topic "Reporting Automatisé des Achats Publiques (Holding)"
```

Required environment variables for the agent workflow:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` with default `gpt-4.1-mini`
- `AGENT_OUTPUT_DIR` with default `generated_reports`

The orchestrator writes one markdown file per phase and a final `cahier_de_charge.md`.

## Notes

- `al_omrane_group.csv` is a generated artifact and is ignored by Git.
- Secrets must stay in environment variables, not in source control.
