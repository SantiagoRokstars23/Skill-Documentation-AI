"""Tests de skills/spring-doc/SKILL.md.

La SKILL debe ser un artefacto LLM-agnostico, agente-agnostico y motor-agnostico:
conocimiento/proceso para documentar un microservicio Java/Spring Boot leyendo su
codigo fuente directamente, sin depender de `spring-doc` (la CLI de este
proyecto) ni de ningun otro componente del repositorio, y sin describir su
arquitectura interna. Puede mencionar `spring-doc` como herramienta opcional,
nunca como requisito. Estos tests verifican esas propiedades, no que documente
una API de linea de comandos (eso quedaria fuera de alcance para este archivo).
"""

from __future__ import annotations

from pathlib import Path

import yaml

SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "spring-doc" / "SKILL.md"

# Rutas/paquetes internos del proyecto: la SKILL no debe describir la
# arquitectura interna de spring-doc (regla explicita del ajuste de alcance).
INTERNAL_PROJECT_REFERENCES = [
    "providers/",
    "analyzer/",
    "generators/",
    "validator/",
    "cli/",
    "ProviderConfig",
    "LLMProvider",
    "FakeProvider",
    "AnalysisResult",
]

# Sintaxis especifica de la CLI de este proyecto: la SKILL no debe requerirla
# ni documentarla como si fuera necesaria para seguir el proceso.
CLI_SPECIFIC_TOKENS = [
    "--format",
    "--json",
    "--output",
    "--strict",
    "--quiet",
    "spring-doc analyze",
    "spring-doc generate",
    "spring-doc validate",
]

# Lenguaje que ataria la SKILL a un agente o proveedor LLM concreto.
AGENT_OR_PROVIDER_SPECIFIC_PHRASES = [
    "Claude Code's",
    "OpenCode's",
    "Codex's",
    "Anthropic's",
    "OpenAI's",
    "Gemini's",
    "As Claude,",
    "As an Anthropic model,",
]


def _read_skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> dict:
    assert text.startswith("---\n"), "SKILL.md debe empezar con frontmatter YAML ('---')"
    closing = text.index("\n---", 4)
    return yaml.safe_load(text[4:closing])


def test_skill_file_exists():
    assert SKILL_PATH.is_file()


def test_skill_frontmatter_has_name_and_description():
    frontmatter = _parse_frontmatter(_read_skill_text())
    assert frontmatter["name"] == "spring-doc"
    assert isinstance(frontmatter["description"], str)
    assert len(frontmatter["description"]) > 0


def test_skill_does_not_reference_internal_project_structure():
    text = _read_skill_text()
    for reference in INTERNAL_PROJECT_REFERENCES:
        assert reference not in text, (
            f"SKILL.md menciona '{reference}' -- no debe describir la arquitectura "
            "interna de spring-doc (providers/analyzer/generators/validator/cli)."
        )


def test_skill_does_not_document_cli_syntax():
    text = _read_skill_text()
    for token in CLI_SPECIFIC_TOKENS:
        assert token not in text, (
            f"SKILL.md contiene '{token}' -- no debe documentar la sintaxis de la "
            "CLI spring-doc como parte de sus instrucciones."
        )


def test_skill_does_not_target_a_specific_agent_or_provider():
    text = _read_skill_text()
    for phrase in AGENT_OR_PROVIDER_SPECIFIC_PHRASES:
        assert phrase not in text


def test_skill_mentions_of_spring_doc_are_framed_as_optional():
    text = _read_skill_text()
    if "spring-doc" in text.split("---", 2)[-1]:
        # Se permite mencionarlo (regla: "puede mencionar herramientas externas
        # como opciones"), pero debe quedar explicitamente marcado como opcional.
        assert "optional" in text.lower()
        assert "not a requirement" in text.lower() or "never a requirement" in text.lower() \
            or "entirely optional" in text.lower()


def test_skill_does_not_require_any_specific_tool_to_follow_it():
    text = _read_skill_text()
    lowered = text.lower()
    forbidden_requirement_phrases = [
        "requires spring-doc",
        "must install spring-doc",
        "spring-doc is required",
        "you must use spring-doc",
        "depends on spring-doc",
    ]
    for phrase in forbidden_requirement_phrases:
        assert phrase not in lowered


def test_skill_states_it_works_from_source_code_alone():
    text = _read_skill_text().lower()
    assert "source code" in text
    assert "no other tooling" in text or "reading source files yourself" in text or (
        "standalone" in text
    )


def test_skill_teaches_evidence_based_principles():
    text = _read_skill_text()
    for phrase in ["evidence", "never invent", "ambigu"]:
        assert phrase.lower() in text.lower(), f"falta principio esperado: '{phrase}'"


def test_skill_explicitly_warns_against_inventing_status_codes_and_security():
    text = _read_skill_text().lower()
    assert "status code" in text
    assert "security" in text


def test_skill_does_not_hardcode_a_secret_looking_value():
    text = _read_skill_text().lower()
    for suspicious in ("api_key=", "api_key =", "sk-ant-", "sk-proj-", "bearer "):
        assert suspicious not in text


def test_skill_is_reasonably_self_contained_markdown():
    text = _read_skill_text()
    # No debe referenciar rutas de documentacion internas del repositorio como
    # si fueran necesarias para entender la skill (debe ser copiable sola).
    assert "docs/" not in text
    assert "prompts/" not in text
