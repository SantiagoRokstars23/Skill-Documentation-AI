"""Orquestador del OpenAPI Generator (V0.3): ``AnalysisResult`` -> documento OpenAPI 3.0.3.

Consume exclusivamente el modelo publico de ``analyzer`` (``AnalysisResult``,
``Endpoint``, ``Parameter``, ``Response``, ...). No importa ``javalang``,
``analyzer.spring_boot_analyzer``, ``analyzer.ast_analyzer``, ``analyzer.dto_analyzer``
ni ``analyzer.scanner`` (seccion 2.1 de la directriz V0.3: Analyzer y Generator son
responsabilidades separadas).

Principio de evidencia (seccion 2.2): ninguna decision de este modulo presenta una
convencion propia (version por defecto de ``info``, tipo de contenido por defecto,
clave de respuesta ``"default"`` cuando no hay evidencia de status) como si fuera
evidencia extraida del codigo. Cada convencion esta documentada explicitamente en el
codigo y, cuando corresponde, acompañada de un ``Diagnostic``.

Determinismo (seccion 12): el orden de ``paths``, de las operaciones dentro de un
path, de ``components.schemas`` y de ``parameters`` es explicito (no se confia en el
orden de ``AnalysisResult.endpoints``, que refleja un detalle interno del Analyzer --
motor AST primero, motor de fallback despues -- y no es un orden canonico util aqui).
"""

from __future__ import annotations

import json

import yaml

from analyzer import AnalysisResult, Diagnostic, DiagnosticSeverity, Endpoint, ParameterSource

from .openapi_schemas import SchemaRegistry, schema_ref_for_dto
from .openapi_types import apply_validations, build_type_schema

OPENAPI_VERSION = "3.0.3"

_DEFAULT_MEDIA_TYPE = "application/json"
"""Convencion documentada (no evidencia): se usa unicamente cuando existe evidencia de
un cuerpo (DTO/tipo) pero no de su tipo de contenido (`consumes`/`produces` ausentes),
consistente con el uso predominante de Spring REST. Nunca sustituye evidencia real."""

_DEFAULT_RESPONSE_DESCRIPTION = (
    "Respuesta generada automaticamente (sin descripcion disponible en la evidencia)."
)

_HTTP_STATUS_CODES: dict[str, int] = {
    "CONTINUE": 100,
    "SWITCHING_PROTOCOLS": 101,
    "PROCESSING": 102,
    "OK": 200,
    "CREATED": 201,
    "ACCEPTED": 202,
    "NON_AUTHORITATIVE_INFORMATION": 203,
    "NO_CONTENT": 204,
    "RESET_CONTENT": 205,
    "PARTIAL_CONTENT": 206,
    "MULTIPLE_CHOICES": 300,
    "MOVED_PERMANENTLY": 301,
    "FOUND": 302,
    "SEE_OTHER": 303,
    "NOT_MODIFIED": 304,
    "TEMPORARY_REDIRECT": 307,
    "PERMANENT_REDIRECT": 308,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "PAYMENT_REQUIRED": 402,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "NOT_ACCEPTABLE": 406,
    "REQUEST_TIMEOUT": 408,
    "CONFLICT": 409,
    "GONE": 410,
    "LENGTH_REQUIRED": 411,
    "PRECONDITION_FAILED": 412,
    "PAYLOAD_TOO_LARGE": 413,
    "UNSUPPORTED_MEDIA_TYPE": 415,
    "UNPROCESSABLE_ENTITY": 422,
    "LOCKED": 423,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "NOT_IMPLEMENTED": 501,
    "BAD_GATEWAY": 502,
    "SERVICE_UNAVAILABLE": 503,
    "GATEWAY_TIMEOUT": 504,
}
"""Tabla de constantes ``org.springframework.http.HttpStatus`` -> codigo numerico.
Ampliable; un nombre no listado aqui se trata como evidencia no resoluble (ver
``_resolve_status_code``), nunca se adivina un numero."""


def generate(result: AnalysisResult) -> tuple[dict, list[Diagnostic]]:
    """Genera el documento OpenAPI 3.0.3 (como ``dict``) a partir de ``AnalysisResult``.

    Devuelve ``(documento, diagnostics)``. ``diagnostics`` son hallazgos propios del
    Generator (no confundir con ``result.diagnostics`` del Analyzer, que no se
    modifican ni se reemiten aqui)."""
    diagnostics: list[Diagnostic] = []
    registry: SchemaRegistry = {}
    used_operation_ids: dict[str, int] = {}
    paths: dict[str, dict] = {}

    for endpoint in sorted(result.endpoints, key=lambda e: (e.endpoint, e.method)):
        operation = _build_operation(endpoint, registry, diagnostics, used_operation_ids)
        path_item = paths.setdefault(endpoint.endpoint, {})
        path_item[endpoint.method.lower()] = operation

    document: dict = {
        "openapi": OPENAPI_VERSION,
        "info": {"title": "Generated API", "version": "0.0.0"},
        "paths": dict(sorted(paths.items())),
    }
    if registry:
        document["components"] = {"schemas": dict(sorted(registry.items()))}

    return document, diagnostics


