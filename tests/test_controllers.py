from analyzer.spring_boot_analyzer import analyze_file


def test_detects_rest_controller(tmp_path):
    java_file = tmp_path / "CustomerController.java"
    java_file.write_text(
        """
        package com.example.controller;

        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class CustomerController {

            @GetMapping("/customers")
            public String list() {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, warnings = analyze_file(java_file)

    assert warnings == []
    assert len(endpoints) == 1
    assert endpoints[0].controller == "CustomerController"


def test_ignores_class_without_rest_controller(tmp_path):
    java_file = tmp_path / "CustomerService.java"
    java_file.write_text(
        """
        package com.example.service;

        public class CustomerService {

            public String find() {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, warnings = analyze_file(java_file)

    assert endpoints == []
    assert warnings == []


def test_detects_multiple_controllers_in_project(tmp_path):
    (tmp_path / "A.java").write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class AController {
            @GetMapping("/a")
            public String a() { return "a"; }
        }
        """,
        encoding="utf-8",
    )
    (tmp_path / "B.java").write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class BController {
            @GetMapping("/b")
            public String b() { return "b"; }
        }
        """,
        encoding="utf-8",
    )

    from analyzer import analyze_project

    result = analyze_project(tmp_path)

    controllers = {e.controller for e in result.endpoints}
    assert controllers == {"AController", "BController"}
    assert result.files_analyzed == 2
