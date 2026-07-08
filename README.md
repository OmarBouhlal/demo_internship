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

## Notes

- `al_omrane_group.csv` is a generated artifact and is ignored by Git.
- Secrets must stay in environment variables, not in source control.
