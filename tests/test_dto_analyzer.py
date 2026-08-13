from analyzer import ast_backend, dto_analyzer


def _index(tmp_path, files: dict[str, str]):
    parsed = {}
    for name, content in files.items():
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        unit, text = ast_backend.parse_file(path)
        parsed[str(path)] = (unit, text)
    return dto_analyzer.build_class_index(parsed)


def test_resolves_simple_dto_fields(tmp_path):
    index = _index(
        tmp_path,
        {
            "CustomerRequest.java": """
            public class CustomerRequest {
                private String name;
                private Integer age;
            }
            """
        },
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("CustomerRequest", index, diagnostics)

    assert dto.name == "CustomerRequest"
    assert dto.kind == "class"
    assert [f.name for f in dto.fields] == ["name", "age"]
    assert [f.type for f in dto.fields] == ["String", "Integer"]
    assert diagnostics == []


def test_resolves_nested_dto(tmp_path):
    index = _index(
        tmp_path,
        {
            "CustomerRequest.java": """
            public class CustomerRequest {
                private Address address;
            }
            """,
            "Address.java": """
            public class Address {
                private String city;
            }
            """,
        },
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("CustomerRequest", index, diagnostics)

    address_field = dto.fields[0]
    assert address_field.type == "Address"
    assert address_field.nested_dto.name == "Address"
    assert address_field.nested_dto.fields[0].name == "city"


def test_collection_field_unwraps_and_preserves_type_text(tmp_path):
    index = _index(
        tmp_path,
        {
            "Order.java": """
            public class Order {
                private java.util.List<String> tags;
                private java.util.List<LineItem> items;
            }
            """,
            "LineItem.java": """
            public class LineItem {
                private String sku;
            }
            """,
        },
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("Order", index, diagnostics)
    tags, items = dto.fields

    assert tags.is_collection is True
    assert tags.type == "java.util.List<String>"
    assert tags.nested_dto is None
    assert items.is_collection is True
    assert items.nested_dto.name == "LineItem"


def test_enum_dto(tmp_path):
    index = _index(
        tmp_path,
        {"CustomerStatus.java": "public enum CustomerStatus { ACTIVE, INACTIVE }"},
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("CustomerStatus", index, diagnostics)

    assert dto.kind == "enum"
    assert dto.enum_constants == ("ACTIVE", "INACTIVE")
    assert dto.fields == ()


def test_cycle_detected_produces_diagnostic_and_stops_recursion(tmp_path):
    index = _index(
        tmp_path,
        {
            "A.java": "public class A { private B b; }",
            "B.java": "public class B { private A a; }",
        },
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("A", index, diagnostics)

    b_field = dto.fields[0]
    assert b_field.nested_dto.name == "B"
    a_field_inside_b = b_field.nested_dto.fields[0]
    assert a_field_inside_b.type == "A"
    assert a_field_inside_b.nested_dto is None
    assert any(d.code == "DTO_CYCLE_DETECTED" for d in diagnostics)


def test_ambiguous_name_produces_diagnostic_and_returns_none(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    index = _index(
        tmp_path,
        {
            "a/Foo.java": "public class Foo { private String x; }",
            "b/Foo.java": "public class Foo { private int y; }",
        },
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("Foo", index, diagnostics)

    assert dto is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity.value == "WARNING"
    assert diagnostics[0].code == "DTO_NAME_AMBIGUOUS"


def test_unknown_type_name_returns_none_without_diagnostic(tmp_path):
    index = _index(tmp_path, {"A.java": "public class A { private String x; }"})
    diagnostics = []

    dto = dto_analyzer.resolve_dto("SomeExternalType", index, diagnostics)

    assert dto is None
    assert diagnostics == []


def test_static_fields_excluded(tmp_path):
    index = _index(
        tmp_path,
        {
            "Constants.java": """
            public class Constants {
                public static final String VERSION = "1";
                private String name;
            }
            """
        },
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("Constants", index, diagnostics)

    assert [f.name for f in dto.fields] == ["name"]


def test_extract_validations_recognizes_known_annotations_only(tmp_path):
    index = _index(
        tmp_path,
        {
            "CustomerRequest.java": """
            public class CustomerRequest {
                @jakarta.validation.constraints.NotBlank
                @SomeUnrelatedAnnotation
                private String name;
            }
            """
        },
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("CustomerRequest", index, diagnostics)
    validations = dto.fields[0].validations

    assert [v.name for v in validations] == ["NotBlank"]


def test_extract_validations_captures_args(tmp_path):
    index = _index(
        tmp_path,
        {
            "CustomerRequest.java": """
            public class CustomerRequest {
                @jakarta.validation.constraints.Size(min = 1, max = 50)
                private String name;
            }
            """
        },
    )
    diagnostics = []

    dto = dto_analyzer.resolve_dto("CustomerRequest", index, diagnostics)
    validation = dto.fields[0].validations[0]

    assert validation.name == "Size"
    assert "min=1" in validation.args
    assert "max=50" in validation.args
