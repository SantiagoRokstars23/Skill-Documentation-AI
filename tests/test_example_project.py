from pathlib import Path

from analyzer import analyze_project

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"


def test_analyzes_example_project():
    result = analyze_project(EXAMPLE_PROJECT)

    endpoints_by_signature = {(e.controller, e.method, e.endpoint) for e in result.endpoints}

    assert ("CustomerController", "GET", "/api/customers") in endpoints_by_signature
    assert ("CustomerController", "GET", "/api/customers/{id}") in endpoints_by_signature
    assert ("CustomerController", "POST", "/api/customers") in endpoints_by_signature
    assert ("CustomerController", "PUT", "/api/customers/{id}") in endpoints_by_signature
    assert ("CustomerController", "PATCH", "/api/customers/{id}/status") in endpoints_by_signature
    assert ("CustomerController", "DELETE", "/api/customers/{id}") in endpoints_by_signature
    assert ("OrderController", "GET", "/orders/{orderId}") in endpoints_by_signature

    # OrderController.getOrderSummary usa @RequestMapping sin metodo HTTP explicito:
    # debe omitirse y quedar registrado como warning, no como endpoint (ver docs/07-Analisis.md).
    assert ("OrderController", None, "/orders/{orderId}/summary") not in endpoints_by_signature
    assert any("metodo HTTP explicito" in warning for warning in result.warnings)


def test_example_project_result_is_json_serializable():
    result = analyze_project(EXAMPLE_PROJECT)

    payload = result.to_json()

    assert '"controller": "CustomerController"' in payload


def test_example_project_v0_2_capabilities():
    result = analyze_project(EXAMPLE_PROJECT)

    add_note = next(e for e in result.endpoints if e.java_method == "addNote")
    assert add_note.consumes == ("application/json",)
    assert add_note.produces == ("application/json",)
    assert add_note.security == ("PreAuthorize(hasRole('ADMIN'))",)
    assert add_note.response.status == "HttpStatus.CREATED"

    header_param = next(p for p in add_note.parameters if p.source.value == "header")
    assert header_param.name == "X-Request-Id"

    body_param = next(p for p in add_note.parameters if p.source.value == "body")
    dto = body_param.dto
    assert dto.name == "CustomerRequest"
    fields_by_name = {f.name: f for f in dto.fields}
    assert [v.name for v in fields_by_name["name"].validations] == ["NotBlank", "Size"]
    assert fields_by_name["status"].nested_dto.kind == "enum"
    assert fields_by_name["status"].nested_dto.enum_constants == ("ACTIVE", "INACTIVE", "SUSPENDED")
    assert fields_by_name["address"].nested_dto.name == "Address"
    assert fields_by_name["tags"].is_collection is True

    list_customers = next(e for e in result.endpoints if e.java_method == "listCustomers")
    assert list_customers.response.dto.name == "CustomerResponse"
    assert list_customers.response.is_collection is True

    # LegacyReportController.java tiene un metodo con sintaxis Java invalida a proposito:
    # el motor AST falla en todo el archivo y se recurre al motor de fallback de V0.1, que
    # recupera el unico endpoint valido del archivo (ver docs/07-Analisis.md).
    assert ("LegacyReportController", "GET", "/reports/summary") in {
        (e.controller, e.method, e.endpoint) for e in result.endpoints
    }
    assert any(d.code == "AST_PARSE_FALLBACK" for d in result.diagnostics)
