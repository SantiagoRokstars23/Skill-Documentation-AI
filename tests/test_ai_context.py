"""Tests de ai/context.py (V0.8): DocumentationContextBuilder."""

from __future__ import annotations

import copy
from pathlib import Path

from ai import DocumentationContextBuilder
from analyzer import AnalysisResult, analyze_project

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"


def test_build_against_example_project_produces_expected_shape():
    result = analyze_project(EXAMPLE_PROJECT)
    context = DocumentationContextBuilder().build(result)

    assert len(context.endpoints) == len(result.endpoints)
    assert len(context.dtos) > 0
    assert all(isinstance(endpoint.id, str) and endpoint.id for endpoint in context.endpoints)


def test_build_is_deterministic():
    result = analyze_project(EXAMPLE_PROJECT)
    builder = DocumentationContextBuilder()

    first = builder.build(result).to_dict()
    second = builder.build(result).to_dict()

    assert first == second


def test_build_does_not_mutate_analysis_result():
    result = analyze_project(EXAMPLE_PROJECT)
    original = copy.deepcopy(result)

    DocumentationContextBuilder().build(result)

    assert result == original


def test_build_does_not_mutate_openapi_document():
    from generators import generate

    result = analyze_project(EXAMPLE_PROJECT)
    document, _ = generate(result)
    original_document = copy.deepcopy(document)

    DocumentationContextBuilder().build(result, document)

    assert document == original_document


def test_build_empty_project_yields_empty_context():
    empty_result = AnalysisResult()
    context = DocumentationContextBuilder().build(empty_result)

    assert context.endpoints == ()
    assert context.dtos == ()
    assert context.diagnostics_summary == ()


def test_project_name_is_never_derived_from_openapi_title():
    """El unico candidato ('info.title') es una convencion fija del Generator
    ('Generated API', V0.3), no evidencia real -- no debe usarse. Ver
    ai/context.py."""
    from generators import generate

    result = analyze_project(EXAMPLE_PROJECT)
    document, _ = generate(result)
    assert document["info"]["title"] == "Generated API"  # confirma la convencion fija

    context = DocumentationContextBuilder().build(result, document)
    assert context.project_name is None


def test_dtos_are_deduplicated_and_sorted_by_name():
    result = analyze_project(EXAMPLE_PROJECT)
    context = DocumentationContextBuilder().build(result)

    names = [dto.name for dto in context.dtos]
    assert names == sorted(names)
    assert len(names) == len(set(names))


def test_nested_dto_is_included():
    result = analyze_project(EXAMPLE_PROJECT)
    context = DocumentationContextBuilder().build(result)

    names = {dto.name for dto in context.dtos}
    assert "Address" in names  # DTO anidado dentro de CustomerRequest


def test_endpoint_id_collision_gets_disambiguated():
    from analyzer.models import Endpoint

    result = AnalysisResult(
        endpoints=[
            Endpoint(controller="C", endpoint="/x", method="GET"),
            Endpoint(controller="C", endpoint="/x", method="GET"),
        ]
    )
    context = DocumentationContextBuilder().build(result)

    ids = [endpoint.id for endpoint in context.endpoints]
    assert ids == ["GET /x", "GET /x #2"]


def test_request_dto_name_is_populated_for_body_parameter():
    result = analyze_project(EXAMPLE_PROJECT)
    context = DocumentationContextBuilder().build(result)

    endpoints_with_request_dto = [e for e in context.endpoints if e.request_dto_name]
    assert len(endpoints_with_request_dto) > 0


def test_diagnostics_summary_reflects_analyzer_diagnostics():
    result = analyze_project(EXAMPLE_PROJECT)
    context = DocumentationContextBuilder().build(result)

    assert len(context.diagnostics_summary) == len(result.diagnostics)
