from analyzer.models import ParameterSource
from analyzer.spring_boot_analyzer import analyze_file


def test_request_body_required_by_default(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.PostMapping;
        import org.springframework.web.bind.annotation.RequestBody;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @PostMapping("/customers")
            public String create(@RequestBody CustomerRequest request) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)
    parameter = endpoints[0].parameters[0]

    assert parameter.name == "request"
    assert parameter.type == "CustomerRequest"
    assert parameter.source == ParameterSource.BODY
    assert parameter.required is True


def test_request_body_required_false(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.PatchMapping;
        import org.springframework.web.bind.annotation.RequestBody;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @PatchMapping("/customers/{id}")
            public String patch(@RequestBody(required = false) CustomerRequest request) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)

    assert endpoints[0].parameters[0].required is False


def test_multiple_parameters_mixed_sources(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.PathVariable;
        import org.springframework.web.bind.annotation.PutMapping;
        import org.springframework.web.bind.annotation.RequestBody;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @PutMapping("/customers/{id}")
            public String update(@PathVariable Long id, @RequestBody CustomerRequest request) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)
    parameters = endpoints[0].parameters

    assert len(parameters) == 2
    assert parameters[0].source == ParameterSource.PATH
    assert parameters[1].source == ParameterSource.BODY
