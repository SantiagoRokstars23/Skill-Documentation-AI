"""Tests de ai/parsing.py (V0.8): parseo y validacion de la respuesta del LLM."""

from __future__ import annotations

import json

import pytest

from ai.errors import DocumentationParseError
from ai.models import (
    DTOContext,
    DTOFieldContext,
    DocumentationContext,
    EndpointContext,
    ParameterContext,
    ResponseContext,
)
from ai.parsing import parse_endpoint_response, parse_project_response, status_label


def _endpoint(**overrides) -> EndpointContext:
    defaults = dict(id="GET /x", controller="C", method="GET", path="/x")
    defaults.update(overrides)
    return EndpointContext(**defaults)


def _context(*, dtos: tuple[DTOContext, ...] = (), endpoint: EndpointContext | None = None):
    return DocumentationContext(
        project_name=None,
        endpoints=(endpoint,) if endpoint is not None else (),
        dtos=dtos,
    )


def _endpoint_payload(**overrides) -> dict:
    payload = {
        "endpoint_description": "desc",
        "parameters": {},
        "request_description": None,
        "responses": {},
        "dtos": {},
    }
    payload.update(overrides)
    return payload


# --- project response -------------------------------------------------


def test_parse_project_response_valid():
    raw = json.dumps({"project_description": "una API de ejemplo"})
    assert parse_project_response(raw) == "una API de ejemplo"


def test_parse_project_response_strips_markdown_fence():
    raw = "```json\n" + json.dumps({"project_description": "ok"}) + "\n```"
    assert parse_project_response(raw) == "ok"


def test_parse_project_response_strips_fence_without_language_tag():
    raw = "```\n" + json.dumps({"project_description": "ok"}) + "\n```"
    assert parse_project_response(raw) == "ok"


def test_parse_project_response_invalid_json_raises():
    with pytest.raises(DocumentationParseError):
        parse_project_response("esto no es json")


def test_parse_project_response_non_object_json_raises():
    with pytest.raises(DocumentationParseError):
        parse_project_response(json.dumps(["a", "b"]))


def test_parse_project_response_missing_key_raises():
    with pytest.raises(DocumentationParseError):
        parse_project_response(json.dumps({}))


def test_parse_project_response_wrong_type_raises():
    with pytest.raises(DocumentationParseError):
        parse_project_response(json.dumps({"project_description": 123}))


def test_parse_project_response_partial_fence_is_not_stripped_and_fails():
    # Un fence que no envuelve TODO el string no se toca -- debe fallar el
    # parseo (nunca se busca contenido embebido).
    raw = "prefijo ```json\n" + json.dumps({"project_description": "ok"}) + "\n```"
    with pytest.raises(DocumentationParseError):
        parse_project_response(raw)


# --- endpoint response --------------------------------------------------


def test_parse_endpoint_response_valid_minimal():
    endpoint = _endpoint()
    raw = json.dumps(_endpoint_payload())

    doc, dtos = parse_endpoint_response(raw, _context(), endpoint)

    assert doc.endpoint_id == "GET /x"
    assert doc.description == "desc"
    assert doc.parameters == ()
    assert doc.request_description is None
    assert doc.responses == ()
    assert dtos == ()


def test_parse_endpoint_response_with_known_parameter():
    endpoint = _endpoint(
        parameters=(ParameterContext(name="id", source="path", type="Long", required=True, default_value=None),)
    )
    raw = json.dumps(_endpoint_payload(parameters={"id": "el identificador"}))

    doc, _ = parse_endpoint_response(raw, _context(), endpoint)

    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "id"
    assert doc.parameters[0].description == "el identificador"


def test_parse_endpoint_response_unknown_parameter_raises():
    endpoint = _endpoint()
    raw = json.dumps(_endpoint_payload(parameters={"inventado": "x"}))

    with pytest.raises(DocumentationParseError, match="inventado"):
        parse_endpoint_response(raw, _context(), endpoint)


def test_parse_endpoint_response_unknown_response_status_raises():
    endpoint = _endpoint(responses=(ResponseContext(status="200", body_type="X", is_collection=False, dto_name=None),))
    raw = json.dumps(_endpoint_payload(responses={"404": "no encontrado"}))

    with pytest.raises(DocumentationParseError):
        parse_endpoint_response(raw, _context(), endpoint)


