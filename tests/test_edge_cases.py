from analyzer import analyze_project
from analyzer.spring_boot_analyzer import analyze_file


def test_nonexistent_project_returns_empty_result(tmp_path):
    missing = tmp_path / "does-not-exist"

    result = analyze_project(missing)

    assert result.endpoints == []
    assert result.files_analyzed == 0
    assert result.warnings == []


def test_project_without_java_files_returns_empty_result(tmp_path):
    (tmp_path / "README.md").write_text("not java", encoding="utf-8")

    result = analyze_project(tmp_path)

    assert result.endpoints == []
    assert result.files_analyzed == 0


def test_project_without_controllers_returns_no_endpoints(tmp_path):
    (tmp_path / "PlainClass.java").write_text(
        """
        public class PlainClass {
            public void doSomething() {
            }
        }
        """,
        encoding="utf-8",
    )

    result = analyze_project(tmp_path)

    assert result.endpoints == []
    assert result.files_analyzed == 1


def test_request_mapping_without_http_method_is_skipped_with_warning(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.RequestMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @RequestMapping("/customers")
            public String ambiguous() {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, warnings = analyze_file(java_file)

    assert endpoints == []
    assert len(warnings) == 1
    assert "metodo HTTP explicito" in warnings[0]


def test_malformed_class_without_closing_brace_does_not_crash(tmp_path):
    java_file = tmp_path / "Broken.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Broken {

            @GetMapping("/customers")
            public String list() {
                return "ok";
            }
        """,
        encoding="utf-8",
    )

    endpoints, warnings = analyze_file(java_file)

    assert endpoints == []


def test_parameter_without_relevant_annotation_is_ignored(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping("/customers")
            public String list(jakarta.servlet.http.HttpServletRequest request) {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, warnings = analyze_file(java_file)

    assert warnings == []
    assert endpoints[0].parameters == ()


def test_unreadable_file_produces_warning_instead_of_crashing(tmp_path):
    java_file = tmp_path / "Invalid.java"
    java_file.write_bytes(b"\xff\xfe\x00\xff invalid utf-8 \xff")

    endpoints, warnings = analyze_file(java_file)

    assert endpoints == []
    assert len(warnings) == 1
