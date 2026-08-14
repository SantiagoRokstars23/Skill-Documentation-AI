"""Modelo de datos de la capa AI (V0.8).

Dos familias de estructuras, ambas ``@dataclass(frozen=True)`` y construidas
exclusivamente con tipos inmutables (``str``/``bool``/``tuple``/dataclasses
anidadas frozen -- nunca ``list``/``dict`` como campo, mismo patron ya usado en
``analyzer/models.py`` para garantizar inmutabilidad real):

- ``DocumentationContext`` (y sus dataclasses anidadas): la proyeccion
  serializable, determinista y verificable de ``AnalysisResult`` (mas el
  ``info.title`` del documento OpenAPI si esta disponible) que se le entrega al
  LLM. Independiente de cualquier provider/SDK.
- ``DocumentationResult`` (y sus dataclasses anidadas): la salida ya parseada y
  validada de la capa AI, lista para serializarse a JSON.

Ninguna de las dos depende de ``providers/`` ni de ningun proveedor concreto.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


# ---------------------------------------------------------------------------
# DocumentationContext
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParameterContext:
    name: str
    source: str
    type: str | None
    required: bool
    default_value: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DTOFieldContext:
    name: str
    type: str
    is_collection: bool
    validations: tuple[str, ...] = field(default_factory=tuple)
    nested_dto_name: str | None = None
    """Nombre del DTO referenciado por este campo (``Field.nested_dto.name`` en
    el Analyzer), si el tipo del campo resuelve a otro DTO del contexto. Es lo
    que permite a ``DocumentationContext.referenced_dto_names`` resolver DTOs
    anidados de forma transitiva (p. ej. ``Address`` dentro de
    ``CustomerRequest``) -- sin este campo, un DTO anidado quedaba coleccionado
    en ``DocumentationContext.dtos`` pero nunca llegaba al prompt ni podia ser
    aceptado por el parser (ver ai/prompts.py/ai/parsing.py)."""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "is_collection": self.is_collection,
            "validations": list(self.validations),
            "nested_dto_name": self.nested_dto_name,
        }


@dataclass(frozen=True)
class DTOContext:
    name: str
    kind: str
    fields: tuple[DTOFieldContext, ...] = field(default_factory=tuple)
    enum_constants: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "fields": [f.to_dict() for f in self.fields],
            "enum_constants": list(self.enum_constants),
        }


@dataclass(frozen=True)
class ResponseContext:
    status: str | None
    body_type: str | None
    is_collection: bool
    dto_name: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EndpointContext:
    id: str
    controller: str
    method: str
    path: str
    parameters: tuple[ParameterContext, ...] = field(default_factory=tuple)
    request_dto_name: str | None = None
    consumes: tuple[str, ...] = field(default_factory=tuple)
    produces: tuple[str, ...] = field(default_factory=tuple)
    responses: tuple[ResponseContext, ...] = field(default_factory=tuple)
    security: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "controller": self.controller,
            "method": self.method,
            "path": self.path,
            "parameters": [p.to_dict() for p in self.parameters],
            "request_dto_name": self.request_dto_name,
            "consumes": list(self.consumes),
            "produces": list(self.produces),
            "responses": [r.to_dict() for r in self.responses],
            "security": list(self.security),
        }


@dataclass(frozen=True)
class DocumentationContext:
    """Entrada completa, inmutable y serializable para la capa de prompts.

    ``dtos`` esta deduplicado por nombre y ordenado alfabeticamente (nunca por
    orden de descubrimiento) para que el mismo ``AnalysisResult`` produzca
    siempre el mismo contexto. Ver ``ai/context.py``.
    """

    project_name: str | None
    endpoints: tuple[EndpointContext, ...] = field(default_factory=tuple)
    dtos: tuple[DTOContext, ...] = field(default_factory=tuple)
    diagnostics_summary: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "dtos": [d.to_dict() for d in self.dtos],
            "diagnostics_summary": list(self.diagnostics_summary),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, sort_keys=True)

    def get_endpoint(self, endpoint_id: str) -> EndpointContext | None:
        """Busca un ``EndpointContext`` por ``id``; ``None`` si no existe."""
        for endpoint in self.endpoints:
            if endpoint.id == endpoint_id:
                return endpoint
        return None

    def get_dto(self, name: str) -> DTOContext | None:
        """Busca un ``DTOContext`` por nombre; ``None`` si no existe."""
        for dto in self.dtos:
            if dto.name == name:
                return dto
        return None

    def referenced_dto_names(self, endpoint: EndpointContext) -> frozenset[str]:
        """DTOs que ``endpoint`` referencia, directa o transitivamente (DTOs
        anidados dentro de otros DTOs, via ``DTOFieldContext.nested_dto_name``
        -- p. ej. ``Address`` dentro de ``CustomerRequest``).

        Fuente unica de verdad usada tanto por ``ai/prompts.py`` (para decidir
        que ``DTOContext`` incluir en el prompt) como por ``ai/parsing.py``
        (para decidir que claves de ``dtos`` acepta la respuesta del LLM sin
        tratarlas como una alucinacion) -- deben coincidir exactamente."""
        names: set[str] = set()
        pending: list[str] = []
        if endpoint.request_dto_name:
            pending.append(endpoint.request_dto_name)
        for response in endpoint.responses:
            if response.dto_name:
                pending.append(response.dto_name)

        while pending:
            name = pending.pop()
            if name in names:
                continue
            names.add(name)
            dto = self.get_dto(name)
            if dto is None:
                continue
            for dto_field in dto.fields:
                if dto_field.nested_dto_name:
                    pending.append(dto_field.nested_dto_name)

        return frozenset(names)


# ---------------------------------------------------------------------------
# DocumentationResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParameterDocumentation:
    name: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResponseDocumentation:
    status: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DTODocumentation:
    name: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EndpointDocumentation:
    endpoint_id: str
    summary: str
    description: str
    parameters: tuple[ParameterDocumentation, ...] = field(default_factory=tuple)
    request_description: str | None = None
    responses: tuple[ResponseDocumentation, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "endpoint_id": self.endpoint_id,
            "summary": self.summary,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "request_description": self.request_description,
            "responses": [r.to_dict() for r in self.responses],
        }


@dataclass(frozen=True)
class DocumentationResult:
    """Salida final de ``DocumentationEngine.generate()``: ya parseada y
    validada contra el ``DocumentationContext`` que la origino."""

    project_description: str | None
    endpoints: tuple[EndpointDocumentation, ...] = field(default_factory=tuple)
    dtos: tuple[DTODocumentation, ...] = field(default_factory=tuple)
    diagnostics: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "project_description": self.project_description,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "dtos": [d.to_dict() for d in self.dtos],
            "diagnostics": list(self.diagnostics),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, sort_keys=True)
