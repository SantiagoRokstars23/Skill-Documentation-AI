"""Tests del Validator V0.4: schemas, enum, $ref, components, security."""

from validator import validate


def _doc_with_schema(schema, components=None):
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/x": {
                "get": {
                    "operationId": "getX",
                    "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": schema}}}},
                }
            }
        },
    }
    if components is not None:
        doc["components"] = components
    return doc


def _codes(document):
    return [d.code for d in validate(document)]


# ---------------------------------------------------------------------------
# Schemas: tipos primitivos, array, object
# ---------------------------------------------------------------------------


def test_primitive_schema_valid():
    doc = _doc_with_schema({"type": "string", "description": "d"})
    assert "OPENAPI_INVALID_SCHEMA_TYPE" not in _codes(doc)


def test_invalid_schema_type():
    doc = _doc_with_schema({"type": "weird"})
    assert "OPENAPI_INVALID_SCHEMA_TYPE" in _codes(doc)


def test_array_with_items_valid():
    doc = _doc_with_schema({"type": "array", "items": {"type": "string"}, "description": "d"})
    assert "OPENAPI_ARRAY_ITEMS_MISSING" not in _codes(doc)


def test_array_without_items_is_error():
    doc = _doc_with_schema({"type": "array"})
    assert "OPENAPI_ARRAY_ITEMS_MISSING" in _codes(doc)


def test_object_with_properties_valid():
    doc = _doc_with_schema(
        {"type": "object", "description": "d", "properties": {"name": {"type": "string", "description": "d"}}}
    )
    assert "OPENAPI_OBJECT_SCHEMA_EMPTY" not in _codes(doc)


def test_object_without_properties_is_warning():
    doc = _doc_with_schema({"type": "object", "description": "d"})
    diagnostics = validate(doc)
    finding = next(d for d in diagnostics if d.code == "OPENAPI_OBJECT_SCHEMA_EMPTY")
    assert finding.severity.value == "WARNING"


def test_object_with_additional_properties_true_is_not_empty():
    doc = _doc_with_schema({"type": "object", "description": "d", "additionalProperties": True})
    assert "OPENAPI_OBJECT_SCHEMA_EMPTY" not in _codes(doc)


def test_required_field_not_declared_in_properties():
    doc = _doc_with_schema(
        {
            "type": "object",
            "description": "d",
            "properties": {"name": {"type": "string", "description": "d"}},
            "required": ["name", "ghost"],
        }
    )
    assert "OPENAPI_REQUIRED_FIELD_UNDEFINED" in _codes(doc)


def test_required_invalid_type():
    doc = _doc_with_schema({"type": "object", "description": "d", "required": "name"})
    assert "OPENAPI_OBJECT_SCHEMA_INVALID" in _codes(doc)


# ---------------------------------------------------------------------------
# Constraints: string / number
# ---------------------------------------------------------------------------


def test_string_min_greater_than_max_is_error():
    doc = _doc_with_schema({"type": "string", "description": "d", "minLength": 10, "maxLength": 2})
    assert "OPENAPI_STRING_CONSTRAINT_INVALID" in _codes(doc)


def test_string_constraints_valid():
    doc = _doc_with_schema({"type": "string", "description": "d", "minLength": 1, "maxLength": 10, "pattern": "^[a-z]+$"})
    assert "OPENAPI_STRING_CONSTRAINT_INVALID" not in _codes(doc)


def test_number_minimum_greater_than_maximum_is_error():
    doc = _doc_with_schema({"type": "integer", "description": "d", "minimum": 10, "maximum": 1})
    assert "OPENAPI_NUMBER_CONSTRAINT_INVALID" in _codes(doc)


def test_exclusive_minimum_must_be_boolean_in_3_0_x():
    doc = _doc_with_schema({"type": "number", "description": "d", "exclusiveMinimum": 5})
    assert "OPENAPI_NUMBER_CONSTRAINT_INVALID" in _codes(doc)


def test_exclusive_minimum_boolean_valid():
    doc = _doc_with_schema({"type": "number", "description": "d", "minimum": 0, "exclusiveMinimum": True})
    assert "OPENAPI_NUMBER_CONSTRAINT_INVALID" not in _codes(doc)


def test_multiple_of_zero_is_invalid():
    doc = _doc_with_schema({"type": "integer", "description": "d", "multipleOf": 0})
    assert "OPENAPI_NUMBER_CONSTRAINT_INVALID" in _codes(doc)


# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------


def test_enum_valid():
    doc = _doc_with_schema({"type": "string", "description": "d", "enum": ["A", "B", "C"]})
    assert "OPENAPI_ENUM_INVALID" not in _codes(doc)
    assert "OPENAPI_ENUM_DUPLICATE_VALUES" not in _codes(doc)


def test_enum_not_a_list():
    doc = _doc_with_schema({"type": "string", "description": "d", "enum": "A"})
    assert "OPENAPI_ENUM_INVALID" in _codes(doc)


def test_enum_duplicate_values():
    doc = _doc_with_schema({"type": "string", "description": "d", "enum": ["A", "B", "A"]})
    assert "OPENAPI_ENUM_DUPLICATE_VALUES" in _codes(doc)


def test_enum_type_mismatch():
    doc = _doc_with_schema({"type": "string", "description": "d", "enum": ["A", 1]})
    assert "OPENAPI_ENUM_TYPE_MISMATCH" in _codes(doc)


# ---------------------------------------------------------------------------
# $ref
# ---------------------------------------------------------------------------


def test_ref_valid_resolves():
    doc = _doc_with_schema(
        {"$ref": "#/components/schemas/Customer"},
        components={"schemas": {"Customer": {"type": "object", "description": "d", "properties": {}}}},
    )
    assert "OPENAPI_REF_NOT_FOUND" not in _codes(doc)
    assert "OPENAPI_REF_INVALID" not in _codes(doc)


