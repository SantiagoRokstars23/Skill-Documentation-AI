"""Tests del Validator V0.4: documento raiz, paths, metodos HTTP, operationId."""

from validator import validate


def _minimal(paths=None, **overrides):
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": paths if paths is not None else {},
    }
    doc.update(overrides)
    return doc


def _codes(document):
    return [d.code for d in validate(document)]


# ---------------------------------------------------------------------------
# Documento raiz
# ---------------------------------------------------------------------------


def test_document_not_a_dict():
    assert _codes(["not", "a", "dict"]) == ["OPENAPI_DOCUMENT_NOT_OBJECT"]


def test_valid_minimal_document_has_no_errors():
    diagnostics = validate(_minimal())
    assert all(d.severity.value != "ERROR" for d in diagnostics)


def test_missing_openapi_version():
    doc = _minimal()
    del doc["openapi"]
    assert "OPENAPI_MISSING_VERSION" in _codes(doc)


def test_openapi_version_not_string():
    doc = _minimal(openapi=3.0)
    assert "OPENAPI_MISSING_VERSION" in _codes(doc)


def test_unsupported_version_3_1():
    doc = _minimal(openapi="3.1.0")
    assert "OPENAPI_UNSUPPORTED_VERSION" in _codes(doc)


def test_unsupported_version_2_0():
    doc = _minimal(openapi="2.0")
    assert "OPENAPI_UNSUPPORTED_VERSION" in _codes(doc)


def test_version_3_0_3_is_the_reference_no_info_note():
    doc = _minimal(openapi="3.0.3")
    assert "OPENAPI_VERSION_NOT_REFERENCE" not in _codes(doc)


def test_version_3_0_1_is_valid_but_not_reference():
    doc = _minimal(openapi="3.0.1")
    assert "OPENAPI_VERSION_NOT_REFERENCE" in _codes(doc)
    assert "OPENAPI_UNSUPPORTED_VERSION" not in _codes(doc)


def test_missing_info():
    doc = _minimal()
    del doc["info"]
    assert "OPENAPI_MISSING_INFO" in _codes(doc)


def test_missing_info_title():
    doc = _minimal()
    del doc["info"]["title"]
    assert "OPENAPI_MISSING_INFO_TITLE" in _codes(doc)


def test_missing_info_version():
    doc = _minimal()
    del doc["info"]["version"]
    assert "OPENAPI_MISSING_INFO_VERSION" in _codes(doc)


def test_generator_placeholder_info_detected():
    doc = _minimal()
    doc["info"] = {"title": "Generated API", "version": "0.0.0"}
    codes = _codes(doc)
    assert codes.count("OPENAPI_GENERATOR_PLACEHOLDER_INFO") == 2


def test_real_info_does_not_trigger_placeholder_note():
    doc = _minimal()
    doc["info"] = {"title": "Customer Service API", "version": "2.1.0"}
    assert "OPENAPI_GENERATOR_PLACEHOLDER_INFO" not in _codes(doc)


def test_missing_paths():
    doc = _minimal()
    del doc["paths"]
    assert "OPENAPI_MISSING_PATHS" in _codes(doc)


def test_empty_paths_is_info_not_error():
    doc = _minimal(paths={})
    diagnostics = validate(doc)
    codes_by_severity = {d.code: d.severity.value for d in diagnostics}
    assert codes_by_severity.get("OPENAPI_PATHS_EMPTY") == "INFO"


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def test_valid_path():
    doc = _minimal(paths={"/customers": {"get": {"operationId": "listCustomers", "responses": {"200": {"description": "ok"}}}}})
    assert "OPENAPI_INVALID_PATH" not in _codes(doc)


def test_path_without_leading_slash():
    doc = _minimal(paths={"customers": {"get": {"responses": {"200": {"description": "ok"}}}}})
    assert "OPENAPI_INVALID_PATH" in _codes(doc)


def test_path_item_not_an_object():
    doc = _minimal(paths={"/customers": "not-an-object"})
    assert "OPENAPI_INVALID_PATH_ITEM" in _codes(doc)


def test_valid_method_get():
    doc = _minimal(paths={"/x": {"get": {"responses": {"200": {"description": "ok"}}}}})
    assert "OPENAPI_INVALID_METHOD" not in _codes(doc)


def test_invalid_method():
    doc = _minimal(paths={"/x": {"fetch": {"responses": {"200": {"description": "ok"}}}}})
    assert "OPENAPI_INVALID_METHOD" in _codes(doc)


