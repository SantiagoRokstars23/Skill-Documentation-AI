"""OpenAPI Quality Validator (V0.4): analiza documentos OpenAPI 3.0.3 ya construidos
y detecta problemas estructurales y de calidad.

Ver prompts/V0.4-OPENAPI-VALIDATOR.md para el Scope Lock y docs/05-OpenAPI.md para el
contrato. El Validator consume exclusivamente el documento OpenAPI (``dict`` o texto
JSON/YAML); no analiza Java, no llama al Analyzer ni al Generator, y nunca modifica
el documento recibido.

Uso:

    from analyzer import analyze_project
    from generators import generate
    from validator import validate

    result = analyze_project("examples/customer-service")
    document, _ = generate(result)
    diagnostics = validate(document)
    for diagnostic in diagnostics:
        print(diagnostic.severity.value, diagnostic.code, diagnostic.message)
"""

from __future__ import annotations

from .openapi_validator import validate, validate_json, validate_yaml

__all__ = ["validate", "validate_json", "validate_yaml"]
