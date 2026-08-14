"""Tests de ai/prompts.py (V0.8): DocumentationPromptBuilder."""

from __future__ import annotations

from pathlib import Path

from ai import DocumentationContextBuilder, DocumentationPromptBuilder
from ai.errors import DocumentationError
from analyzer import analyze_project

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"


def _context():
    result = analyze_project(EXAMPLE_PROJECT)
    return DocumentationContextBuilder().build(result)


def test_project_prompt_contains_expected_context():
    context = _context()
    prompt = DocumentationPromptBuilder().build_project_prompt(context)

    assert str(len(context.endpoints)) in prompt
    for endpoint in context.endpoints:
        assert endpoint.id in prompt


def test_endpoint_prompt_contains_expected_context():
    context = _context()
    endpoint = context.endpoints[0]
    prompt = DocumentationPromptBuilder().build_endpoint_prompt(context, endpoint.id)

    assert endpoint.id in prompt
    assert endpoint.path in prompt


def test_endpoint_prompt_includes_referenced_dtos():
    context = _context()
    endpoint = next(e for e in context.endpoints if e.request_dto_name)
    prompt = DocumentationPromptBuilder().build_endpoint_prompt(context, endpoint.id)

    assert endpoint.request_dto_name in prompt


def test_endpoint_prompt_includes_nested_dtos():
    """Regresion (hallazgo de revision de codigo en Fase 5): Address esta
    anidado dentro de CustomerRequest en examples/customer-service; el prompt
    del endpoint que recibe CustomerRequest debe incluir tambien Address, no
    solo el DTO referenciado directamente."""
    context = _context()
    endpoint = next(e for e in context.endpoints if e.request_dto_name == "CustomerRequest")
    prompt = DocumentationPromptBuilder().build_endpoint_prompt(context, endpoint.id)

    assert '"name": "Address"' in prompt


def test_endpoint_prompt_unknown_id_raises():
    context = _context()
    try:
        DocumentationPromptBuilder().build_endpoint_prompt(context, "DOES-NOT-EXIST")
    except DocumentationError:
        pass
    else:
        raise AssertionError("se esperaba DocumentationError")


def test_prompts_contain_anti_hallucination_rules():
    context = _context()
    builder = DocumentationPromptBuilder()
    project_prompt = builder.build_project_prompt(context)
    endpoint_prompt = builder.build_endpoint_prompt(context, context.endpoints[0].id)

    for prompt in (project_prompt, endpoint_prompt):
        assert "No inventes" in prompt
        assert "No determinado por el analisis" in prompt


def test_prompts_are_deterministic():
    context = _context()
    builder = DocumentationPromptBuilder()

    first = builder.build_project_prompt(context)
    second = builder.build_project_prompt(context)
    assert first == second

    endpoint_id = context.endpoints[0].id
    first_ep = builder.build_endpoint_prompt(context, endpoint_id)
    second_ep = builder.build_endpoint_prompt(context, endpoint_id)
    assert first_ep == second_ep


def test_prompts_contain_no_unexpected_secret_looking_values():
    context = _context()
    builder = DocumentationPromptBuilder()
    prompt = builder.build_project_prompt(context)

    lowered = prompt.lower()
    for suspicious in ("api_key", "sk-ant-", "sk-proj-", "bearer "):
        assert suspicious not in lowered


def test_endpoint_prompt_requests_json_only_response():
    context = _context()
    prompt = DocumentationPromptBuilder().build_endpoint_prompt(context, context.endpoints[0].id)
    assert "JSON" in prompt


def test_endpoint_prompt_requests_summary_field():
    context = _context()
    prompt = DocumentationPromptBuilder().build_endpoint_prompt(context, context.endpoints[0].id)
    assert '"summary"' in prompt
