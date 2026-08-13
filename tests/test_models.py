from analyzer.models import AnalysisResult, Endpoint, Evidence, Parameter, ParameterSource


def test_parameter_to_dict_serializes_source_as_string():
    parameter = Parameter(name="id", type="Long", source=ParameterSource.PATH, required=True)

    data = parameter.to_dict()

    assert data == {"name": "id", "type": "Long", "source": "path", "required": True}


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
        {"name": "id", "type": "Long", "source": "path", "required": True}
    ]
    assert data["evidence"] == {"file": "CustomerController.java", "line": 10}


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