def test_reserved_path_item_keys_are_not_treated_as_methods():
    doc = _minimal(
        paths={
            "/x": {
                "summary": "Resumen",
                "description": "Descripcion",
                "parameters": [],
                "get": {"responses": {"200": {"description": "ok"}}},
            }
        }
    )
    assert "OPENAPI_INVALID_METHOD" not in _codes(doc)


def test_extension_keys_in_path_item_are_ignored():
    doc = _minimal(paths={"/x": {"x-internal-note": "algo", "get": {"responses": {"200": {"description": "ok"}}}}})
    assert "OPENAPI_INVALID_METHOD" not in _codes(doc)


def test_path_parameter_missing_definition():
    doc = _minimal(paths={"/customers/{id}": {"get": {"responses": {"200": {"description": "ok"}}}}})
    assert "OPENAPI_PATH_PARAMETER_MISSING" in _codes(doc)


def test_path_parameter_defined_at_path_item_level():
    doc = _minimal(
        paths={
            "/customers/{id}": {
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "get": {"responses": {"200": {"description": "ok"}}},
            }
        }
    )
    assert "OPENAPI_PATH_PARAMETER_MISSING" not in _codes(doc)


def test_path_parameter_defined_at_operation_level():
    doc = _minimal(
        paths={
            "/customers/{id}": {
                "get": {
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        }
    )
    assert "OPENAPI_PATH_PARAMETER_MISSING" not in _codes(doc)


def test_operation_missing_description_is_warning():
    doc = _minimal(paths={"/x": {"get": {"responses": {"200": {"description": "ok"}}}}})
    diagnostics = validate(doc)
    warning = next(d for d in diagnostics if d.code == "OPENAPI_OPERATION_MISSING_DESCRIPTION")
    assert warning.severity.value == "WARNING"


def test_paths_validated_in_alphabetical_order():
    doc = _minimal(
        paths={
            "/zzz": {"get": {"responses": {"200": {"description": "ok"}}}},
            "/aaa": {"get": {"responses": {"200": {"description": "ok"}}}},
        }
    )
    pointers = [d.evidence.file for d in validate(doc) if d.code == "OPENAPI_OPERATION_MISSING_DESCRIPTION"]
    assert pointers == sorted(pointers)


# ---------------------------------------------------------------------------
# operationId
# ---------------------------------------------------------------------------


def test_unique_operation_id():
    doc = _minimal(
        paths={
            "/a": {"get": {"operationId": "getA", "responses": {"200": {"description": "ok"}}}},
            "/b": {"get": {"operationId": "getB", "responses": {"200": {"description": "ok"}}}},
        }
    )
    assert "OPENAPI_DUPLICATE_OPERATION_ID" not in _codes(doc)


def test_operation_id_not_string():
    doc = _minimal(paths={"/a": {"get": {"operationId": 123, "responses": {"200": {"description": "ok"}}}}})
    assert "OPENAPI_OPERATION_ID_INVALID_TYPE" in _codes(doc)


def test_duplicate_operation_id_across_paths():
    doc = _minimal(
        paths={
            "/a": {"get": {"operationId": "dup", "responses": {"200": {"description": "ok"}}}},
            "/b": {"get": {"operationId": "dup", "responses": {"200": {"description": "ok"}}}},
        }
    )
    assert _codes(doc).count("OPENAPI_DUPLICATE_OPERATION_ID") == 1


def test_duplicate_operation_id_across_methods_same_path():
    doc = _minimal(
        paths={
            "/a": {
                "get": {"operationId": "dup", "responses": {"200": {"description": "ok"}}},
                "post": {"operationId": "dup", "responses": {"200": {"description": "ok"}}},
            },
        }
    )
    assert _codes(doc).count("OPENAPI_DUPLICATE_OPERATION_ID") == 1


def test_triple_duplicate_operation_id_flags_each_extra_occurrence():
    doc = _minimal(
        paths={
            "/a": {"get": {"operationId": "dup", "responses": {"200": {"description": "ok"}}}},
            "/b": {"get": {"operationId": "dup", "responses": {"200": {"description": "ok"}}}},
            "/c": {"get": {"operationId": "dup", "responses": {"200": {"description": "ok"}}}},
        }
    )
    assert _codes(doc).count("OPENAPI_DUPLICATE_OPERATION_ID") == 2
