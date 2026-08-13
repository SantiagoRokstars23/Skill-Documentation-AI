from analyzer import (
    AnalysisResult,
    Endpoint,
    Evidence,
    Parameter,
    ParameterSource,
    Response,
)
from generators import generate, to_json, to_yaml


def _generate_from_java(tmp_path, files: dict[str, str]):
    from analyzer import analyze_project

    for name, content in files.items():
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
    result = analyze_project(tmp_path)
    return generate(result)


# ---------------------------------------------------------------------------
# Paths / HTTP methods
# ---------------------------------------------------------------------------


def test_all_five_http_methods_generate_operations(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            @RequestMapping("/items")
            public class C {
                @GetMapping public String list() { return "ok"; }
                @PostMapping public String create() { return "ok"; }
                @PutMapping("/{id}") public String update() { return "ok"; }
                @PatchMapping("/{id}") public String patch() { return "ok"; }
                @DeleteMapping("/{id}") public String delete() { return "ok"; }
            }
            """
        },
    )

    assert set(document["paths"]["/items"].keys()) == {"get", "post"}
    assert set(document["paths"]["/items/{id}"].keys()) == {"put", "patch", "delete"}


def test_paths_and_schemas_are_sorted_deterministically(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping("/zzz") public String z() { return "ok"; }
                @GetMapping("/aaa") public String a() { return "ok"; }
            }
            """
        },
    )

    assert list(document["paths"].keys()) == ["/aaa", "/zzz"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


def test_path_parameter_is_always_required(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping("/{id}")
                public String get(@PathVariable(required = false) Long id) { return "ok"; }
            }
            """
        },
    )
    param = document["paths"]["/{id}"]["get"]["parameters"][0]
    assert param["in"] == "path"
    assert param["required"] is True


def test_query_parameter_optional_with_default_value(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping public String list(@RequestParam(defaultValue = "10") int limit) { return "ok"; }
            }
            """
        },
    )
    param = document["paths"]["/"]["get"]["parameters"][0]
    assert param == {
        "name": "limit",
        "in": "query",
        "required": False,
        "schema": {"type": "integer", "format": "int32", "default": 10},
    }


def test_header_parameter(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping public String list(@RequestHeader("X-Trace-Id") String traceId) { return "ok"; }
            }
            """
        },
    )
    param = document["paths"]["/"]["get"]["parameters"][0]
    assert param["in"] == "header"
    assert param["name"] == "X-Trace-Id"
    assert param["required"] is True


# ---------------------------------------------------------------------------
# Request body
# ---------------------------------------------------------------------------


def test_request_body_primitive(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @PostMapping public String create(@RequestBody String note) { return "ok"; }
            }
            """
        },
    )
    body = document["paths"]["/"]["post"]["requestBody"]
    assert body["content"]["application/json"]["schema"] == {"type": "string"}
    assert body["required"] is True


def test_request_body_dto_and_collection(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;
            import java.util.List;

            @RestController
            public class C {
                @PostMapping("/one") public String createOne(@RequestBody Item body) { return "ok"; }
                @PostMapping("/many") public String createMany(@RequestBody List<Item> body) { return "ok"; }
            }
            """,
            "Item.java": "public class Item { private String sku; }",
        },
    )
    one = document["paths"]["/one"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    many = document["paths"]["/many"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert one == {"$ref": "#/components/schemas/Item"}
    assert many == {"type": "array", "items": {"$ref": "#/components/schemas/Item"}}


def test_request_body_nested_dto(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @PostMapping public String create(@RequestBody Order body) { return "ok"; }
            }
            """,
            "Order.java": "public class Order { private Item item; }",
            "Item.java": "public class Item { private String sku; }",
        },
    )
    schemas = document["components"]["schemas"]
    assert schemas["Order"]["properties"]["item"] == {"$ref": "#/components/schemas/Item"}
    assert "Item" in schemas


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


