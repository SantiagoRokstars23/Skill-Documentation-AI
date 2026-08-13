from analyzer import analyze_project


def test_fallback_used_for_unparseable_file_recovers_valid_method(tmp_path):
    # El motor AST falla en TODO el archivo ante cualquier error de sintaxis Java
    # (verificado en el reporte de Fase 2). El motor de fallback (V0.1) recupera el
    # metodo valido y omite unicamente el metodo malformado, igual que en V0.1.
    (tmp_path / "Partial.java").write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Partial {

            @GetMapping("/good")
            public String good() {
                return "ok";
            }

            public String broken(String unterminated {
                return "x";
            }
        }
        """,
        encoding="utf-8",
    )

    result = analyze_project(tmp_path)

    assert len(result.endpoints) == 1
    assert result.endpoints[0].endpoint == "/good"
    assert any(d.code == "AST_PARSE_FALLBACK" for d in result.diagnostics)
    assert result.files_analyzed == 1


def test_fallback_for_wholly_unclosed_class_matches_v0_1_behavior(tmp_path):
    # Caso ya cubierto como regresion de V0.1 (tests/test_edge_cases.py): una clase
    # sin cerrar produce 0 endpoints tanto en el motor de fallback como en V0.1 puro
    # (el motor de fallback no cambia este comportamiento, ver docs/07-Analisis.md).
    (tmp_path / "Broken.java").write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Broken {

            @GetMapping("/x")
            public String list() {
                return "ok";
            }
        """,
        encoding="utf-8",
    )

    result = analyze_project(tmp_path)

    assert result.endpoints == []
    assert any(d.code == "AST_PARSE_FALLBACK" for d in result.diagnostics)
    assert result.files_analyzed == 1


def test_modern_java_syntax_falls_back_without_crashing(tmp_path):
    (tmp_path / "CustomerRecord.java").write_text(
        "package com.example;\n\npublic record CustomerRecord(String name, String email) {}\n",
        encoding="utf-8",
    )

    result = analyze_project(tmp_path)

    assert result.endpoints == []
    assert result.files_analyzed == 1
    assert any(d.code == "AST_PARSE_FALLBACK" for d in result.diagnostics)


def test_mixed_project_ast_and_fallback_files_both_contribute(tmp_path):
    (tmp_path / "GoodController.java").write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class GoodController {
            @GetMapping("/good")
            public String good() { return "ok"; }
        }
        """,
        encoding="utf-8",
    )
    (tmp_path / "BrokenController.java").write_text(
        """
        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class BrokenController {
            @GetMapping("/broken")
            public String broken() {
                return "ok";
            }

            public String malformed(String unterminated {
                return "x";
            }
        }
        """,
        encoding="utf-8",
    )

    result = analyze_project(tmp_path)

    endpoints = {(e.controller, e.endpoint) for e in result.endpoints}
    assert ("GoodController", "/good") in endpoints
    assert ("BrokenController", "/broken") in endpoints
    assert result.files_analyzed == 2


def test_legacy_engine_warning_is_also_wrapped_as_diagnostic(tmp_path):
    # Clase bien formada (para que el motor de fallback la recorra por completo) con
    # un metodo malformado aparte que fuerza la caida a fallback en todo el archivo.
    (tmp_path / "Ambiguous.java").write_text(
        """
        import org.springframework.web.bind.annotation.RequestMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        public class Ambiguous {

            @RequestMapping("/x")
            public String handle() {
                return "ok";
            }

            public String broken(String unterminated {
                return "x";
            }
        }
        """,
        encoding="utf-8",
    )

    result = analyze_project(tmp_path)

    assert any("metodo HTTP explicito" in warning for warning in result.warnings)
    assert any(
        d.code == "LEGACY_ENGINE_WARNING" and "metodo HTTP explicito" in d.message
        for d in result.diagnostics
    )


def test_files_analyzed_counts_all_files_regardless_of_engine(tmp_path):
    (tmp_path / "Good.java").write_text(
        "import org.springframework.web.bind.annotation.RestController;\n@RestController\npublic class Good {}\n",
        encoding="utf-8",
    )
    (tmp_path / "Broken.java").write_text(
        "import org.springframework.web.bind.annotation.RestController;\n@RestController\npublic class Broken {\n",
        encoding="utf-8",
    )

    result = analyze_project(tmp_path)

    assert result.files_analyzed == 2
