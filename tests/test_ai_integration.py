"""Test de integracion end-to-end (V0.8, seccion 31): analyze_project() ->
DocumentationContextBuilder -> DocumentationPromptBuilder -> FakeProvider ->
DocumentationResult, contra examples/customer-service. Sin Anthropic real."""

from __future__ import annotations

import json
from pathlib import Path

from ai import DocumentationContextBuilder, DocumentationEngine, DocumentationPromptBuilder
from analyzer import analyze_project
from providers import FakeProvider

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"

# examples/customer-service tiene endpoints con parametros/DTOs/responses;
# FakeProvider solo soporta una respuesta fija (V0.6), asi que la respuesta
# elegida cubre el "molde" mas exigente (schema de endpoint) para demostrar
# que el flujo real end-to-end tolera una respuesta sin parametros/dtos/
# responses conocidos declarados (el caso valido mas simple del schema).
_FIXED_RESPONSE = json.dumps(
    {
        "project_description": "N/A",
        "summary": "N/A",
        "endpoint_description": "N/A",
        "parameters": {},
        "request_description": None,
        "responses": {},
        "dtos": {},
    }
)


def test_end_to_end_flow_with_fake_provider_is_deterministic():
    analysis_result = analyze_project(EXAMPLE_PROJECT)
    assert len(analysis_result.endpoints) > 0

    engine = DocumentationEngine(
        FakeProvider(response=_FIXED_RESPONSE),
        DocumentationContextBuilder(),
        DocumentationPromptBuilder(),
    )

    first = engine.generate(analysis_result)
    second = engine.generate(analysis_result)

    assert first.to_dict() == second.to_dict()
    assert len(first.endpoints) == len(analysis_result.endpoints)
    assert first.project_description == "N/A"


def test_end_to_end_result_is_json_serializable():
    analysis_result = analyze_project(EXAMPLE_PROJECT)
    engine = DocumentationEngine(
        FakeProvider(response=_FIXED_RESPONSE),
        DocumentationContextBuilder(),
        DocumentationPromptBuilder(),
    )

    result = engine.generate(analysis_result)

    json.loads(result.to_json())  # no debe lanzar
