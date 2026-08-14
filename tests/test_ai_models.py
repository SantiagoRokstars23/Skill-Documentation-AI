"""Tests de ai/models.py (V0.8): inmutabilidad, serializacion, campos."""

from __future__ import annotations

import dataclasses
import json

import pytest

from ai import (
    DTOContext,
    DTODocumentation,
    DTOFieldContext,
    DocumentationContext,
    DocumentationResult,
    EndpointContext,
    EndpointDocumentation,
    ParameterContext,
    ParameterDocumentation,
    ResponseContext,
    ResponseDocumentation,
)


def test_documentation_context_is_immutable():
    context = DocumentationContext(project_name=None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.project_name = "x"  # type: ignore[misc]


def test_documentation_result_is_immutable():
    result = DocumentationResult(project_description=None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.project_description = "x"  # type: ignore[misc]


def test_endpoint_context_and_nested_dataclasses_are_immutable():
    endpoint = EndpointContext(id="GET /x", controller="C", method="GET", path="/x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        endpoint.controller = "other"  # type: ignore[misc]


def test_documentation_context_defaults_are_empty_tuples():
    context = DocumentationContext(project_name=None)
    assert context.endpoints == ()
    assert context.dtos == ()
    assert context.diagnostics_summary == ()


def test_documentation_result_defaults_are_empty_tuples():
    result = DocumentationResult(project_description=None)
    assert result.endpoints == ()
    assert result.dtos == ()
    assert result.diagnostics == ()


def test_documentation_context_to_dict_is_json_serializable():
    context = DocumentationContext(
        project_name=None,
        endpoints=(
            EndpointContext(
                id="GET /x",
                controller="C",
                method="GET",
                path="/x",
                parameters=(
                    ParameterContext(
                        name="id", source="path", type="Long", required=True, default_value=None
                    ),
                ),
                responses=(
                    ResponseContext(status="200", body_type="X", is_collection=False, dto_name="X"),
                ),
            ),
        ),
        dtos=(
            DTOContext(
                name="X",
                kind="class",
                fields=(DTOFieldContext(name="id", type="Long", is_collection=False),),
            ),
        ),
        diagnostics_summary=("INFO: algo",),
    )
    json.dumps(context.to_dict())  # no debe lanzar


def test_documentation_context_to_json_is_deterministic():
    context = DocumentationContext(project_name=None, diagnostics_summary=("a", "b"))
    assert context.to_json() == context.to_json()


def test_get_endpoint_found_and_not_found():
    context = DocumentationContext(
        project_name=None,
        endpoints=(EndpointContext(id="GET /x", controller="C", method="GET", path="/x"),),
    )
    assert context.get_endpoint("GET /x") is not None
    assert context.get_endpoint("DOES-NOT-EXIST") is None


def test_get_dto_found_and_not_found():
    context = DocumentationContext(
        project_name=None,
        dtos=(DTOContext(name="X", kind="class"),),
    )
    assert context.get_dto("X") is not None
    assert context.get_dto("Missing") is None


def test_documentation_result_to_dict_is_json_serializable():
    result = DocumentationResult(
        project_description="desc",
        endpoints=(
            EndpointDocumentation(
                endpoint_id="GET /x",
                description="desc",
                parameters=(ParameterDocumentation(name="id", description="el id"),),
                request_description=None,
                responses=(ResponseDocumentation(status="200", description="ok"),),
            ),
        ),
        dtos=(DTODocumentation(name="X", description="desc"),),
        diagnostics=("nota",),
    )
    parsed = json.loads(result.to_json())
    assert parsed["project_description"] == "desc"
    assert parsed["endpoints"][0]["endpoint_id"] == "GET /x"
    assert parsed["dtos"][0]["name"] == "X"


def test_referenced_dto_names_direct_only():
    endpoint = EndpointContext(id="GET /x", controller="C", method="GET", path="/x", request_dto_name="A")
    context = DocumentationContext(project_name=None, dtos=(DTOContext(name="A", kind="class"),))

    assert context.referenced_dto_names(endpoint) == frozenset({"A"})


def test_referenced_dto_names_resolves_nested_dtos_transitively():
    """Regresion (hallazgo de revision de codigo, Fase 5 de V0.8): un DTO
    anidado dentro de otro DTO (via DTOFieldContext.nested_dto_name) debe
    resolverse tambien, no solo el DTO referenciado directamente por el
    endpoint."""
    endpoint = EndpointContext(id="GET /x", controller="C", method="GET", path="/x", request_dto_name="A")
    context = DocumentationContext(
        project_name=None,
        dtos=(
            DTOContext(
                name="A",
                kind="class",
                fields=(DTOFieldContext(name="b", type="B", is_collection=False, nested_dto_name="B"),),
            ),
            DTOContext(
                name="B",
                kind="class",
                fields=(DTOFieldContext(name="c", type="C", is_collection=False, nested_dto_name="C"),),
            ),
            DTOContext(name="C", kind="class"),
        ),
    )

    assert context.referenced_dto_names(endpoint) == frozenset({"A", "B", "C"})


def test_referenced_dto_names_handles_cycles_without_looping_forever():
    endpoint = EndpointContext(id="GET /x", controller="C", method="GET", path="/x", request_dto_name="A")
    context = DocumentationContext(
        project_name=None,
        dtos=(
            DTOContext(
                name="A",
                kind="class",
                fields=(DTOFieldContext(name="b", type="B", is_collection=False, nested_dto_name="B"),),
            ),
            DTOContext(
                name="B",
                kind="class",
                fields=(DTOFieldContext(name="a", type="A", is_collection=False, nested_dto_name="A"),),
            ),
        ),
    )

    assert context.referenced_dto_names(endpoint) == frozenset({"A", "B"})
