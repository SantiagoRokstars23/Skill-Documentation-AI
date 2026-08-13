from analyzer.models import ParameterSource
from analyzer.spring_boot_analyzer import analyze_file


def test_path_variable_implicit_name(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.PathVariable;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping("/customers/{id}")
            public String get(@PathVariable Long id) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)
    parameters = endpoints[0].parameters

    assert len(parameters) == 1
    assert parameters[0].name == "id"
    assert parameters[0].type == "Long"
    assert parameters[0].source == ParameterSource.PATH
    assert parameters[0].required is True


def test_path_variable_explicit_name(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.PathVariable;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping("/customers/{id}")
            public String get(@PathVariable("id") Long customerId) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)

    assert endpoints[0].parameters[0].name == "id"


def test_path_variable_required_false(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.PathVariable;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping("/customers/{id}")
            public String get(@PathVariable(required = false) Long id) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)

    assert endpoints[0].parameters[0].required is False
