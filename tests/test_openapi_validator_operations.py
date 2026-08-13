"""Tests del Validator V0.4: parameters, requestBody, responses, status codes."""

from validator import validate


def _doc_with_operation(operation, extra_paths=None):
    paths = {"/x/{id}": {"get": {"operationId": "getX", **operation}}}
    if extra_paths:
        paths.update(extra_paths)
    return {"openapi": "3.0.3", "info": {"title": "Test API", "version": "1.0.0"}, "paths": paths}


def _codes(document):
    return [d.code for d in validate(document)]


def _param(name, location, **overrides):
    base = {"name": name, "in": location, "required": location == "path", "schema": {"type": "string"}}
    base.update(overrides)
    return base


_OK_RESPONSES = {"200": {"description": "ok"}}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


def test_path_parameter_valid():
    doc = _doc_with_operation({"parameters": [_param("id", "path")], "responses": _OK_RESPONSES})
    assert not any(c.startswith("OPENAPI_PARAMETER") or c.startswith("OPENAPI_PATH_PARAMETER") for c in _codes(doc))


def test_query_parameter_valid():
    doc = _doc_with_operation(
        {"parameters": [_param("id", "path"), _param("q", "query", required=False)], "responses": _OK_RESPONSES}
    )
    codes = _codes(doc)
    assert "OPENAPI_PARAMETER_MISSING_NAME" not in codes
    assert "OPENAPI_PARAMETER_INVALID_IN" not in codes


def test_header_parameter_valid():
    doc = _doc_with_operation(
        {"parameters": [_param("id", "path"), _param("X-Trace", "header", required=False)], "responses": _OK_RESPONSES}
    )
    assert "OPENAPI_PARAMETER_INVALID_IN" not in _codes(doc)


def test_cookie_parameter_valid():
    doc = _doc_with_operation(
        {"parameters": [_param("id", "path"), _param("session", "cookie", required=False)], "responses": _OK_RESPONSES}
    )
    assert "OPENAPI_PARAMETER_INVALID_IN" not in _codes(doc)


def test_parameter_invalid_in():
    doc = _doc_with_operation(
        {"parameters": [_param("id", "path"), _param("q", "body", required=False)], "responses": _OK_RESPONSES}
    )
    assert "OPENAPI_PARAMETER_INVALID_IN" in _codes(doc)


def test_parameter_missing_name():
    doc = _doc_with_operation(
        {"parameters": [_param("id", "path"), {"in": "query", "schema": {"type": "string"}}], "responses": _OK_RESPONSES}
    )
    assert "OPENAPI_PARAMETER_MISSING_NAME" in _codes(doc)


def test_parameter_missing_in():
    doc = _doc_with_operation(
        {"parameters": [_param("id", "path"), {"name": "q", "schema": {"type": "string"}}], "responses": _OK_RESPONSES}
    )
    assert "OPENAPI_PARAMETER_MISSING_IN" in _codes(doc)


def test_path_parameter_not_required_is_error():
    doc = _doc_with_operation(
        {"parameters": [_param("id", "path", required=False)], "responses": _OK_RESPONSES}
    )
    assert "OPENAPI_PATH_PARAMETER_NOT_REQUIRED" in _codes(doc)


def test_parameter_duplicate_same_scope():
    doc = _doc_with_operation(
        {
            "parameters": [
                _param("id", "path"),
                _param("q", "query", required=False),
                _param("q", "query", required=False),
            ],
            "responses": _OK_RESPONSES,
        }
    )
    assert "OPENAPI_PARAMETER_DUPLICATE" in _codes(doc)


def test_parameter_missing_schema_and_content():
    doc = _doc_with_operation(
        {"parameters": [_param("id", "path"), {"name": "q", "in": "query"}], "responses": _OK_RESPONSES}
    )
    assert "OPENAPI_PARAMETER_MISSING_SCHEMA" in _codes(doc)


def test_parameter_schema_and_content_conflict():
    doc = _doc_with_operation(
        {
            "parameters": [
                _param("id", "path"),
                {"name": "q", "in": "query", "schema": {"type": "string"}, "content": {"application/json": {}}},
            ],
            "responses": _OK_RESPONSES,
        }
    )
    assert "OPENAPI_PARAMETER_SCHEMA_CONTENT_CONFLICT" in _codes(doc)


# ---------------------------------------------------------------------------
# Request body
# ---------------------------------------------------------------------------


def test_request_body_valid():
    doc = _doc_with_operation(
        {
            "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "string"}}}},
            "responses": _OK_RESPONSES,
        }
    )
    assert not any(c.startswith("OPENAPI_REQUEST_BODY") for c in _codes(doc))


