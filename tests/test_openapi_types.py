from analyzer import DTO, Validation
from generators.openapi_types import (
    apply_validations,
    build_type_schema,
    is_required_by_validation,
    parse_type_text,
)


def test_parse_simple_type():
    parsed = parse_type_text("Long")
    assert parsed.name == "Long"
    assert parsed.args == ()
    assert parsed.array_dims == 0


def test_parse_qualified_type_keeps_simple_name():
    parsed = parse_type_text("java.util.List<String>")
    assert parsed.name == "List"
    assert parsed.args[0].name == "String"


def test_parse_nested_generics():
    parsed = parse_type_text("ResponseEntity<List<CustomerResponse>>")
    assert parsed.name == "ResponseEntity"
    assert parsed.args[0].name == "List"
    assert parsed.args[0].args[0].name == "CustomerResponse"


def test_parse_array_dimension():
    parsed = parse_type_text("String[]")
    assert parsed.name == "String"
    assert parsed.array_dims == 1


def test_parse_multi_argument_generic():
    parsed = parse_type_text("Map<String, Object>")
    assert parsed.name == "Map"
    assert [a.name for a in parsed.args] == ["String", "Object"]


def test_parse_wildcard_and_void():
    assert parse_type_text("?").name == "?"
    assert parse_type_text("void").name == "void"


def test_build_schema_primitive_long():
    diagnostics = []
    schema = build_type_schema("Long", None, diagnostics, None)
    assert schema == {"type": "integer", "format": "int64"}
    assert diagnostics == []


def test_build_schema_string_no_format():
    diagnostics = []
    schema = build_type_schema("String", None, diagnostics, None)
    assert schema == {"type": "string"}


def test_build_schema_array_of_primitive():
    diagnostics = []
    schema = build_type_schema("List<String>", None, diagnostics, None)
    assert schema == {"type": "array", "items": {"type": "string"}}


def test_build_schema_array_via_java_array_syntax():
    diagnostics = []
    schema = build_type_schema("String[]", None, diagnostics, None)
    assert schema == {"type": "array", "items": {"type": "string"}}


def test_build_schema_optional_unwraps_transparently():
    diagnostics = []
    schema = build_type_schema("Optional<String>", None, diagnostics, None)
    assert schema == {"type": "string"}


def test_build_schema_map_is_generic_object_without_diagnostic():
    diagnostics = []
    schema = build_type_schema("Map<String, Object>", None, diagnostics, None)
    assert schema == {"type": "object"}
    assert diagnostics == []


def test_build_schema_unknown_type_is_empty_and_diagnosed():
    diagnostics = []
    schema = build_type_schema("SomeUnknownType", None, diagnostics, None)
    assert schema == {}
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "OPENAPI_UNKNOWN_TYPE"
    assert diagnostics[0].severity.value == "WARNING"


def test_build_schema_resolves_dto_via_callback():
    dto = DTO(name="CustomerResponse", kind="class")
    registry = {}
    diagnostics = []

    def resolve_ref(resolved_dto):
        registry[resolved_dto.name] = {"type": "object"}
        return {"$ref": f"#/components/schemas/{resolved_dto.name}"}

    schema = build_type_schema("CustomerResponse", dto, diagnostics, None, resolve_dto_ref=resolve_ref)

    assert schema == {"$ref": "#/components/schemas/CustomerResponse"}
    assert diagnostics == []


def test_build_schema_dto_ignored_without_resolver_callback():
    dto = DTO(name="CustomerResponse", kind="class")
    diagnostics = []

    schema = build_type_schema("CustomerResponse", dto, diagnostics, None)

    assert schema == {}
    assert diagnostics[0].code == "OPENAPI_UNKNOWN_TYPE"


def test_validation_not_blank_sets_min_length():
    schema = apply_validations({"type": "string"}, (Validation(name="NotBlank"),), is_collection=False)
    assert schema["minLength"] == 1


def test_validation_not_empty_string_vs_collection():
    string_schema = apply_validations({"type": "string"}, (Validation(name="NotEmpty"),), is_collection=False)
    array_schema = apply_validations(
        {"type": "array", "items": {"type": "string"}}, (Validation(name="NotEmpty"),), is_collection=True
    )
    assert string_schema["minLength"] == 1
    assert array_schema["minItems"] == 1


def test_validation_size_string_vs_collection():
    string_schema = apply_validations(
        {"type": "string"}, (Validation(name="Size", args="min=1, max=50"),), is_collection=False
    )
    array_schema = apply_validations(
        {"type": "array", "items": {}}, (Validation(name="Size", args="min=1, max=50"),), is_collection=True
    )
    assert string_schema == {"type": "string", "minLength": 1, "maxLength": 50}
    assert array_schema["minItems"] == 1
    assert array_schema["maxItems"] == 50


def test_validation_min_max_numbers():
    schema = apply_validations(
        {"type": "integer"},
        (Validation(name="Min", args="1"), Validation(name="Max", args="100")),
        is_collection=False,
    )
    assert schema["minimum"] == 1
    assert schema["maximum"] == 100


def test_validation_email_sets_format():
    schema = apply_validations({"type": "string"}, (Validation(name="Email"),), is_collection=False)
    assert schema["format"] == "email"


def test_validation_pattern_sets_pattern():
    schema = apply_validations(
        {"type": "string"}, (Validation(name="Pattern", args="regexp=^[A-Z]+$"),), is_collection=False
    )
    assert schema["pattern"] == "^[A-Z]+$"


def test_validation_positive_and_negative():
    positive = apply_validations({"type": "integer"}, (Validation(name="Positive"),), is_collection=False)
    positive_or_zero = apply_validations(
        {"type": "integer"}, (Validation(name="PositiveOrZero"),), is_collection=False
    )
    negative = apply_validations({"type": "integer"}, (Validation(name="Negative"),), is_collection=False)
    negative_or_zero = apply_validations(
        {"type": "integer"}, (Validation(name="NegativeOrZero"),), is_collection=False
    )
    assert positive == {"type": "integer", "minimum": 0, "exclusiveMinimum": True}
    assert positive_or_zero == {"type": "integer", "minimum": 0}
    assert negative == {"type": "integer", "maximum": 0, "exclusiveMaximum": True}
    assert negative_or_zero == {"type": "integer", "maximum": 0}


def test_is_required_by_validation():
    assert is_required_by_validation((Validation(name="NotNull"),)) is True
    assert is_required_by_validation((Validation(name="NotBlank"),)) is True
    assert is_required_by_validation((Validation(name="NotEmpty"),)) is True
    assert is_required_by_validation((Validation(name="Email"),)) is False
    assert is_required_by_validation(()) is False
