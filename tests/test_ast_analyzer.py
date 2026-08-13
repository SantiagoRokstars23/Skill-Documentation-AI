from analyzer import ast_analyzer, ast_backend, dto_analyzer


def _analyze(tmp_path, files: dict[str, str], target: str):
    parsed = {}
    for name, content in files.items():
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        unit, text = ast_backend.parse_file(path)
        parsed[str(path)] = (unit, text)
    index = dto_analyzer.build_class_index(parsed)
    target_path = str(tmp_path / target)
    unit, _text = parsed[target_path]
    return ast_analyzer.analyze_compilation_unit(unit, target_path, index)


def test_rest_controller_detected(tmp_path):
    endpoints, controllers, diagnostics = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.GetMapping;
            import org.springframework.web.bind.annotation.RestController;

            @RestController
            public class C {
                @GetMapping("/x")
                public String list() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    assert len(controllers) == 1
    assert controllers[0].name == "C"
    assert endpoints[0].endpoint == "/x"
    assert diagnostics == []


def test_plain_controller_with_mapping_is_detected(tmp_path):
    endpoints, controllers, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.stereotype.Controller;
            import org.springframework.web.bind.annotation.GetMapping;

            @Controller
            public class C {
                @GetMapping("/x")
                public String list() { return "view"; }
            }
            """
        },
        "C.java",
    )

    assert len(controllers) == 1
    assert len(endpoints) == 1


def test_plain_controller_without_mapping_is_ignored(tmp_path):
    endpoints, controllers, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.stereotype.Controller;

            @Controller
            public class C {
                public String helper() { return "not an endpoint"; }
            }
            """
        },
        "C.java",
    )

    assert controllers == []
    assert endpoints == []


