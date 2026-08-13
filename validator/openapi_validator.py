"""Orquestador del OpenAPI Quality Validator (V0.4).

Consume exclusivamente un documento OpenAPI ya construido (``dict``, o texto
JSON/YAML que se parsea a un ``dict``). No importa ``analyzer.ast_analyzer``,
``analyzer.dto_analyzer``, ``analyzer.spring_boot_analyzer``, ``analyzer.scanner``,
``javalang`` ni ``generators`` -- el Validator no vuelve a analizar Java ni llama al
Generator (ver Scope Lock, prompts/V0.4-OPENAPI-VALIDATOR.md seccion 24).

El Validator es de solo lectura: nunca modifica el documento recibido.

Determinismo: ``document["paths"]``, sus metodos, ``parameters`` y
``components.schemas``/``securitySchemes`` siempre se recorren en orden ordenado
explicitamente (nunca en el orden de insercion accidental del dict de entrada).
"""

from __future__ import annotations

import json

import yaml

from analyzer import Diagnostic, DiagnosticSeverity, Evidence

from . import openapi_rules as rules


def validate(document) -> list[Diagnostic]:
    """Valida un documento OpenAPI 3.0.3 ya construido. Devuelve una lista de
    ``Diagnostic`` (posiblemente vacia). Nunca lanza excepcion ni modifica
    ``document``."""
    diagnostics: list[Diagnostic] = []

    if not isinstance(document, dict):
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="OPENAPI_DOCUMENT_NOT_OBJECT",
                message="El documento raiz debe ser un objeto (dict); se recibio otro tipo.",
                evidence=Evidence(file="", type="document"),
            )
        )
        return diagnostics

    rules.check_root(document, diagnostics)

    components_index = rules.build_components_index(document)
    used_refs: set[tuple[str, str]] = set()
    operation_ids: dict[str, list[str]] = {}

    paths = document.get("paths")
    if isinstance(paths, dict):
        rules.check_paths(paths, diagnostics, components_index, used_refs, operation_ids)

    rules.check_components(document, diagnostics, components_index, used_refs)

    rules.check_duplicate_operation_ids(operation_ids, diagnostics)
    rules.check_unreferenced_schemas(components_index, used_refs, diagnostics)

    return diagnostics


def validate_json(text: str) -> list[Diagnostic]:
    """Parsea ``text`` como JSON y valida el resultado. Ante un error de parseo,
    devuelve un unico ``Diagnostic`` (``OPENAPI_JSON_PARSE_ERROR``) sin lanzar
    excepcion."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        return [
            Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="OPENAPI_JSON_PARSE_ERROR",
                message=f"No se pudo parsear el JSON: {exc}",
                evidence=Evidence(file="", type="document"),
            )
        ]
    return validate(document)


def validate_yaml(text: str) -> list[Diagnostic]:
    """Parsea ``text`` como YAML y valida el resultado. Ante un error de parseo,
    devuelve un unico ``Diagnostic`` (``OPENAPI_YAML_PARSE_ERROR``) sin lanzar
    excepcion."""
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [
            Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="OPENAPI_YAML_PARSE_ERROR",
                message=f"No se pudo parsear el YAML: {exc}",
                evidence=Evidence(file="", type="document"),
            )
        ]
    return validate(document)
