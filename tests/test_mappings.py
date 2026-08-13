from analyzer.spring_boot_analyzer import analyze_file


def test_combines_class_base_path_with_method_path(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RequestMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        @RequestMapping("/api/customers")
        public class Controller {

            @GetMapping("/active")
            public String active() {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, warnings = analyze_file(java_file)

    assert warnings == []
    assert endpoints[0].endpoint == "/api/customers/active"


def test_method_mapping_without_path_uses_base_path(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RequestMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        @RequestMapping("/api/customers")
        public class Controller {

            @GetMapping
            public String list() {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)

    assert endpoints[0].endpoint == "/api/customers"


def test_path_value_attribute_form(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping(value = "/customers")
            public String list() {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)

    assert endpoints[0].endpoint == "/customers"


def test_no_base_path_no_method_path_defaults_to_root(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @GetMapping
            public String root() {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, _ = analyze_file(java_file)

    assert endpoints[0].endpoint == "/"
