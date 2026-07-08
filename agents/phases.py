from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class PhaseDefinition:
    key: str
    title: str
    output_filename: str
    instructions: str
    prompt_builder: Callable[[dict[str, str]], str]


BASE_INSTRUCTIONS = (
    "Tu es un agent spécialisé dans la rédaction de livrables de projet. "
    "Réponds en français, dans un style clair, technique et académique. "
    "N'invente pas de faits non présents dans le contexte. "
    "Si une information manque, formule une hypothèse raisonnable et indique-la. "
    "Retourne uniquement le contenu demandé, sans préambule ni conclusion sur ton rôle."
)


def _exploration_prompt(data: dict[str, str]) -> str:
    return f"""
Sujet du projet:
{data["topic"]}

Contexte du dépôt:
{data["repo_context"]}

Tache:
Rédige une synthese d'exploration pour la partie 1 du cahier des charges.
Inclure:
- le domaine metier
- le besoin observe
- les sources de donnees
- le probleme a resoudre
- les premiers constats
- une synthese courte et exploitable pour un rapport
"""


def _objective_prompt(data: dict[str, str]) -> str:
    return f"""
Sujet du projet:
{data["topic"]}

Synthese d'exploration precedente:
{data["exploration"]}

Tache:
Redige la partie objectif et specifications fonctionnelles.
Inclure:
- objectif general
- objectifs specifiques
- utilisateurs cibles
- besoins fonctionnels
- perimetre fonctionnel
- livrables attendus
"""


def _analysis_prompt(data: dict[str, str]) -> str:
    return f"""
Sujet du projet:
{data["topic"]}

Specification fonctionnelle:
{data["objective"]}

Tache:
Redige la partie analyse et conception.
Inclure:
- analyse du besoin
- cas d'utilisation
- entites metier principales
- flux de donnees
- regles de gestion
- contraintes et hypothese de conception
"""


def _architecture_prompt(data: dict[str, str]) -> str:
    return f"""
Sujet du projet:
{data["topic"]}

Analyse et conception:
{data["analysis"]}

Tache:
Redige la partie architecture technique.
Inclure:
- architecture globale
- choix du langage
- bibliotheques
- base de donnees
- composants applicatifs
- deploiement cible
- justification des choix techniques
"""


def _implementation_prompt(data: dict[str, str]) -> str:
    return f"""
Sujet du projet:
{data["topic"]}

Architecture technique:
{data["architecture"]}

Contexte du code existant:
{data["repo_context"]}

Tache:
Redige la partie implementation.
Inclure:
- structure du projet
- modules existants
- pipeline de collecte
- ETL
- backend API
- tableau de bord
- points d'amelioration a implementer
"""


def _deployment_prompt(data: dict[str, str]) -> str:
    return f"""
Sujet du projet:
{data["topic"]}

Implementation:
{data["implementation"]}

Tache:
Redige la partie deploiement et automatisation de deploiement.
Inclure:
- conteneurisation
- orchestration avec Docker Compose
- variables d'environnement
- procedure de lancement
- automatisation possible
- surveillance et exploitation
"""


PHASES: list[PhaseDefinition] = [
    PhaseDefinition(
        key="exploration",
        title="Partie 1 - Exploration",
        output_filename="01_exploration.md",
        instructions=BASE_INSTRUCTIONS,
        prompt_builder=_exploration_prompt,
    ),
    PhaseDefinition(
        key="objective",
        title="Partie 2 - Objectif et specifications fonctionnelles",
        output_filename="02_objectifs_specifications.md",
        instructions=BASE_INSTRUCTIONS,
        prompt_builder=_objective_prompt,
    ),
    PhaseDefinition(
        key="analysis",
        title="Partie 2.5 - Analyse et conception",
        output_filename="03_analyse_conception.md",
        instructions=BASE_INSTRUCTIONS,
        prompt_builder=_analysis_prompt,
    ),
    PhaseDefinition(
        key="architecture",
        title="Partie 3 - Architecture",
        output_filename="04_architecture.md",
        instructions=BASE_INSTRUCTIONS,
        prompt_builder=_architecture_prompt,
    ),
    PhaseDefinition(
        key="implementation",
        title="Partie 4 - Implementation",
        output_filename="05_implementation.md",
        instructions=BASE_INSTRUCTIONS,
        prompt_builder=_implementation_prompt,
    ),
    PhaseDefinition(
        key="deployment",
        title="Partie 5 - Deploiement et automatisation",
        output_filename="06_deploiement.md",
        instructions=BASE_INSTRUCTIONS,
        prompt_builder=_deployment_prompt,
    ),
]