def test_fully_qualified_annotations_recognized(tmp_path):
    endpoints, controllers, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            @org.springframework.web.bind.annotation.RestController
            public class C {
                @org.springframework.web.bind.annotation.GetMapping("/x")
                public String list() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    assert len(controllers) == 1
    assert endpoints[0].method == "GET"


def test_package_private_method_detected(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.GetMapping;
            import org.springframework.web.bind.annotation.RestController;

            @RestController
            public class C {
                @GetMapping("/x")
                String list() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    assert len(endpoints) == 1
    assert endpoints[0].java_method == "list"


def test_request_mapping_multiple_methods_produces_multiple_endpoints(tmp_path):
    endpoints, _, diagnostics = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.RequestMapping;
            import org.springframework.web.bind.annotation.RequestMethod;
            import org.springframework.web.bind.annotation.RestController;

            @RestController
            public class C {
                @RequestMapping(value = "/x", method = {RequestMethod.GET, RequestMethod.POST})
                public String handle() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    methods = sorted(e.method for e in endpoints)
    assert methods == ["GET", "POST"]
    assert all(e.endpoint == "/x" for e in endpoints)
    assert diagnostics == []


def test_request_mapping_without_method_produces_diagnostic(tmp_path):
    endpoints, _, diagnostics = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.RequestMapping;
            import org.springframework.web.bind.annotation.RestController;

            @RestController
            public class C {
                @RequestMapping("/x")
                public String handle() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    assert endpoints == []
    assert len(diagnostics) == 1
    assert diagnostics[0].severity.value == "WARNING"
    assert diagnostics[0].code == "AST_MAPPING_WITHOUT_HTTP_METHOD"
    assert "metodo HTTP explicito" in diagnostics[0].message


def test_class_base_path_combines_with_method_path(tmp_path):
    endpoints, controllers, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.GetMapping;
            import org.springframework.web.bind.annotation.RequestMapping;
            import org.springframework.web.bind.annotation.RestController;

            @RestController
            @RequestMapping("/api/customers")
            public class C {
                @GetMapping("/{id}")
                public String get() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    assert controllers[0].base_path == "/api/customers"
    assert endpoints[0].endpoint == "/api/customers/{id}"


def test_path_variable_and_request_param_and_header(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping("/{id}")
                public String get(
                        @PathVariable("id") Long customerId,
                        @RequestParam(defaultValue = "10") int limit,
                        @RequestHeader("X-Request-Id") String requestId) {
                    return "ok";
                }
            }
            """
        },
        "C.java",
    )

    params = {p.name: p for p in endpoints[0].parameters}
    assert params["id"].source.value == "path"
    assert params["limit"].source.value == "query"
    assert params["limit"].required is False
    assert params["limit"].default_value == "10"
    assert params["X-Request-Id"].source.value == "header"


def test_request_body_resolves_dto(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @PostMapping
                public String create(@RequestBody CustomerRequest body) { return "ok"; }
            }
            """,
            "CustomerRequest.java": """
            public class CustomerRequest {
                @jakarta.validation.constraints.NotBlank
                private String name;
            }
            """,
        },
        "C.java",
    )

    body_param = endpoints[0].parameters[0]
    assert body_param.dto.name == "CustomerRequest"
    assert body_param.dto.fields[0].validations[0].name == "NotBlank"


def test_parameter_validation_annotation_captured(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @GetMapping
                public String list(@RequestParam @jakarta.validation.constraints.Positive int page) {
                    return "ok";
                }
            }
            """
        },
        "C.java",
    )

    parameter = endpoints[0].parameters[0]
    assert [v.name for v in parameter.validations] == ["Positive"]


def test_response_wrapper_and_body_and_collection(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.http.ResponseEntity;
            import org.springframework.web.bind.annotation.*;
            import java.util.List;

            @RestController
            public class C {
                @GetMapping
                public ResponseEntity<List<CustomerResponse>> list() { return null; }
            }
            """,
            "CustomerResponse.java": "public class CustomerResponse { private String name; }",
        },
        "C.java",
    )

    response = endpoints[0].response
    assert response.wrapper == "ResponseEntity"
    assert response.is_collection is True
    assert response.body_type == "List<CustomerResponse>"
    assert response.dto.name == "CustomerResponse"


def test_response_status_captured(tmp_path):
    endpoints, _, _ = _analyze(
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
        "C.java",
    )

    assert endpoints[0].response.status == "HttpStatus.CREATED"
    assert endpoints[0].response.body_type is None


def test_response_void_without_wrapper(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @DeleteMapping
                public void delete() { }
            }
            """
        },
        "C.java",
    )

    response = endpoints[0].response
    assert response.wrapper is None
    assert response.body_type is None


def test_consumes_and_produces_from_method(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class C {
                @PostMapping(consumes = "application/json", produces = {"application/json", "application/xml"})
                public String create() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    assert endpoints[0].consumes == ("application/json",)
    assert endpoints[0].produces == ("application/json", "application/xml")


def test_consumes_and_produces_fallback_to_class_level(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            @RequestMapping(value = "/x", consumes = "application/json")
            public class C {
                @PostMapping
                public String create() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    assert endpoints[0].consumes == ("application/json",)


def test_security_evidence_from_class_and_method(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "C.java": """
            import org.springframework.web.bind.annotation.*;
            import org.springframework.security.access.prepost.PreAuthorize;

            @RestController
            @PreAuthorize("hasRole('USER')")
            public class C {
                @GetMapping
                @PreAuthorize("hasRole('ADMIN')")
                public String list() { return "ok"; }
            }
            """
        },
        "C.java",
    )

    assert endpoints[0].security == (
        "PreAuthorize(hasRole('USER'))",
        "PreAuthorize(hasRole('ADMIN'))",
    )


def test_non_controller_class_produces_nothing(tmp_path):
    endpoints, controllers, diagnostics = _analyze(
        tmp_path,
        {"C.java": "public class C { public void helper() {} }"},
        "C.java",
    )

    assert endpoints == []
    assert controllers == []
    assert diagnostics == []


def test_evidence_endpoint_matches_directive_shape(tmp_path):
    endpoints, _, _ = _analyze(
        tmp_path,
        {
            "CustomerController.java": """
            import org.springframework.web.bind.annotation.*;

            @RestController
            public class CustomerController {
                @PostMapping
                public String createCustomer() { return "ok"; }
            }
            """
        },
        "CustomerController.java",
    )

    evidence = endpoints[0].evidence
    assert evidence.symbol == "createCustomer"
    assert evidence.type == "endpoint"
    assert evidence.line is not None