def to_json(document: dict, *, indent: int = 2) -> str:
    return json.dumps(document, indent=indent, ensure_ascii=False, sort_keys=False)


def to_yaml(document: dict) -> str:
    return yaml.safe_dump(document, sort_keys=False, allow_unicode=True, default_flow_style=False)


# ---------------------------------------------------------------------------
# Operation
# ---------------------------------------------------------------------------


def _build_operation(
    endpoint: Endpoint,
    registry: SchemaRegistry,
    diagnostics: list[Diagnostic],
    used_operation_ids: dict[str, int],
) -> dict:
    operation: dict = {"operationId": _compute_operation_id(endpoint, used_operation_ids)}
    if endpoint.controller:
        operation["tags"] = [endpoint.controller]

    parameters = _build_parameters(endpoint, diagnostics)
    if parameters:
        operation["parameters"] = parameters

    request_body = _build_request_body(endpoint, registry, diagnostics)
    if request_body is not None:
        operation["requestBody"] = request_body

    operation["responses"] = _build_responses(endpoint, registry, diagnostics)

    security_evidence = _security_extension(endpoint, diagnostics)
    if security_evidence is not None:
        operation["x-security-evidence"] = security_evidence

    return operation


# ---------------------------------------------------------------------------
# operationId (seccion 13 de la directriz V0.3)
# ---------------------------------------------------------------------------


def _pascal(text: str) -> str:
    return text[0].upper() + text[1:] if text else text


def _normalize_path_segment(path: str) -> str:
    segments = [s for s in path.strip("/").split("/") if s]
    tokens = []
    for segment in segments:
        if segment.startswith("{") and segment.endswith("}"):
            tokens.append("By" + _pascal(segment[1:-1]))
        else:
            tokens.append(_pascal(segment))
    return "".join(tokens) if tokens else "Root"


def _compute_operation_id(endpoint: Endpoint, used_operation_ids: dict[str, int]) -> str:
    """Prioridad autorizada: HTTP + Controller + java_method; si ``java_method`` no
    esta disponible (endpoints del motor de fallback, ver docs/07-Analisis.md):
    HTTP + endpoint normalizado. Colisiones se resuelven con sufijo numerico
    determinista (``_2``, ``_3``, ...), nunca hashes ni valores aleatorios."""
    if endpoint.java_method:
        base = f"{endpoint.method.lower()}{_pascal(endpoint.controller)}{_pascal(endpoint.java_method)}"
    else:
        base = f"{endpoint.method.lower()}{_normalize_path_segment(endpoint.endpoint)}"

    count = used_operation_ids.get(base, 0) + 1
    used_operation_ids[base] = count
    return base if count == 1 else f"{base}_{count}"


# ---------------------------------------------------------------------------
# Parameters (path/query/header) y requestBody
# ---------------------------------------------------------------------------


def _build_parameters(endpoint: Endpoint, diagnostics: list[Diagnostic]) -> list[dict]:
    parameters = []
    for parameter in endpoint.parameters:
        if parameter.source == ParameterSource.BODY:
            continue

        schema = build_type_schema(parameter.type, None, diagnostics, parameter.evidence)
        is_collection = schema.get("type") == "array"
        schema = apply_validations(schema, parameter.validations, is_collection=is_collection)
        if parameter.default_value is not None:
            schema["default"] = _coerce_default(parameter.default_value, schema.get("type"))

        location = parameter.source.value
        # OpenAPI exige required=true para parametros "in: path" siempre (restriccion
        # estructural del formato de salida, no una afirmacion sobre el codigo fuente).
        required = True if location == "path" else parameter.required

        parameters.append(
            {
                "name": parameter.name,
                "in": location,
                "required": required,
                "schema": schema,
            }
        )
    return sorted(parameters, key=lambda item: (item["in"], item["name"]))


def _coerce_default(text: str, openapi_type: str | None):
    if openapi_type == "integer":
        try:
            return int(text)
        except ValueError:
            return text
    if openapi_type == "number":
        try:
            return float(text)
        except ValueError:
            return text
    if openapi_type == "boolean" and text.lower() in ("true", "false"):
        return text.lower() == "true"
    return text