def test_ref_not_found():
    doc = _doc_with_schema({"$ref": "#/components/schemas/DoesNotExist"})
    assert "OPENAPI_REF_NOT_FOUND" in _codes(doc)


def test_ref_empty_string():
    doc = _doc_with_schema({"$ref": ""})
    assert "OPENAPI_REF_INVALID" in _codes(doc)


def test_ref_malformed_structure():
    doc = _doc_with_schema({"$ref": "#/components/schemas/"})
    assert "OPENAPI_REF_INVALID" in _codes(doc)


def test_ref_external_is_info_not_error():
    doc = _doc_with_schema({"$ref": "https://example.com/schema.json#/Foo"})
    diagnostics = validate(doc)
    finding = next(d for d in diagnostics if d.code == "OPENAPI_REF_EXTERNAL_SKIPPED")
    assert finding.severity.value == "INFO"
    assert not any(d.severity.value == "ERROR" for d in diagnostics)


def test_repeated_ref_is_counted_as_referenced_and_not_duplicated_inline():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {
            "/a": {
                "get": {
                    "operationId": "getA",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Customer"}}},
                        }
                    },
                }
            },
            "/b": {
                "get": {
                    "operationId": "getB",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Customer"}}
                                }
                            },
                        }
                    },
                }
            },
        },
        "components": {"schemas": {"Customer": {"type": "object", "description": "d", "properties": {}}}},
    }
    codes = _codes(doc)
    assert "OPENAPI_REF_NOT_FOUND" not in codes
    assert "OPENAPI_SCHEMA_UNREFERENCED" not in codes


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


def test_components_not_required():
    doc = {"openapi": "3.0.3", "info": {"title": "X", "version": "1"}, "paths": {}}
    assert "OPENAPI_COMPONENTS_INVALID" not in _codes(doc)


def test_components_invalid_type():
    doc = {"openapi": "3.0.3", "info": {"title": "X", "version": "1"}, "paths": {}, "components": "not-an-object"}
    assert "OPENAPI_COMPONENTS_INVALID" in _codes(doc)


def test_component_name_invalid_characters():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {},
        "components": {"schemas": {"Bad Name!": {"type": "object", "description": "d", "properties": {}}}},
    }
    diagnostics = validate(doc)
    finding = next(d for d in diagnostics if d.code == "OPENAPI_COMPONENT_NAME_INVALID")
    assert finding.severity.value == "WARNING"


def test_unreferenced_schema_is_info():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {},
        "components": {"schemas": {"Orphan": {"type": "object", "description": "d", "properties": {}}}},
    }
    diagnostics = validate(doc)
    finding = next(d for d in diagnostics if d.code == "OPENAPI_SCHEMA_UNREFERENCED")
    assert finding.severity.value == "INFO"


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------


def _doc_with_operation_extra(extra):
    return {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {"/x": {"get": {"operationId": "getX", "responses": {"200": {"description": "ok"}}, **extra}}},
    }


def test_operation_without_security_is_info():
    doc = _doc_with_operation_extra({})
    diagnostics = validate(doc)
    finding = next(d for d in diagnostics if d.code == "OPENAPI_OPERATION_NO_SECURITY")
    assert finding.severity.value == "INFO"


def test_x_security_evidence_is_warning_not_error():
    doc = _doc_with_operation_extra({"x-security-evidence": ["PreAuthorize(hasRole('ADMIN'))"]})
    diagnostics = validate(doc)
    finding = next(d for d in diagnostics if d.code == "OPENAPI_SECURITY_EXTENSION_ONLY")
    assert finding.severity.value == "WARNING"
    assert "OPENAPI_OPERATION_NO_SECURITY" not in [d.code for d in diagnostics]


def test_x_security_evidence_malformed():
    doc = _doc_with_operation_extra({"x-security-evidence": "not-a-list"})
    assert "OPENAPI_EXTENSION_MALFORMED" in _codes(doc)


def test_security_scheme_not_found():
    doc = _doc_with_operation_extra({"security": [{"missingScheme": []}]})
    assert "OPENAPI_SECURITY_SCHEME_NOT_FOUND" in _codes(doc)


def test_security_scheme_found_valid():
    doc = _doc_with_operation_extra({"security": [{"apiKeyAuth": []}]})
    doc["components"] = {"securitySchemes": {"apiKeyAuth": {"type": "apiKey", "name": "X-Api-Key", "in": "header"}}}
    assert "OPENAPI_SECURITY_SCHEME_NOT_FOUND" not in _codes(doc)
    assert "OPENAPI_SECURITY_INVALID" not in _codes(doc)


def test_security_scheme_apikey_missing_fields():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {},
        "components": {"securitySchemes": {"apiKeyAuth": {"type": "apiKey"}}},
    }
    assert "OPENAPI_SECURITY_INVALID" in _codes(doc)


def test_security_scheme_http_missing_scheme_field():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {},
        "components": {"securitySchemes": {"bearerAuth": {"type": "http"}}},
    }
    assert "OPENAPI_SECURITY_INVALID" in _codes(doc)


def test_security_scheme_oauth2_valid():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {},
        "components": {
            "securitySchemes": {
                "oauth2Auth": {
                    "type": "oauth2",
                    "flows": {"authorizationCode": {"authorizationUrl": "https://x", "tokenUrl": "https://y", "scopes": {}}},
                }
            }
        },
    }
    assert "OPENAPI_SECURITY_INVALID" not in _codes(doc)


def test_security_scheme_unknown_type():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": "1"},
        "paths": {},
        "components": {"securitySchemes": {"weird": {"type": "basic"}}},
    }
    assert "OPENAPI_SECURITY_INVALID" in _codes(doc)