def test_response_with_status_evidence(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @PostMapping
                @ResponseStatus(HttpStatus.CREATED)
                public void create() { }
            }
            """
        },
    )
    responses = document["paths"]["/"]["post"]["responses"]
    assert list(responses.keys()) == ["201"]


def test_response_dto_primitive_and_collection(tmp_path):
    document, diagnostics = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.http.ResponseEntity;
            import org.springframework.web.bind.annotation.*;
            import java.util.List;

            @RestController
            public class C {
                @GetMapping("/one") public ResponseEntity<Item> one() { return null; }
                @GetMapping("/many") public ResponseEntity<List<Item>> many() { return null; }
                @GetMapping("/text") public String text() { return "ok"; }
            }
            """,
            "Item.java": "public class Item { private String sku; }",
        },
    )
    one = document["paths"]["/one"]["get"]["responses"]["default"]["content"]["application/json"]["schema"]
    many = document["paths"]["/many"]["get"]["responses"]["default"]["content"]["application/json"]["schema"]
    text = document["paths"]["/text"]["get"]["responses"]["default"]["content"]["application/json"]["schema"]
    assert one == {"$ref": "#/components/schemas/Item"}
    assert many == {"type": "array", "items": {"$ref": "#/components/schemas/Item"}}
    assert text == {"type": "string"}
    assert any(d.code == "OPENAPI_RESPONSE_STATUS_UNKNOWN" for d in diagnostics)


def test_response_void_has_no_content(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @DeleteMapping public void delete() { }
            }
            """
        },
    )
    entry = document["paths"]["/"]["delete"]["responses"]["default"]
    assert "content" not in entry


def test_response_missing_entirely_uses_default_conservative_response():
    # Endpoint construido directamente sin Response (equivalente al motor de fallback).
    result = AnalysisResult(
        endpoints=[
            Endpoint(
                controller="Legacy",
                endpoint="/legacy",
                method="GET",
                evidence=Evidence(file="Legacy.java"),
            )
        ]
    )
    document, diagnostics = generate(result)

    assert document["paths"]["/legacy"]["get"]["responses"] == {
        "default": {"description": document["paths"]["/legacy"]["get"]["responses"]["default"]["description"]}
    }
    assert any(d.code == "OPENAPI_RESPONSE_NO_EVIDENCE" for d in diagnostics)


# ---------------------------------------------------------------------------
# consumes / produces
# ---------------------------------------------------------------------------


def test_consumes_produces_from_method(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @PostMapping(consumes = "application/xml", produces = "application/xml")
                @ResponseStatus(HttpStatus.OK)
                public String create(@RequestBody String body) { return "ok"; }
            }
            """
        },
    )
    op = document["paths"]["/"]["post"]
    assert list(op["requestBody"]["content"].keys()) == ["application/xml"]
    assert list(op["responses"]["200"]["content"].keys()) == ["application/xml"]


def test_consumes_produces_fallback_to_class_level(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            @RequestMapping(consumes = "application/xml")
            public class C {
                @PostMapping public String create(@RequestBody String body) { return "ok"; }
            }
            """
        },
    )
    op = document["paths"]["/"]["post"]
    assert list(op["requestBody"]["content"].keys()) == ["application/xml"]


def test_consumes_absent_uses_documented_convention_and_diagnostic(tmp_path):
    document, diagnostics = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @PostMapping public String create(@RequestBody String body) { return "ok"; }
            }
            """
        },
    )
    op = document["paths"]["/"]["post"]
    assert list(op["requestBody"]["content"].keys()) == ["application/json"]
    assert any(d.code == "OPENAPI_MEDIA_TYPE_CONVENTION" for d in diagnostics)


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------


def test_security_evidence_becomes_extension_and_diagnostic(tmp_path):
    document, diagnostics = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;
            import org.springframework.security.access.prepost.PreAuthorize;

            @RestController
            public class C {
                @GetMapping
                @PreAuthorize("hasRole('ADMIN')")
                public String list() { return "ok"; }
            }
            """
        },
    )
    op = document["paths"]["/"]["get"]
    assert op["x-security-evidence"] == ["PreAuthorize(hasRole('ADMIN'))"]
    assert "security" not in op
    assert any(d.code == "OPENAPI_SECURITY_EVIDENCE_ONLY" for d in diagnostics)


def test_no_security_evidence_omits_extension(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping public String list() { return "ok"; }
            }
            """
        },
    )
    assert "x-security-evidence" not in document["paths"]["/"]["get"]