def test_request_body_missing_content():
    doc = _doc_with_operation({"requestBody": {"required": True}, "responses": _OK_RESPONSES})
    assert "OPENAPI_REQUEST_BODY_MISSING_CONTENT" in _codes(doc)


def test_request_body_content_empty():
    doc = _doc_with_operation({"requestBody": {"content": {}}, "responses": _OK_RESPONSES})
    assert "OPENAPI_REQUEST_BODY_INVALID" in _codes(doc)


def test_request_body_not_an_object():
    doc = _doc_with_operation({"requestBody": "not-an-object", "responses": _OK_RESPONSES})
    assert "OPENAPI_REQUEST_BODY_INVALID" in _codes(doc)


def test_request_body_schema_invalid_type_reported():
    doc = _doc_with_operation(
        {
            "requestBody": {"content": {"application/json": {"schema": {"type": "not-a-real-type"}}}},
            "responses": _OK_RESPONSES,
        }
    )
    assert "OPENAPI_INVALID_SCHEMA_TYPE" in _codes(doc)


def test_request_body_never_assumes_application_json_media_type():
    # El Validator no debe inventar ningun media type: si 'content' existe pero con
    # otro tipo, no debe reclamar nada sobre 'application/json'.
    doc = _doc_with_operation(
        {
            "requestBody": {"content": {"application/xml": {"schema": {"type": "string"}}}},
            "responses": _OK_RESPONSES,
        }
    )
    diagnostics = validate(doc)
    assert not any("application/json" in d.message for d in diagnostics)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


def test_response_valid():
    doc = _doc_with_operation({"responses": {"200": {"description": "ok"}}})
    assert not any(c.startswith("OPENAPI_RESPONSE") or c == "OPENAPI_MISSING_RESPONSES" for c in _codes(doc) if c != "OPENAPI_RESPONSE_MISSING_DESCRIPTION")


def test_responses_missing_is_error():
    doc = _doc_with_operation({})
    assert "OPENAPI_MISSING_RESPONSES" in _codes(doc)


def test_response_missing_description_is_warning():
    doc = _doc_with_operation({"responses": {"200": {}}})
    diagnostics = validate(doc)
    finding = next(d for d in diagnostics if d.code == "OPENAPI_RESPONSE_MISSING_DESCRIPTION")
    assert finding.severity.value == "WARNING"


def test_invalid_status_code_key():
    doc = _doc_with_operation({"responses": {"2xx": {"description": "ok"}}})
    assert "OPENAPI_INVALID_STATUS_CODE" in _codes(doc)


def test_default_status_key_is_valid():
    doc = _doc_with_operation({"responses": {"default": {"description": "ok"}}})
    assert "OPENAPI_INVALID_STATUS_CODE" not in _codes(doc)


def test_three_digit_status_code_is_valid():
    doc = _doc_with_operation({"responses": {"404": {"description": "not found"}}})
    assert "OPENAPI_INVALID_STATUS_CODE" not in _codes(doc)


def test_response_array_schema_missing_items():
    doc = _doc_with_operation(
        {
            "responses": {
                "200": {
                    "description": "ok",
                    "content": {"application/json": {"schema": {"type": "array"}}},
                }
            }
        }
    )
    assert "OPENAPI_ARRAY_ITEMS_MISSING" in _codes(doc)


def test_response_headers_invalid_type():
    doc = _doc_with_operation({"responses": {"200": {"description": "ok", "headers": "not-an-object"}}})
    assert "OPENAPI_RESPONSE_HEADERS_INVALID" in _codes(doc)


def test_response_links_invalid_type():
    doc = _doc_with_operation({"responses": {"200": {"description": "ok", "links": "not-an-object"}}})
    assert "OPENAPI_RESPONSE_LINKS_INVALID" in _codes(doc)


def test_generator_default_response_description_detected():
    doc = _doc_with_operation(
        {
            "responses": {
                "default": {
                    "description": "Respuesta generada automaticamente (sin descripcion disponible en la evidencia)."
                }
            }
        }
    )
    assert "OPENAPI_GENERATOR_DEFAULT_RESPONSE_DESCRIPTION" in _codes(doc)


def test_hand_written_description_does_not_trigger_generator_heuristic():
    doc = _doc_with_operation({"responses": {"200": {"description": "Devuelve el cliente solicitado."}}})
    assert "OPENAPI_GENERATOR_DEFAULT_RESPONSE_DESCRIPTION" not in _codes(doc)
