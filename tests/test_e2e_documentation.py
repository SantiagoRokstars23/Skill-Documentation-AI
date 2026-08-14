"""Test de integracion end-to-end (V0.9): la cadena completa

    analyze_project() -> generate() -> DocumentationContextBuilder ->
    DocumentationEngine(FakeProvider-like) -> apply_documentation() -> validate()

contra examples/customer-service, sin Anthropic real, determinista. Ver
prompts/V0.9—SKILL-&-END-TO-END-DOCUMENTATION.md secciones 19 y 31.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai import (
    DocumentationContextBuilder,
    DocumentationEngine,
    DocumentationPromptBuilder,
    apply_documentation,
)
from analyzer import analyze_project
from generators import generate, to_yaml
from providers import LLMProvider
from validator import validate

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"


class _DeterministicProvider(LLMProvider):
    """Responde de forma valida y determinista a cualquier prompt de proyecto
    o de endpoint, sin usar Internet ni depender de un LLM real -- mismo rol
    que un FakeProvider mas elaborado, sin ampliar FakeProvider en si (V0.8
    seccion 19: se puede usar un doble de prueba local en vez de complicar
    FakeProvider)."""

    def generate(self, prompt: str) -> str:
        if "descripcion general de este proyecto" in prompt:
            return json.dumps({"project_description": "Servicio de gestion de clientes."})
        return json.dumps(
            {
                "summary": "Resumen generado deterministicamente",
                "endpoint_description": "",
                "parameters": {},
                "request_description": None,
                "responses": {},
                "dtos": {},
            }
        )


def _run_end_to_end():
    analysis_result = analyze_project(EXAMPLE_PROJECT)
    document, generator_diagnostics = generate(analysis_result)
    context = DocumentationContextBuilder().build(analysis_result)

    engine = DocumentationEngine(
        _DeterministicProvider(), DocumentationContextBuilder(), DocumentationPromptBuilder()
    )
    documentation_result = engine.generate(analysis_result)

    enriched_document, enrichment_diagnostics = apply_documentation(
        document, documentation_result, context
    )
    final_diagnostics = validate(enriched_document)

    return {
        "analysis_result": analysis_result,
        "document": document,
        "generator_diagnostics": generator_diagnostics,
        "documentation_result": documentation_result,
        "enriched_document": enriched_document,
        "enrichment_diagnostics": enrichment_diagnostics,
        "final_diagnostics": final_diagnostics,
    }


def test_end_to_end_chain_produces_a_valid_enriched_document():
    outcome = _run_end_to_end()

    assert len(outcome["analysis_result"].endpoints) > 0
    assert outcome["enriched_document"]["info"]["description"] == "Servicio de gestion de clientes."

    errors = [d for d in outcome["final_diagnostics"] if d.severity.value == "ERROR"]
    assert errors == []


def test_end_to_end_chain_does_not_introduce_new_validator_errors():
    outcome = _run_end_to_end()

    base_errors = [d for d in validate(outcome["document"]) if d.severity.value == "ERROR"]
    enriched_errors = [d for d in outcome["final_diagnostics"] if d.severity.value == "ERROR"]

    assert len(enriched_errors) <= len(base_errors)


def test_end_to_end_chain_is_deterministic():
    first = _run_end_to_end()
    second = _run_end_to_end()

    assert first["enriched_document"] == second["enriched_document"]
    assert first["documentation_result"].to_dict() == second["documentation_result"].to_dict()


def test_end_to_end_chain_original_base_document_unchanged():
    analysis_result = analyze_project(EXAMPLE_PROJECT)
    document, _ = generate(analysis_result)
    document_before = to_yaml(document)

    outcome = _run_end_to_end()

    assert to_yaml(outcome["document"]) == document_before


def test_end_to_end_chain_preserves_paths_and_operations_exactly():
    outcome = _run_end_to_end()

    assert set(outcome["enriched_document"]["paths"].keys()) == set(outcome["document"]["paths"].keys())
    for path, methods in outcome["document"]["paths"].items():
        assert set(outcome["enriched_document"]["paths"][path].keys()) == set(methods.keys())
