"""Aplicacion de un ``DocumentationResult`` sobre un documento OpenAPI ya
generado (V0.9, "Paso 7 - Integracion" de
prompts/V0.9—SKILL-&-END-TO-END-DOCUMENTATION.md).

Regla central: esta funcion solo puede escribir en campos de texto libre
(``summary``/``description``) -- nunca en ``paths``, metodos, ``parameters``,
``required``, tipos, status codes, ``$ref``, ni puede agregar o quitar
operaciones o schemas. Esto no es solo una instruccion de prompt: los tipos
que esta funcion lee (``EndpointDocumentation``/``ParameterDocumentation``/
``ResponseDocumentation``/``DTODocumentation``, ver ai/models.py) no tienen
ningun campo capaz de representar un path, un metodo o un parametro nuevo --
estructuralmente no hay forma de que una respuesta del LLM, por mas que lo
intente, modifique el contrato (ver seccion 20 de la directriz, "test de no
invencion").

No lanza una excepcion nueva ante una entrada que no puede aplicarse con
seguridad (p. ej. un endpoint del contexto que ya no aparece en el
documento): se omite y se registra como diagnostic, siguiendo el mismo patron
ya establecido por ``generators.generate() -> (document, diagnostics)``
(V0.3) -- un desajuste no es una falla catastrofica, es la misma nocion de
"incertidumbre que se conserva, no se oculta" que gobierna todo el proyecto.
"""

from __future__ import annotations

import copy

from .models import DocumentationContext, DocumentationResult
from .parsing import UNKNOWN_STATUS_LABEL

# Heuristica especifica de este proyecto (mismo patron y mismo texto literal
# que ya usa validator/openapi_rules.py::_GENERATOR_DEFAULT_RESPONSE_DESCRIPTION
# -- duplicado deliberadamente en vez de importado: ai/ no debe depender de
# generators/ ni de validator/, y ese texto es una convencion privada del
# Generator, no una API publica). Si el Generator cambia este texto, esta
# heuristica deja de reconocer el placeholder y simplemente no se reemplaza
# (nunca se rompe, nunca sobrescribe un valor real por error).
_GENERATOR_DEFAULT_RESPONSE_DESCRIPTION = (
    "Respuesta generada automaticamente (sin descripcion disponible en la evidencia)."
)

# Convencion del Generator (V0.3, generators/openapi_generator.py): la clave
# de respuesta usada en el documento OpenAPI cuando no hay evidencia de
# @ResponseStatus. ai/parsing.py::status_label() etiqueta ese mismo caso como
# UNKNOWN_STATUS_LABEL ("unknown") al construir el contexto/prompt del LLM,
# deliberadamente distinto del nombre que usa el Generator (ver el docstring
# de status_label). Sin esta reconciliacion, la descripcion que el LLM genera
# para una respuesta sin status resuelto nunca encontraria su lugar en el
# documento real -- se perderia en silencio para la mayoria de los endpoints
# de un proyecto real, que no declaran @ResponseStatus explicitamente.
_GENERATOR_UNRESOLVED_STATUS_KEY = "default"


def _resolve_response_key(responses: dict, status: str) -> str | None:
    if status in responses:
        return status
    if status == UNKNOWN_STATUS_LABEL and _GENERATOR_UNRESOLVED_STATUS_KEY in responses:
        return _GENERATOR_UNRESOLVED_STATUS_KEY
    return None


def _is_blank(value: object) -> bool:
    return not isinstance(value, str) or not value.strip()


def apply_documentation(
    document: dict,
    documentation: DocumentationResult,
    context: DocumentationContext,
) -> tuple[dict, list[str]]:
    """Devuelve ``(documento_enriquecido, diagnostics)``.

    ``document`` nunca se muta (se trabaja sobre una copia profunda). Cada
    entrada de ``documentation`` que no pueda ubicarse de forma segura en
    ``document`` se omite y se agrega un mensaje a ``diagnostics`` -- nunca se
    lanza una excepcion por un desajuste de este tipo.
    """
    enriched = copy.deepcopy(document)
    diagnostics: list[str] = []

    _apply_project_description(enriched, documentation, diagnostics)

    paths = enriched.get("paths")
    if not isinstance(paths, dict):
        diagnostics.append(
            "El documento no tiene 'paths' como objeto; no se aplico ningun "
            "enriquecimiento de endpoints."
        )
        paths = None

    for endpoint_documentation in documentation.endpoints:
        endpoint_context = context.get_endpoint(endpoint_documentation.endpoint_id)
        if endpoint_context is None:
            diagnostics.append(
                f"'{endpoint_documentation.endpoint_id}' no esta en el contexto; "
                "se omite su enriquecimiento."
            )
            continue
        if paths is None:
            continue
        _apply_endpoint_documentation(paths, endpoint_context, endpoint_documentation, diagnostics)

    components = enriched.get("components")
    schemas = components.get("schemas") if isinstance(components, dict) else None
    if isinstance(schemas, dict):
        for dto_documentation in documentation.dtos:
            _apply_dto_documentation(schemas, dto_documentation, diagnostics)
    elif documentation.dtos:
        diagnostics.append(
            "El documento no tiene 'components.schemas'; se omitio el "
            "enriquecimiento de DTOs."
        )

    return enriched, diagnostics


