"""Analyzer: analisis estatico de microservicios Java/Spring Boot.

Punto de entrada publico del paquete. Ver docs/07-Analisis.md.
"""

from __future__ import annotations

from pathlib import Path

from .models import AnalysisResult, Endpoint, Evidence, HttpMethod, Parameter, ParameterSource
from .scanner import discover_java_files
from .spring_boot_analyzer import analyze_file

__all__ = [
    "AnalysisResult",
    "Endpoint",
    "Evidence",
    "HttpMethod",
    "Parameter",
    "ParameterSource",
    "analyze_file",
    "analyze_project",
    "discover_java_files",
]


def analyze_project(root: str | Path) -> AnalysisResult:
    """Analiza recursivamente un proyecto Java/Spring Boot y devuelve la metadata
    estructurada de sus endpoints (ver docs/14-Glosario.md)."""
    result = AnalysisResult()
    for java_file in discover_java_files(root):
        endpoints, warnings = analyze_file(java_file)
        result.endpoints.extend(endpoints)
        result.warnings.extend(warnings)
        result.files_analyzed += 1
    return result
