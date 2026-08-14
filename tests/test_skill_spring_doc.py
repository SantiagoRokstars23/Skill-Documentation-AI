"""Tests de skills/spring-doc/SKILL.md.

La SKILL tiene dos modos, claramente delimitados por la seccion
"## Optional: end-to-end orchestration using the spring-doc engine" (V0.9):

- **Modo por defecto** (todo el contenido ANTES de esa seccion): conocimiento/
  proceso para documentar un microservicio Java/Spring Boot leyendo su codigo
  fuente directamente. LLM-agnostico, agente-agnostico y motor-agnostico por
  completo -- cero referencias a `spring-doc`/arquitectura interna del
  proyecto/sintaxis de CLI. Debe seguir funcionando igual sin `spring-doc`
  instalado y sin ningun LLM disponible.
- **Modo de orquestacion opcional** (la seccion nueva en si, V0.9): SI puede
  referenciar la CLI `spring-doc` y las abstracciones publicas del motor
  (`ProviderConfig`/`get_provider`/`LLMProvider`) -- es exactamente su
  proposito, documentado explicitamente como capa adicional opcional, nunca
  como reemplazo del modo por defecto.

Ambos modos deben permanecer, en todo momento, sin mencionar ni depender de
ningun LLM o agente concreto (Claude Code, OpenCode, Codex, ChatGPT,
Anthropic, Gemini, OpenAI, u otro).
"""

from __future__ import annotations

from pathlib import Path

import yaml

SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "spring-doc" / "SKILL.md"

ORCHESTRATION_SECTION_MARKER = (
    "## Optional: end-to-end orchestration using the spring-doc engine"
)

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


def _default_mode_text(text: str) -> str:
    """Contenido del modo por defecto: todo lo que precede a la seccion de
    orquestacion opcional. Ahi, y solo ahi, aplican las restricciones mas
    estrictas (sin CLI, sin nombres internos del proyecto)."""
    assert ORCHESTRATION_SECTION_MARKER in text, (
        "SKILL.md debe tener la seccion de orquestacion opcional (V0.9), "
        "claramente delimitada por su encabezado."
    )
    return text.split(ORCHESTRATION_SECTION_MARKER, 1)[0]


def _orchestration_section_text(text: str) -> str:
    assert ORCHESTRATION_SECTION_MARKER in text
    return text.split(ORCHESTRATION_SECTION_MARKER, 1)[1]


def test_skill_file_exists():
    assert SKILL_PATH.is_file()


def test_skill_frontmatter_has_name_and_description():
    frontmatter = _parse_frontmatter(_read_skill_text())
    assert frontmatter["name"] == "spring-doc"
    assert isinstance(frontmatter["description"], str)
    assert len(frontmatter["description"]) > 0


def test_skill_default_mode_does_not_reference_internal_project_structure():
    default_mode = _default_mode_text(_read_skill_text())
    for reference in INTERNAL_PROJECT_REFERENCES:
        assert reference not in default_mode, (
            f"SKILL.md (modo por defecto) menciona '{reference}' -- no debe describir "
            "la arquitectura interna de spring-doc (providers/analyzer/generators/"
            "validator/cli) fuera de la seccion de orquestacion opcional."
        )


def test_skill_default_mode_does_not_document_cli_syntax():
    default_mode = _default_mode_text(_read_skill_text())
    for token in CLI_SPECIFIC_TOKENS:
        assert token not in default_mode, (
            f"SKILL.md (modo por defecto) contiene '{token}' -- la sintaxis de la CLI "
            "spring-doc solo puede aparecer dentro de la seccion de orquestacion opcional."
        )


def test_skill_orchestration_section_may_reference_the_cli_and_public_api():
    """Confirma que la seccion opcional SI puede (y de hecho hace) referenciar
    la CLI y las abstracciones publicas del motor -- es su proposito
    explicito, a diferencia del modo por defecto."""
    orchestration = _orchestration_section_text(_read_skill_text())
    assert "spring-doc analyze" in orchestration
    assert "spring-doc generate" in orchestration
    assert "spring-doc validate" in orchestration
    assert "ProviderConfig" in orchestration
    assert "get_provider" in orchestration


def test_skill_orchestration_section_is_explicitly_optional_and_has_fallback():
    orchestration = _orchestration_section_text(_read_skill_text()).lower()
    assert "optional" in orchestration
    assert "fallback" in orchestration
    assert "never required" in orchestration or "not required" in orchestration or (
        "neither is required" in orchestration
    )


def test_skill_orchestration_section_never_names_a_concrete_llm_or_vendor():
    orchestration = _orchestration_section_text(_read_skill_text())
    for phrase in AGENT_OR_PROVIDER_SPECIFIC_PHRASES:
        assert phrase not in orchestration


def test_skill_orchestration_section_uses_neutral_language_for_the_llm():
    orchestration = _orchestration_section_text(_read_skill_text()).lower()
    assert "llm provider" in orchestration
    assert "the agent" in orchestration


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


def test_skill_requires_tracing_error_responses_not_just_success():
    text = _read_skill_text().lower()
    assert "error response" in text
    assert "only the success response" in text or "not just" in text or (
        "success path" in text
    )


def test_skill_requires_tags_and_summary_on_every_operation():
    text = _read_skill_text().lower()
    assert "tags" in text
    assert "summary" in text


def test_skill_distinguishes_fixed_vs_dynamic_catalog_fields():
    text = _read_skill_text().lower()
    assert "catalog" in text
    assert "hardcod" in text  # cubre "hardcode"/"hardcoding" en ambos casos


def test_skill_requires_field_level_descriptions_on_both_request_and_response():
    text = _read_skill_text().lower()
    assert "give every field a description" in text
    assert "response" in text and "request" in text


def test_skill_requires_verifying_security_is_actually_enforced():
    text = _read_skill_text().lower()
    assert "not currently enforced" in text or "not actually enforced" in text or (
        "disabled" in text
    )
    assert "prompts/" not in text
