from analyzer.models import ParameterSource
from analyzer.spring_boot_analyzer import analyze_file


def test_request_param_required_by_default(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RequestParam;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping("/customers")
            public String list(@RequestParam String status) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)
    parameter = endpoints[0].parameters[0]

    assert parameter.name == "status"
    assert parameter.type == "String"
    assert parameter.source == ParameterSource.QUERY
    assert parameter.required is True


def test_request_param_required_false(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RequestParam;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping("/customers")
            public String list(@RequestParam(required = false) String status) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)

    assert endpoints[0].parameters[0].required is False


def test_request_param_with_default_value_is_optional(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RequestParam;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping("/customers")
            public String list(@RequestParam(defaultValue = "0") int page) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)
    parameter = endpoints[0].parameters[0]

    assert parameter.name == "page"
    assert parameter.type == "int"
    assert parameter.required is False


def test_request_param_explicit_name(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RequestParam;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping("/customers")
            public String list(@RequestParam(name = "size", defaultValue = "20") int pageSize) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)

    assert endpoints[0].parameters[0].name == "size"
