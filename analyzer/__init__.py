"""Analyzer: analisis estatico de microservicios Java/Spring Boot.

Punto de entrada publico del paquete. Ver docs/07-Analisis.md.

V0.2 (ver prompts/V0.2-ADVANCED-SPRING-BOOT-ANALYZER.md): ``analyze_project`` opera en
dos pasadas.

1. Para cada archivo ``.java`` descubierto, intenta parsearlo como AST
   (``ast_backend.parse_file``, motor principal V0.2 basado en ``javalang``). Las
   unidades que se parsean correctamente se indexan por nombre de clase/enum
   (``dto_analyzer.build_class_index``) para poder resolver DTOs referenciados desde
   otros archivos del proyecto (p. ej. un ``@RequestBody`` cuyo tipo esta definido en
   otro archivo).
2. Construye la metadata por archivo: si el AST esta disponible, usa
   ``ast_analyzer.analyze_compilation_unit`` (Controllers/Endpoints/Parameters con las
   capacidades ampliadas de V0.2: DTOs, validaciones, response, headers,
   consumes/produces, evidencia de seguridad). Si el archivo no pudo parsearse como
   AST (sintaxis no soportada por ``javalang``, codigo malformado, o error de
   lectura), recurre sin ninguna modificacion al motor de V0.1
   (``analyzer/spring_boot_analyzer.py``, regex + balanceo de brackets) para ese
   archivo especifico. Esto preserva integramente el comportamiento y las garantias
   de V0.1 (incluida la tolerancia a archivos malformados) para los casos en los que
   el motor AST no puede procesar el archivo. Ver la decision Regex vs AST
   documentada en docs/03-Arquitectura.md y docs/07-Analisis.md.

``AnalysisResult.warnings`` (``list[str]``, V0.1) se mantiene por compatibilidad y se
puebla tanto con los mensajes de los ``Diagnostic`` de severidad WARNING producidos
por el motor AST como con los warnings del motor de fallback. ``AnalysisResult.
diagnostics`` (V0.2) es el canal estructurado equivalente, mas rico, para todo lo
anterior mas los eventos exclusivos del motor AST (uso de fallback, DTOs ambiguos,
referencias ciclicas).
"""

from __future__ import annotations

from pathlib import Path

from . import ast_analyzer, ast_backend, dto_analyzer
from .models import (
    DTO,
    AnalysisResult,
    Controller,
    Diagnostic,
    DiagnosticSeverity,
    Endpoint,
    Evidence,
    Field,
    HttpMethod,
    Parameter,
    ParameterSource,
    Response,
    Validation,
)
from .scanner import discover_java_files
from .spring_boot_analyzer import analyze_file

__all__ = [
    "DTO",
    "AnalysisResult",
    "Controller",
    "Diagnostic",
    "DiagnosticSeverity",
    "Endpoint",
    "Evidence",
    "Field",
    "HttpMethod",
    "Parameter",
    "ParameterSource",
    "Response",
    "Validation",
    "analyze_file",
    "analyze_project",
    "discover_java_files",
]


def analyze_project(root: str | Path) -> AnalysisResult:
    """Analiza recursivamente un proyecto Java/Spring Boot y devuelve la metadata
    estructurada de sus endpoints (ver docs/14-Glosario.md)."""
    files = discover_java_files(root)
    result = AnalysisResult()

    parsed_units: dict[str, tuple] = {}
    fallback_files: list[Path] = []

    for java_file in files:
        try:
            unit, text = ast_backend.parse_file(java_file)
        except ast_backend.AstParseError as exc:
            fallback_files.append(java_file)
            result.diagnostics.append(
                Diagnostic(
                    severity=DiagnosticSeverity.INFO,
                    code="AST_PARSE_FALLBACK",
                    message=(
                        f"No se pudo analizar '{java_file}' con el motor AST ({exc}); "
                        "se usa el motor de V0.1 (regex) como fallback para este archivo."
                    ),
                    evidence=Evidence(file=str(java_file)),
                )
            )
            continue
        parsed_units[str(java_file)] = (unit, text)

    class_index = dto_analyzer.build_class_index(parsed_units)

    for file_label, (unit, _text) in parsed_units.items():
        endpoints, controllers, diagnostics = ast_analyzer.analyze_compilation_unit(
            unit, file_label, class_index
        )
        result.endpoints.extend(endpoints)
        result.controllers.extend(controllers)
        result.diagnostics.extend(diagnostics)
        result.warnings.extend(d.message for d in diagnostics if d.severity == DiagnosticSeverity.WARNING)
        result.files_analyzed += 1

    for java_file in fallback_files:
        endpoints, warnings = analyze_file(java_file)
        result.endpoints.extend(endpoints)
        result.warnings.extend(warnings)
        result.diagnostics.extend(
            Diagnostic(
                severity=DiagnosticSeverity.WARNING,
                code="LEGACY_ENGINE_WARNING",
                message=warning,
                evidence=Evidence(file=str(java_file)),
            )
            for warning in warnings
        )
        result.files_analyzed += 1

    return result