def _build_request_body(
    endpoint: Endpoint, registry: SchemaRegistry, diagnostics: list[Diagnostic]
) -> dict | None:
    body_parameter = next(
        (p for p in endpoint.parameters if p.source == ParameterSource.BODY), None
    )
    if body_parameter is None:
        return None

    def resolve_ref(dto):
        return schema_ref_for_dto(dto, registry, diagnostics)

    schema = build_type_schema(
        body_parameter.type,
        body_parameter.dto,
        diagnostics,
        body_parameter.evidence,
        resolve_dto_ref=resolve_ref,
    )
    is_collection = schema.get("type") == "array"
    schema = apply_validations(schema, body_parameter.validations, is_collection=is_collection)

    if endpoint.consumes:
        media_types = list(endpoint.consumes)
    else:
        media_types = [_DEFAULT_MEDIA_TYPE]
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.INFO,
                code="OPENAPI_MEDIA_TYPE_CONVENTION",
                message=(
                    "No hay evidencia de 'consumes' para el cuerpo de la peticion de "
                    f"'{endpoint.method} {endpoint.endpoint}'; se usa "
                    f"'{_DEFAULT_MEDIA_TYPE}' como convencion documentada (no evidencia)."
                ),
                evidence=endpoint.evidence,
            )
        )

    return {
        "required": body_parameter.required,
        "content": {media_type: {"schema": schema} for media_type in media_types},
    }


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


def _resolve_status_code(status_text: str | None) -> str | None:
    if not status_text:
        return None
    name = status_text.rsplit(".", 1)[-1]
    code = _HTTP_STATUS_CODES.get(name)
    return str(code) if code is not None else None


def _build_responses(
    endpoint: Endpoint, registry: SchemaRegistry, diagnostics: list[Diagnostic]
) -> dict:
    response = endpoint.response

    if response is None:
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.WARNING,
                code="OPENAPI_RESPONSE_NO_EVIDENCE",
                message=(
                    f"El endpoint '{endpoint.method} {endpoint.endpoint}' no tiene "
                    "informacion de respuesta en la metadata (analizado por el motor "
                    "de fallback de V0.1, ver docs/07-Analisis.md); se genera una "
                    "respuesta conservadora bajo la clave 'default', sin cuerpo ni "
                    "codigo de estado verificados."
                ),
                evidence=endpoint.evidence,
            )
        )
        return {"default": {"description": _DEFAULT_RESPONSE_DESCRIPTION}}

    status_code = _resolve_status_code(response.status)

    body_schema = None
    if response.body_type not in (None, "void"):

        def resolve_ref(dto):
            return schema_ref_for_dto(dto, registry, diagnostics)

        body_schema = build_type_schema(
            response.body_type, response.dto, diagnostics, response.evidence, resolve_dto_ref=resolve_ref
        )

    if status_code is None:
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.WARNING,
                code="OPENAPI_RESPONSE_STATUS_UNKNOWN",
                message=(
                    f"No hay evidencia de un codigo de estado HTTP para "
                    f"'{endpoint.method} {endpoint.endpoint}' (sin @ResponseStatus "
                    "reconocible); se genera la respuesta bajo la clave 'default' en "
                    "vez de asumir un codigo (p. ej. 200) sin evidencia."
                ),
                evidence=endpoint.evidence,
            )
        )
        key = "default"
    else:
        key = status_code

    entry: dict = {"description": _DEFAULT_RESPONSE_DESCRIPTION}
    if body_schema:
        media_types = list(endpoint.produces) if endpoint.produces else [_DEFAULT_MEDIA_TYPE]
        entry["content"] = {media_type: {"schema": body_schema} for media_type in media_types}
    return {key: entry}


# ---------------------------------------------------------------------------
# Security (conservador -- seccion "Security" de la directriz V0.3)
# ---------------------------------------------------------------------------


def _security_extension(endpoint: Endpoint, diagnostics: list[Diagnostic]) -> list[str] | None:
    if not endpoint.security:
        return None
    diagnostics.append(
        Diagnostic(
            severity=DiagnosticSeverity.WARNING,
            code="OPENAPI_SECURITY_EVIDENCE_ONLY",
            message=(
                f"Se detecto evidencia de seguridad ({', '.join(endpoint.security)}) "
                f"para '{endpoint.method} {endpoint.endpoint}', pero no permite "
                "determinar un securityScheme OpenAPI concreto (oauth2/apiKey/http). "
                "Se documenta como extension 'x-security-evidence' en vez de inventar "
                "un esquema de seguridad."
            ),
            evidence=endpoint.evidence,
        )
    )
    return list(endpoint.security)
