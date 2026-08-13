from analyzer import DTO, Field, Validation
from generators.openapi_schemas import schema_ref_for_dto


def test_simple_dto_schema():
    dto = DTO(
        name="CustomerResponse",
        kind="class",
        fields=(Field(name="id", type="Long"), Field(name="name", type="String")),
    )
    registry = {}
    diagnostics = []

    ref = schema_ref_for_dto(dto, registry, diagnostics)

    assert ref == {"$ref": "#/components/schemas/CustomerResponse"}
    assert registry["CustomerResponse"] == {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "format": "int64"},
            "name": {"type": "string"},
        },
    }


def test_enum_dto_schema():
    dto = DTO(name="CustomerStatus", kind="enum", enum_constants=("ACTIVE", "INACTIVE"))
    registry = {}

    schema_ref_for_dto(dto, registry, [])

    assert registry["CustomerStatus"] == {"type": "string", "enum": ["ACTIVE", "INACTIVE"]}


def test_nested_dto_produces_ref_not_inline_schema():
    address = DTO(name="Address", kind="class", fields=(Field(name="city", type="String"),))
    customer = DTO(
        name="Customer",
        kind="class",
        fields=(Field(name="address", type="Address", nested_dto=address),),
    )
    registry = {}

    schema_ref_for_dto(customer, registry, [])

    assert registry["Customer"]["properties"]["address"] == {"$ref": "#/components/schemas/Address"}
    assert "Address" in registry
    assert registry["Address"]["type"] == "object"


def test_repeated_dto_reference_reuses_single_schema():
    address = DTO(name="Address", kind="class", fields=(Field(name="city", type="String"),))
    customer = DTO(
        name="Customer",
        kind="class",
        fields=(
            Field(name="billingAddress", type="Address", nested_dto=address),
            Field(name="shippingAddress", type="Address", nested_dto=address),
        ),
    )
    registry = {}

    schema_ref_for_dto(customer, registry, [])

    assert len(registry) == 2  # Customer + Address, sin duplicar Address
    assert registry["Customer"]["properties"]["billingAddress"] == {"$ref": "#/components/schemas/Address"}
    assert registry["Customer"]["properties"]["shippingAddress"] == {"$ref": "#/components/schemas/Address"}


def test_collection_field_becomes_array_of_ref():
    line_item = DTO(name="LineItem", kind="class", fields=(Field(name="sku", type="String"),))
    order = DTO(
        name="Order",
        kind="class",
        fields=(Field(name="items", type="List<LineItem>", is_collection=True, nested_dto=line_item),),
    )
    registry = {}

    schema_ref_for_dto(order, registry, [])

    assert registry["Order"]["properties"]["items"] == {
        "type": "array",
        "items": {"$ref": "#/components/schemas/LineItem"},
    }


def test_required_derived_from_not_blank_and_not_null():
    dto = DTO(
        name="CustomerRequest",
        kind="class",
        fields=(
            Field(name="name", type="String", validations=(Validation(name="NotBlank"),)),
            Field(name="age", type="Integer", validations=(Validation(name="NotNull"),)),
            Field(name="email", type="String"),
        ),
    )
    registry = {}

    schema_ref_for_dto(dto, registry, [])

    assert registry["CustomerRequest"]["required"] == ["name", "age"]
    assert "required" not in registry["CustomerRequest"]["properties"]["email"]


def test_dto_without_required_fields_has_no_required_key():
    dto = DTO(name="Simple", kind="class", fields=(Field(name="x", type="String"),))
    registry = {}

    schema_ref_for_dto(dto, registry, [])

    assert "required" not in registry["Simple"]


def test_unresolved_field_type_produces_diagnostic():
    dto = DTO(name="Weird", kind="class", fields=(Field(name="thing", type="SomeExternalType"),))
    registry = {}
    diagnostics = []

    schema_ref_for_dto(dto, registry, diagnostics)

    assert registry["Weird"]["properties"]["thing"] == {}
    assert any(d.code == "OPENAPI_UNKNOWN_TYPE" for d in diagnostics)
