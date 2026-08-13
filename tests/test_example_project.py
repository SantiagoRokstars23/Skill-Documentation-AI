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
