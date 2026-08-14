"""PromptEngine (V0.8): construye prompts a partir de ``DocumentationContext``.

No conoce ningun proveedor concreto (ver
prompts/V0.8—AI-DOCUMENTATION-FOUNDATION.md seccion 9): recibe y devuelve solo
``str``, sin importar ``providers/`` en absoluto.

Las instrucciones anti-alucinacion y el formato esperado viven centralizados
aqui (seccion 10 de la directriz), no dispersos por el resto de la capa AI.
"""

from __future__ import annotations

import json

from .errors import DocumentationError
from .models import DocumentationContext, EndpointContext

PROMPT_VERSION = "1.0"

_ANTI_HALLUCINATION_RULES = """\
Reglas obligatorias:
- Usa EXCLUSIVAMENTE la informacion presente en el contexto JSON de abajo.
- No inventes endpoints, parametros, codigos HTTP, reglas de negocio, \
autenticacion, ni nombres de entidades que no esten en el contexto.
- No asumas comportamiento que el contexto no represente explicitamente.
- Si algo no puede determinarse a partir del contexto, usa exactamente el \
texto "No determinado por el analisis" en el campo correspondiente, en vez \
de inventar un valor plausible.
- Responde en espanol.
- Responde EXCLUSIVAMENTE con un objeto JSON valido, sin texto antes ni \
despues, sin explicaciones adicionales."""

_PROJECT_RESPONSE_FORMAT = """\
Formato de respuesta esperado (unicamente estas claves, JSON valido):
{"project_description": "<texto>"}"""

_ENDPOINT_RESPONSE_FORMAT = """\
Formato de respuesta esperado (unicamente estas claves, JSON valido):
{
  "endpoint_description": "<texto>",
  "parameters": {"<nombre_de_parametro_del_contexto>": "<texto>"},
  "request_description": "<texto o null si el endpoint no tiene request body>",
  "responses": {"<status_del_contexto>": "<texto>"},
  "dtos": {"<nombre_de_dto_del_contexto>": "<texto>"}
}
Las claves de "parameters", "responses" y "dtos" deben ser EXACTAMENTE un \
subconjunto de los nombres/status que aparecen en el contexto entregado -- \
nunca inventes una clave que no este ahi. Para "responses", usa el valor de \
"status" del contexto tal cual (como texto); si "status" es null en el \
contexto, usa la clave "unknown". Si el endpoint no tiene \
parametros/responses/dtos en el contexto, devuelve un objeto vacio ({}) para \
esa clave."""


class DocumentationPromptBuilder:
    """Construye los dos tipos de prompt de V0.8: uno por proyecto (resumen
    compacto) y uno por endpoint (detalle del endpoint y sus DTOs)."""

    def build_project_prompt(self, context: DocumentationContext) -> str:
        payload = {
            "project_name": context.project_name,
            "endpoint_count": len(context.endpoints),
            "controllers": sorted({endpoint.controller for endpoint in context.endpoints}),
            "endpoints": [
                {"id": endpoint.id, "method": endpoint.method, "path": endpoint.path}
                for endpoint in context.endpoints
            ],
        }
        return self._build_prompt(
            task="Redacta una descripcion general de este proyecto Spring Boot, en base "
            "unicamente al siguiente contexto (controllers y endpoints detectados).",
            response_format=_PROJECT_RESPONSE_FORMAT,
            context_payload=payload,
        )

    def build_endpoint_prompt(self, context: DocumentationContext, endpoint_id: str) -> str:
        endpoint = context.get_endpoint(endpoint_id)
        if endpoint is None:
            raise DocumentationError(
                f"El contexto no contiene ningun endpoint con id '{endpoint_id}'."
            )
        payload = {
            "endpoint": endpoint.to_dict(),
            "dtos": [
                dto.to_dict()
                for dto in self._referenced_dtos(context, endpoint)
            ],
        }
        return self._build_prompt(
            task="Redacta la documentacion tecnica de este endpoint (descripcion, "
            "parametros, request body si aplica, y cada response), en base "
            "unicamente al siguiente contexto.",
            response_format=_ENDPOINT_RESPONSE_FORMAT,
            context_payload=payload,
        )

    @staticmethod
    def _referenced_dtos(context: DocumentationContext, endpoint: EndpointContext):
        # Incluye DTOs anidados transitivamente (p. ej. Address dentro de
        # CustomerRequest), no solo los referenciados directamente por el
        # endpoint -- misma resolucion que usa ai/parsing.py para aceptar esas
        # mismas claves en la respuesta del LLM (ver
        # DocumentationContext.referenced_dto_names).
        names = context.referenced_dto_names(endpoint)
        return [context.get_dto(name) for name in sorted(names) if context.get_dto(name)]

    @staticmethod
    def _build_prompt(*, task: str, response_format: str, context_payload: dict) -> str:
        context_json = json.dumps(
            context_payload, indent=2, ensure_ascii=False, sort_keys=True
        )
        return (
            f"{task}\n\n"
            f"{_ANTI_HALLUCINATION_RULES}\n\n"
            f"{response_format}\n\n"
            f"Contexto:\n{context_json}"
        )
