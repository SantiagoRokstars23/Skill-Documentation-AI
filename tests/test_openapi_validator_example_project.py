"""Tests del Validator V0.4: parseo JSON/YAML, integracion con examples/customer-service,
determinismo e inmutabilidad."""

import copy
import json
from pathlib import Path

from analyzer import analyze_project
from generators import generate, to_json, to_yaml
from validator import validate, validate_json, validate_yaml

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"


def _generate_example_document():
    result = analyze_project(EXAMPLE_PROJECT)
    document, _ = generate(result)
    return document


# ---------------------------------------------------------------------------
# Parseo
# ---------------------------------------------------------------------------


def test_validate_json_valid():
    document = _generate_example_document()
    diagnostics = validate_json(to_json(document))
    assert diagnostics == validate(document)


def test_validate_json_invalid_returns_parse_error_without_raising():
    diagnostics = validate_json("{not valid json")
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "OPENAPI_JSON_PARSE_ERROR"
    assert diagnostics[0].severity.value == "ERROR"


def test_validate_yaml_valid():
    document = _generate_example_document()
    diagnostics = validate_yaml(to_yaml(document))
    assert diagnostics == validate(document)


def test_validate_yaml_invalid_returns_parse_error_without_raising():
    diagnostics = validate_yaml("key: [unbalanced")
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "OPENAPI_YAML_PARSE_ERROR"
    assert diagnostics[0].severity.value == "ERROR"


def test_json_and_yaml_produce_equivalent_results():
    document = _generate_example_document()
    from_json = validate_json(to_json(document))
    from_yaml = validate_yaml(to_yaml(document))
    assert [(d.severity, d.code, d.message, d.evidence) for d in from_json] == [
        (d.severity, d.code, d.message, d.evidence) for d in from_yaml
    ]


def test_validate_yaml_empty_document_does_not_raise():
    diagnostics = validate_yaml("")
    assert diagnostics[0].code == "OPENAPI_DOCUMENT_NOT_OBJECT"


# ---------------------------------------------------------------------------
# Integracion con examples/customer-service
# ---------------------------------------------------------------------------


def test_example_project_validates_without_raising():
    document = _generate_example_document()
    diagnostics = validate(document)
    assert isinstance(diagnostics, list)


def test_example_project_has_no_errors():
    # El documento generado por V0.3 es estructuralmente sano por construccion
    # (ver reporte de Fase 1 de V0.4): se esperan WARNING/INFO, pero cero ERROR.
    document = _generate_example_document()
    diagnostics = validate(document)
    errors = [d for d in diagnostics if d.severity.value == "ERROR"]
    assert errors == []


def test_example_project_diagnostics_are_deterministic_and_match_expected_codes():
    document = _generate_example_document()
    diagnostics = validate(document)
    from collections import Counter

    by_code = Counter(d.code for d in diagnostics)
    # El ejemplo nunca declara 'description' en operaciones/schemas/responses, ni
    # 'security'/'securitySchemes' reales; y sus valores de info/response coinciden
    # con los placeholders/boilerplate fijos del Generator V0.3.
    assert by_code["OPENAPI_OPERATION_MISSING_DESCRIPTION"] > 0
    assert by_code["OPENAPI_SCHEMA_MISSING_DESCRIPTION"] > 0
    assert by_code["OPENAPI_RESPONSE_MISSING_DESCRIPTION"] == 0  # todas usan el texto fijo -> otra regla
    assert by_code["OPENAPI_GENERATOR_DEFAULT_RESPONSE_DESCRIPTION"] > 0
    assert by_code["OPENAPI_GENERATOR_PLACEHOLDER_INFO"] == 2
    assert by_code["OPENAPI_SECURITY_EXTENSION_ONLY"] == 1
    assert by_code["OPENAPI_OPERATION_NO_SECURITY"] > 0
    assert by_code["OPENAPI_SCHEMA_UNREFERENCED"] == 0
    assert "OPENAPI_REF_NOT_FOUND" not in by_code


def test_example_project_does_not_modify_document():
    document = _generate_example_document()
    snapshot = copy.deepcopy(document)
    validate(document)
    assert document == snapshot


def test_example_project_deterministic_across_repeated_calls():
    document = _generate_example_document()
    first = validate(document)
    second = validate(document)
    third = validate(document)
    key = lambda diags: [(d.severity, d.code, d.message, d.evidence) for d in diags]  # noqa: E731
    assert key(first) == key(second) == key(third)


# ---------------------------------------------------------------------------
# Determinismo ante distinto orden de insercion del dict de entrada
# ---------------------------------------------------------------------------


def test_deterministic_regardless_of_input_dict_key_order():
    paths = {
        "/a": {"get": {"operationId": "getA", "responses": {"200": {"description": "ok"}}}},
        "/b": {"post": {"operationId": "postB", "responses": {"200": {"description": "ok"}}}},
    }
    doc_forward = {"openapi": "3.0.3", "info": {"title": "X", "version": "1"}, "paths": paths}
    doc_reversed = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": dict(reversed(list(paths.items()))),
    }
    key = lambda diags: [(d.severity, d.code, d.evidence.file if d.evidence else None) for d in diags]  # noqa: E731
    assert key(validate(doc_forward)) == key(validate(doc_reversed))


# ---------------------------------------------------------------------------
# Inmutabilidad general (seccion 28 de la directriz)
# ---------------------------------------------------------------------------


def test_immutability_generic_document():
    document = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {
            "/x": {
                "get": {
                    "operationId": "getX",
                    "parameters": [{"name": "q", "in": "query", "required": False, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
        "components": {"schemas": {"Foo": {"type": "object", "properties": {}}}},
    }
    original = copy.deepcopy(document)
    validate(document)
    assert document == original
