from analyzer.models import (
    DTO,
    AnalysisResult,
    Controller,
    Diagnostic,
    DiagnosticSeverity,
    Endpoint,
    Evidence,
    Field,
    Parameter,
    ParameterSource,
    Response,
    Validation,
)


def test_parameter_to_dict_serializes_source_as_string():
    parameter = Parameter(name="id", type="Long", source=ParameterSource.PATH, required=True)

    data = parameter.to_dict()

    assert data == {
        "name": "id",
        "type": "Long",
        "source": "path",
        "required": True,
        "default_value": None,
        "validations": [],
        "dto": None,
        "evidence": None,
    }


def test_endpoint_to_dict_includes_parameters_and_evidence():
    endpoint = Endpoint(
        controller="CustomerController",
        endpoint="/customers/{id}",
        method="GET",
        parameters=(Parameter(name="id", type="Long", source=ParameterSource.PATH, required=True),),
        evidence=Evidence(file="CustomerController.java", line=10),
    )

    data = endpoint.to_dict()

    assert data["controller"] == "CustomerController"
    assert data["parameters"] == [
        {
            "name": "id",
            "type": "Long",
            "source": "path",
            "required": True,
            "default_value": None,
            "validations": [],
            "dto": None,
            "evidence": None,
        }
    ]
    assert data["evidence"] == {
        "file": "CustomerController.java",
        "line": 10,
        "symbol": None,
        "type": None,
    }


def test_endpoint_to_dict_without_evidence_is_none():
    endpoint = Endpoint(controller="C", endpoint="/c", method="GET")

    assert endpoint.to_dict()["evidence"] is None


def test_analysis_result_to_json_round_trips_via_json_module():
    import json

    result = AnalysisResult(
        endpoints=[Endpoint(controller="C", endpoint="/c", method="GET")],
        files_analyzed=1,
        warnings=["algo"],
    )

    parsed = json.loads(result.to_json())

    assert parsed["files_analyzed"] == 1
    assert parsed["warnings"] == ["algo"]
    assert len(parsed["endpoints"]) == 1


def test_validation_to_dict():
    validation = Validation(name="Size", args="min=1, max=50", evidence=Evidence(file="X.java", line=3))

    assert validation.to_dict() == {
        "name": "Size",
        "args": "min=1, max=50",
        "evidence": {"file": "X.java", "line": 3, "symbol": None, "type": None},
    }


def test_diagnostic_to_dict_serializes_severity_as_string():
    diagnostic = Diagnostic(
        severity=DiagnosticSeverity.WARNING,
        code="ANALYZER_UNCLOSED_CLASS",
        message="clase sin cerrar",
    )

    assert diagnostic.to_dict() == {
        "severity": "WARNING",
        "code": "ANALYZER_UNCLOSED_CLASS",
        "message": "clase sin cerrar",
        "evidence": None,
    }


def test_field_to_dict_with_nested_dto():
    nested = DTO(name="Address", kind="class", fields=(Field(name="city", type="String"),))
    field_ = Field(
        name="address",
        type="Address",
        validations=(Validation(name="NotNull"),),
        nested_dto=nested,
    )

    data = field_.to_dict()

    assert data["name"] == "address"
    assert data["nested_dto"]["name"] == "Address"
    assert data["nested_dto"]["fields"] == [
        {
            "name": "city",
            "type": "String",
            "is_collection": False,
            "validations": [],
            "nested_dto": None,
            "evidence": None,
        }
    ]
    assert data["validations"] == [{"name": "NotNull", "args": "", "evidence": None}]


def test_dto_to_dict_enum_kind():
    dto = DTO(name="Status", kind="enum", enum_constants=("ACTIVE", "INACTIVE"))

    assert dto.to_dict() == {
        "name": "Status",
        "kind": "enum",
        "fields": [],
        "enum_constants": ["ACTIVE", "INACTIVE"],
        "evidence": None,
    }


def test_response_to_dict():
    response = Response(wrapper="ResponseEntity", body_type="CustomerResponse", status="CREATED")

    assert response.to_dict() == {
        "wrapper": "ResponseEntity",
        "body_type": "CustomerResponse",
        "is_collection": False,
        "dto": None,
        "status": "CREATED",
        "evidence": None,
    }


def test_controller_to_dict():
    controller = Controller(
        name="CustomerController",
        annotations=("RestController", "RequestMapping"),
        modifiers=("public",),
        base_path="/api/customers",
    )

    assert controller.to_dict() == {
        "name": "CustomerController",
        "annotations": ["RestController", "RequestMapping"],
        "modifiers": ["public"],
        "base_path": "/api/customers",
        "evidence": None,
    }


def test_endpoint_to_dict_includes_v0_2_fields():
    endpoint = Endpoint(
        controller="C",
        endpoint="/c",
        method="POST",
        java_method="create",
        consumes=("application/json",),
        produces=("application/json",),
        security=("PreAuthorize",),
        response=Response(wrapper=None, body_type="Void"),
    )

    data = endpoint.to_dict()

    assert data["java_method"] == "create"
    assert data["consumes"] == ["application/json"]
    assert data["produces"] == ["application/json"]
    assert data["security"] == ["PreAuthorize"]
    assert data["response"] == {
        "wrapper": None,
        "body_type": "Void",
        "is_collection": False,
        "dto": None,
        "status": None,
        "evidence": None,
    }


def test_analysis_result_to_dict_includes_controllers_and_diagnostics():
    result = AnalysisResult(
        controllers=[Controller(name="C")],
        diagnostics=[Diagnostic(severity=DiagnosticSeverity.INFO, code="X", message="m")],
    )

    data = result.to_dict()

    assert data["controllers"] == [
        {"name": "C", "annotations": [], "modifiers": [], "base_path": "", "evidence": None}
    ]
    assert data["diagnostics"] == [{"severity": "INFO", "code": "X", "message": "m", "evidence": None}]