def test_parse_endpoint_response_known_response_status_accepted():
    endpoint = _endpoint(responses=(ResponseContext(status="200", body_type="X", is_collection=False, dto_name=None),))
    raw = json.dumps(_endpoint_payload(responses={"200": "ok"}))

    doc, _ = parse_endpoint_response(raw, _context(), endpoint)

    assert doc.responses == (doc.responses[0],)
    assert doc.responses[0].status == "200"


def test_parse_endpoint_response_null_status_uses_unknown_label():
    endpoint = _endpoint(responses=(ResponseContext(status=None, body_type="X", is_collection=False, dto_name=None),))
    assert status_label(None) == "unknown"
    raw = json.dumps(_endpoint_payload(responses={"unknown": "sin status conocido"}))

    doc, _ = parse_endpoint_response(raw, _context(), endpoint)

    assert doc.responses[0].status == "unknown"


def test_parse_endpoint_response_unknown_dto_raises():
    endpoint = _endpoint(request_dto_name="CustomerRequest")
    context = _context(dtos=(DTOContext(name="CustomerRequest", kind="class"),))
    raw = json.dumps(_endpoint_payload(dtos={"NoExiste": "x"}))

    with pytest.raises(DocumentationParseError):
        parse_endpoint_response(raw, context, endpoint)


def test_parse_endpoint_response_known_dto_accepted_and_returned_separately():
    endpoint = _endpoint(request_dto_name="CustomerRequest")
    context = _context(dtos=(DTOContext(name="CustomerRequest", kind="class"),))
    raw = json.dumps(_endpoint_payload(dtos={"CustomerRequest": "un cliente"}))

    doc, dtos = parse_endpoint_response(raw, context, endpoint)

    assert dtos == (dtos[0],)
    assert dtos[0].name == "CustomerRequest"
    assert dtos[0].description == "un cliente"


def test_parse_endpoint_response_nested_dto_is_accepted():
    """Regresion (hallazgo de revision de codigo en Fase 5): un DTO anidado
    dentro de otro DTO (p. ej. Address dentro de CustomerRequest) debe
    aceptarse en 'dtos', no rechazarse como alucinacion, porque
    DocumentationContext.referenced_dto_names lo resuelve transitivamente."""
    endpoint = _endpoint(request_dto_name="CustomerRequest")
    context = _context(
        dtos=(
            DTOContext(
                name="CustomerRequest",
                kind="class",
                fields=(
                    DTOFieldContext(
                        name="address", type="Address", is_collection=False, nested_dto_name="Address"
                    ),
                ),
            ),
            DTOContext(name="Address", kind="class"),
        )
    )
    raw = json.dumps(
        _endpoint_payload(dtos={"CustomerRequest": "un cliente", "Address": "una direccion"})
    )

    doc, dtos = parse_endpoint_response(raw, context, endpoint)

    names = {dto.name for dto in dtos}
    assert names == {"CustomerRequest", "Address"}


def test_parse_endpoint_response_missing_key_raises():
    endpoint = _endpoint()
    payload = _endpoint_payload()
    del payload["endpoint_description"]

    with pytest.raises(DocumentationParseError):
        parse_endpoint_response(json.dumps(payload), _context(), endpoint)


def test_parse_endpoint_response_wrong_value_type_raises():
    endpoint = _endpoint()
    raw = json.dumps(_endpoint_payload(endpoint_description=123))

    with pytest.raises(DocumentationParseError):
        parse_endpoint_response(raw, _context(), endpoint)


def test_parse_endpoint_response_request_description_allows_null():
    endpoint = _endpoint()
    raw = json.dumps(_endpoint_payload(request_description=None))

    doc, _ = parse_endpoint_response(raw, _context(), endpoint)

    assert doc.request_description is None


def test_parse_endpoint_response_request_description_string():
    endpoint = _endpoint()
    raw = json.dumps(_endpoint_payload(request_description="cuerpo esperado"))

    doc, _ = parse_endpoint_response(raw, _context(), endpoint)

    assert doc.request_description == "cuerpo esperado"


def test_parse_endpoint_response_invalid_json_raises():
    with pytest.raises(DocumentationParseError):
        parse_endpoint_response("no es json", _context(), _endpoint())
