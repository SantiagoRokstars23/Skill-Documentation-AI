import pytest

from analyzer.spring_boot_analyzer import analyze_file

MAPPING_CASES = [
    ("GetMapping", "GET"),
    ("PostMapping", "POST"),
    ("PutMapping", "PUT"),
    ("DeleteMapping", "DELETE"),
    ("PatchMapping", "PATCH"),
]


@pytest.mark.parametrize("annotation, expected_method", MAPPING_CASES)
def test_detects_http_method(tmp_path, annotation, expected_method):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        f"""
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {{

            @{annotation}("/items")
            public String handle() {{
                return "ok";
            }}
        }}
        """,
        encoding="utf-8",
    )

    endpoints, warnings = analyze_file(java_file)

    assert warnings == []
    assert len(endpoints) == 1
    assert endpoints[0].method == expected_method
    assert endpoints[0].endpoint == "/items"


def test_request_mapping_with_explicit_method(tmp_path):
    java_file = tmp_path / "Controller.java"
    java_file.write_text(
        """
        import org.springframework.web.bind.annotation.RequestMapping;
        import org.springframework.web.bind.annotation.RequestMethod;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Controller {

            @RequestMapping(value = "/items", method = RequestMethod.POST)
            public String create() {
                return "ok";
            }
        }
        """,
        encoding="utf-8",
    )

    endpoints, warnings = analyze_file(java_file)

    assert warnings == []
    assert len(endpoints) == 1
    assert endpoints[0].method == "POST"
    assert endpoints[0].endpoint == "/items"
