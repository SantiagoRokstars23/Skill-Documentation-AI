"""Parseo y validacion de la respuesta cruda del LLM (V0.8).

Separa explicitamente (seccion 16 de
prompts/V0.8—AI-DOCUMENTATION-FOUNDATION.md):

    respuesta cruda (str) -> parsing -> validacion -> dataclass

Sin heuristicas fragiles: la unica tolerancia es un fence de markdown que
envuelva el string COMPLETO (regex anclada a inicio/fin, nunca busca llaves
ni "arregla" contenido interno -- decision explicita de Fase 2, autorizada).
Cualquier clave de "parameters"/"responses"/"dtos" que no este en el
``DocumentationContext``/``EndpointContext`` se trata como una posible
alucinacion y provoca ``DocumentationParseError``, no se descarta en silencio.
"""

from __future__ import annotations

import json
import re

from .errors import DocumentationParseError
from .models import (
    DTODocumentation,
    DocumentationContext,
    EndpointContext,
    EndpointDocumentation,
    ParameterDocumentation,
    ResponseDocumentation,
)

UNKNOWN_STATUS_LABEL = "unknown"

_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*)\n```$", re.DOTALL)


def _strip_markdown_fence(text: str) -> str:
    """Si ``text`` (ya sin espacios en los bordes) esta envuelto por un unico
    fence de markdown que cubre el string completo, devuelve el contenido sin
    el fence. En cualquier otro caso devuelve ``text`` sin tocar -- nunca
    busca fences parciales ni contenido embebido."""
    match = _FENCE_RE.match(text)
    return match.group(1).strip() if match else text


def _load_json_object(raw: str) -> dict:
    candidate = _strip_markdown_fence(raw.strip())
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise DocumentationParseError(
            f"La respuesta del LLM no es JSON valido: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise DocumentationParseError("La respuesta del LLM debe ser un objeto JSON.")
    return data


def _require_str(data: dict, key: str, *, allow_none: bool = False) -> str | None:
    if key not in data:
        raise DocumentationParseError(f"Falta la clave '{key}' en la respuesta del LLM.")
    value = data[key]
    if value is None and allow_none:
        return None
    if not isinstance(value, str):
        raise DocumentationParseError(f"'{key}' debe ser un string.")
    return value


def _require_str_mapping(data: dict, key: str, *, allowed_keys: set[str]) -> dict[str, str]:
    if key not in data:
        raise DocumentationParseError(f"Falta la clave '{key}' en la respuesta del LLM.")
    value = data[key]
    if not isinstance(value, dict):
        raise DocumentationParseError(f"'{key}' debe ser un objeto.")
    unknown = set(value) - allowed_keys
    if unknown:
        raise DocumentationParseError(
            f"'{key}' menciona claves que no estan en el contexto (posible "
            f"alucinacion): {sorted(unknown)}"
        )
    for sub_key, sub_value in value.items():
        if not isinstance(sub_value, str):
            raise DocumentationParseError(f"'{key}.{sub_key}' debe ser un string.")
    return value


def status_label(status: str | None) -> str:
    """Etiqueta usada para emparejar 'responses' entre el contexto y la
    respuesta del LLM. Ver ai/prompts.py -- deliberadamente distinta de la
    convencion "default" del Generator (V0.3), para no mezclar semanticas."""
    return status if status is not None else UNKNOWN_STATUS_LABEL


def parse_project_response(raw: str) -> str:
    """Parsea la respuesta de ``build_project_prompt``. Devuelve
    ``project_description``. Lanza ``DocumentationParseError`` si el formato
    no es el esperado."""
    data = _load_json_object(raw)
    description = _require_str(data, "project_description")
    return description


def parse_endpoint_response(
    raw: str, context: DocumentationContext, endpoint: EndpointContext
) -> tuple[EndpointDocumentation, tuple[DTODocumentation, ...]]:
    """Parsea la respuesta de ``build_endpoint_prompt`` para ``endpoint``.

    Devuelve ``(EndpointDocumentation, dtos)`` -- los DTOs se devuelven por
    separado para que ``DocumentationEngine`` los agregue en el
    ``DocumentationResult`` final (ver Fase 2, seccion "formato de
    respuesta"). ``context`` se usa para resolver los DTOs que ``endpoint``
    referencia transitivamente (DTOs anidados dentro de otros DTOs), la misma
    resolucion que usa ``ai/prompts.py`` para decidir que incluir en el
    prompt -- ambas deben coincidir exactamente."""
    data = _load_json_object(raw)

    description = _require_str(data, "endpoint_description")
    request_description = _require_str(data, "request_description", allow_none=True)

    known_parameter_names = {parameter.name for parameter in endpoint.parameters}
    parameters_raw = _require_str_mapping(data, "parameters", allowed_keys=known_parameter_names)
    parameters = tuple(
        ParameterDocumentation(name=name, description=parameters_raw[name])
        for name in sorted(parameters_raw)
    )

    known_statuses = {status_label(response.status) for response in endpoint.responses}
    responses_raw = _require_str_mapping(data, "responses", allowed_keys=known_statuses)
    responses = tuple(
        ResponseDocumentation(status=status, description=responses_raw[status])
        for status in sorted(responses_raw)
    )

    known_dto_names = context.referenced_dto_names(endpoint)
    dtos_raw = _require_str_mapping(data, "dtos", allowed_keys=known_dto_names)
    dtos = tuple(
        DTODocumentation(name=name, description=dtos_raw[name]) for name in sorted(dtos_raw)
    )

    endpoint_documentation = EndpointDocumentation(
        endpoint_id=endpoint.id,
        description=description,
        parameters=parameters,
        request_description=request_description,
        responses=responses,
    )
    return endpoint_documentation, dtos
