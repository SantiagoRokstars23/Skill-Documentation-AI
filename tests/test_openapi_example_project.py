"""Golden files limitados (seccion 11 de la directriz V0.3): no se compara byte a
byte contra un archivo fijo. Se regenera el documento a partir del proyecto de
ejemplo y se validan hechos estructurales clave, tal como autorizado."""

import json
from pathlib import Path

import yaml

from analyzer import analyze_project
from generators import generate, to_json, to_yaml

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"


def _generate_example_document():
    result = analyze_project(EXAMPLE_PROJECT)
    return generate(result)


def test_yaml_output_is_parseable():
    document, _ = _generate_example_document()
    parsed = yaml.safe_load(to_yaml(document))
    assert parsed == document


def test_json_output_is_parseable():
    document, _ = _generate_example_document()
    parsed = json.loads(to_json(document))
    assert parsed == document


def test_openapi_version_is_3_0_3():
    document, _ = _generate_example_document()
    assert document["openapi"] == "3.0.3"


def test_info_object_present():
    document, _ = _generate_example_document()
    assert "title" in document["info"]
    assert "version" in document["info"]


def test_expected_paths_present():
    document, _ = _generate_example_document()
    for path in (
        "/api/customers",
        "/api/customers/{id}",
        "/api/customers/{id}/status",
        "/api/customers/{id}/notes",
        "/orders/{orderId}",
        "/reports/summary",
    ):
        assert path in document["paths"]


def test_expected_operations_present():
    document, _ = _generate_example_document()
    assert set(document["paths"]["/api/customers"].keys()) == {"get", "post"}
    assert set(document["paths"]["/api/customers/{id}"].keys()) == {"get", "put", "delete"}


def test_main_schemas_present():
    document, _ = _generate_example_document()
    schemas = document["components"]["schemas"]
    for name in ("CustomerRequest", "CustomerResponse", "Address", "CustomerStatus", "OrderResponse"):
        assert name in schemas


def test_refs_used_for_dto_reuse():
    document, _ = _generate_example_document()
    list_schema = document["paths"]["/api/customers"]["get"]["responses"]["default"]["content"][
        "application/json"
    ]["schema"]
    single_schema = document["paths"]["/api/customers/{id}"]["get"]["responses"]["default"]["content"][
        "application/json"
    ]["schema"]
    assert list_schema == {"type": "array", "items": {"$ref": "#/components/schemas/CustomerResponse"}}
    assert single_schema == {"$ref": "#/components/schemas/CustomerResponse"}
    # Un unico schema registrado para CustomerResponse, reutilizado por ambos endpoints.
    assert list(document["components"]["schemas"]).count("CustomerResponse") == 1


def test_generation_over_example_project_is_deterministic():
    doc1, _ = _generate_example_document()
    doc2, _ = _generate_example_document()
    assert to_json(doc1) == to_json(doc2)