def _apply_project_description(
    document: dict, documentation: DocumentationResult, diagnostics: list[str]
) -> None:
    if not documentation.project_description:
        return
    info = document.get("info")
    if not isinstance(info, dict):
        diagnostics.append("El documento no tiene 'info' como objeto; se omitio la descripcion del proyecto.")
        return
    if _is_blank(info.get("description")):
        info["description"] = documentation.project_description


def _apply_endpoint_documentation(
    paths: dict,
    endpoint_context,
    endpoint_documentation,
    diagnostics: list[str],
) -> None:
    path_item = paths.get(endpoint_context.path)
    if not isinstance(path_item, dict):
        diagnostics.append(
            f"'{endpoint_context.path}' no existe en 'paths' del documento; se omite "
            f"el enriquecimiento de '{endpoint_documentation.endpoint_id}'."
        )
        return
    operation = path_item.get(endpoint_context.method.lower())
    if not isinstance(operation, dict):
        diagnostics.append(
            f"'{endpoint_context.method} {endpoint_context.path}' no existe en el "
            f"documento; se omite el enriquecimiento de '{endpoint_documentation.endpoint_id}'."
        )
        return

    if endpoint_documentation.summary and _is_blank(operation.get("summary")):
        operation["summary"] = endpoint_documentation.summary
    if endpoint_documentation.description and _is_blank(operation.get("description")):
        operation["description"] = endpoint_documentation.description

    if endpoint_documentation.parameters:
        _apply_parameter_documentation(operation, endpoint_documentation, diagnostics)

    if endpoint_documentation.responses:
        _apply_response_documentation(operation, endpoint_documentation, diagnostics)


def _apply_parameter_documentation(operation: dict, endpoint_documentation, diagnostics: list[str]) -> None:
    parameters = operation.get("parameters")
    if not isinstance(parameters, list):
        if endpoint_documentation.parameters:
            diagnostics.append(
                f"'{endpoint_documentation.endpoint_id}' no tiene 'parameters' en el "
                "documento; se omitieron sus descripciones."
            )
        return
    by_name = {
        parameter_documentation.name: parameter_documentation.description
        for parameter_documentation in endpoint_documentation.parameters
    }
    for parameter_obj in parameters:
        if not isinstance(parameter_obj, dict):
            continue
        name = parameter_obj.get("name")
        if name in by_name and _is_blank(parameter_obj.get("description")):
            parameter_obj["description"] = by_name[name]


def _apply_response_documentation(operation: dict, endpoint_documentation, diagnostics: list[str]) -> None:
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        diagnostics.append(
            f"'{endpoint_documentation.endpoint_id}' no tiene 'responses' en el "
            "documento; se omitieron sus descripciones."
        )
        return
    for response_documentation in endpoint_documentation.responses:
        key = _resolve_response_key(responses, response_documentation.status)
        if key is None:
            diagnostics.append(
                f"'{endpoint_documentation.endpoint_id}': la respuesta con status "
                f"'{response_documentation.status}' no existe en el documento; se "
                "omitio su descripcion."
            )
            continue
        response_obj = responses[key]
        if not isinstance(response_obj, dict):
            continue
        current = response_obj.get("description")
        if _is_blank(current) or current == _GENERATOR_DEFAULT_RESPONSE_DESCRIPTION:
            response_obj["description"] = response_documentation.description


def _apply_dto_documentation(schemas: dict, dto_documentation, diagnostics: list[str]) -> None:
    schema = schemas.get(dto_documentation.name)
    if not isinstance(schema, dict):
        diagnostics.append(
            f"'{dto_documentation.name}' no esta en 'components.schemas' del documento; "
            "se omitio su descripcion."
        )
        return
    if _is_blank(schema.get("description")):
        schema["description"] = dto_documentation.description
