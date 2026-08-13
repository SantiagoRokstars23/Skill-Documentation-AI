"""OpenAPI Generator (V0.3): transforma ``analyzer.AnalysisResult`` en un documento
OpenAPI 3.0.3.

Ver docs/05-OpenAPI.md para el contrato y las decisiones documentadas, y
docs/07-Analisis.md para el origen de la metadata consumida. El Generator consume
exclusivamente el modelo publico de ``analyzer``; no analiza Java ni depende de los
motores internos del Analyzer (ver `docs/03-Arquitectura.md`).

Uso:

    from analyzer import analyze_project
    from generators import generate, to_json, to_yaml

    result = analyze_project("examples/customer-service")
    document, diagnostics = generate(result)
    print(to_yaml(document))
"""

from __future__ import annotations

from .openapi_generator import OPENAPI_VERSION, generate, to_json, to_yaml

__all__ = ["OPENAPI_VERSION", "generate", "to_json", "to_yaml"]