# ---------------------------------------------------------------------------
# operationId
# ---------------------------------------------------------------------------


def test_operation_id_uses_method_controller_java_method(tmp_path):
    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class CustomerController {
                @GetMapping("/{id}") public String getCustomer() { return "ok"; }
            }
            """
        },
    )
    assert document["paths"]["/{id}"]["get"]["operationId"] == "getCustomerControllerGetCustomer"


def test_operation_id_collision_repeated_method_names_across_controllers():
    result = AnalysisResult(
        endpoints=[
            Endpoint(controller="A", endpoint="/a", method="GET", java_method="list"),
            Endpoint(controller="B", endpoint="/b", method="GET", java_method="list"),
        ]
    )
    document, _ = generate(result)
    ids = {document["paths"][p]["get"]["operationId"] for p in ("/a", "/b")}
    assert ids == {"getAList", "getBList"}  # distintos por controller, sin colision real


def test_operation_id_collision_same_controller_and_method_gets_suffix():
    # Mismo controller + mismo java_method (p.ej. sobrecarga) fuerza colision real.
    result = AnalysisResult(
        endpoints=[
            Endpoint(controller="C", endpoint="/c1", method="GET", java_method="list"),
            Endpoint(controller="C", endpoint="/c2", method="GET", java_method="list"),
            Endpoint(controller="C", endpoint="/c3", method="GET", java_method="list"),
        ]
    )
    document, _ = generate(result)
    ids = [document["paths"][p]["get"]["operationId"] for p in ("/c1", "/c2", "/c3")]
    assert ids == ["getCList", "getCList_2", "getCList_3"]


def test_operation_id_fallback_engine_endpoint_uses_normalized_path():
    # java_method=None equivale a un endpoint producido por el motor de fallback.
    result = AnalysisResult(
        endpoints=[
            Endpoint(controller="Legacy", endpoint="/orders/{orderId}/summary", method="GET"),
        ]
    )
    document, _ = generate(result)
    operation_id = document["paths"]["/orders/{orderId}/summary"]["get"]["operationId"]
    assert operation_id == "getOrdersByOrderIdSummary"


def test_operation_id_never_uses_hash_or_random_values():
    result = AnalysisResult(
        endpoints=[Endpoint(controller="C", endpoint="/x", method="GET", java_method="x")]
    )
    document1, _ = generate(result)
    document2, _ = generate(result)
    assert document1["paths"]["/x"]["get"]["operationId"] == document2["paths"]["/x"]["get"]["operationId"]


# ---------------------------------------------------------------------------
# Serializacion
# ---------------------------------------------------------------------------


def test_to_json_is_valid_and_parseable(tmp_path):
    import json

    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping public String list() { return "ok"; }
            }
            """
        },
    )
    parsed = json.loads(to_json(document))
    assert parsed == document


def test_to_yaml_is_valid_and_parseable(tmp_path):
    import yaml

    document, _ = _generate_from_java(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping public String list() { return "ok"; }
            }
            """
        },
    )
    parsed = yaml.safe_load(to_yaml(document))
    assert parsed == document


def test_generation_is_deterministic_across_runs(tmp_path):
    for name, content in {
        "C.java": """
        import org.springframework.web.bind.annotation.*;

        @RestController
        public class C {
            @GetMapping("/b") public String b() { return "ok"; }
            @GetMapping("/a") public String a() { return "ok"; }
        }
        """
    }.items():
        (tmp_path / name).write_text(content, encoding="utf-8")

    from analyzer import analyze_project

    result = analyze_project(tmp_path)
    doc1, _ = generate(result)
    doc2, _ = generate(result)
    assert to_json(doc1) == to_json(doc2)
    assert to_yaml(doc1) == to_yaml(doc2)
