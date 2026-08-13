"""Modelo de metadata estructurada producido por el Analyzer.

Ver docs/07-Analisis.md y docs/14-Glosario.md para las definiciones conceptuales.

V0.2 amplia el modelo de V0.1 (Endpoint, Parameter, Evidence, AnalysisResult) de forma
aditiva: todos los campos nuevos son opcionales con valores por defecto, por lo que el
codigo de V0.1 (incluido analyzer/spring_boot_analyzer.py, sin modificar) sigue
construyendo estas estructuras exactamente igual que antes. Ver docs/13-Versionado.md.

Principio de V0.2 (ver prompts/V0.2-...): el Analyzer produce evidencia, no
inferencias. Ningun campo de este modelo se rellena con un valor supuesto cuando la
informacion no puede determinarse de forma confiable a partir del codigo: en ese caso
el campo queda en ``None``/vacio y, cuando corresponde, se emite un ``Diagnostic``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ParameterSource(str, Enum):
    PATH = "path"
    QUERY = "query"
    BODY = "body"
    HEADER = "header"


class DiagnosticSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True)
class Evidence:
    """Origen de la informacion extraida del codigo fuente.

    ``symbol`` y ``type`` se agregan en V0.2 (ver seccion 5.10 de la directriz V0.2)
    para identificar, ademas del archivo y la linea, el simbolo Java concreto (nombre
    de clase, metodo, campo) y el tipo de elemento (``"endpoint"``, ``"dto"``,
    ``"field"``, ``"parameter"``, ...) al que corresponde la evidencia. Ambos son
    opcionales para no romper compatibilidad con el uso existente de V0.1
    (``Evidence(file=..., line=...)``).
    """

    file: str
    line: int | None = None
    symbol: str | None = None
    type: str | None = None


@dataclass(frozen=True)
class Validation:
    """Evidencia de una anotacion de Bean Validation reconocida (ver docs/07-Analisis.md).

    ``args`` es el texto crudo de los atributos de la anotacion (p. ej. "min=1, max=50"),
    o cadena vacia si la anotacion no tiene atributos. No se interpreta semanticamente.
    """

    name: str
    args: str = ""
    evidence: Evidence | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "args": self.args,
            "evidence": asdict(self.evidence) if self.evidence else None,
        }


@dataclass(frozen=True)
class Diagnostic:
    """Hallazgo estructurado del Analyzer (ver seccion 5.11 de la directriz V0.2).

    Reemplaza/complementa el canal plano ``AnalysisResult.warnings`` de V0.1 con
    severidad, codigo estable y evidencia. ``AnalysisResult.warnings`` se mantiene por
    compatibilidad (ver docs/13-Versionado.md) y se deriva de los diagnostics de
    severidad WARNING generados durante el analisis.
    """

    severity: DiagnosticSeverity
    code: str
    message: str
    evidence: Evidence | None = None

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "evidence": asdict(self.evidence) if self.evidence else None,
        }


@dataclass(frozen=True)
class Field:
    """Campo de un DTO (ver seccion 5.4 de la directriz V0.2).

    ``nested_dto`` solo se rellena cuando el tipo (desenvuelto de colecciones/Optional)
    del campo resuelve, de forma no ambigua, a otra clase/enum del proyecto indexada
    por el Analyzer (ver analyzer/dto_analyzer.py). Si no se puede resolver con
    confianza, permanece en ``None`` en vez de suponerse.
    """

    name: str
    type: str
    is_collection: bool = False
    validations: tuple[Validation, ...] = field(default_factory=tuple)
    nested_dto: "DTO | None" = None
    evidence: Evidence | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "is_collection": self.is_collection,
            "validations": [v.to_dict() for v in self.validations],
            "nested_dto": self.nested_dto.to_dict() if self.nested_dto else None,
            "evidence": asdict(self.evidence) if self.evidence else None,
        }


@dataclass(frozen=True)
class DTO:
    """Modelo estructurado de una clase/enum referenciada por un endpoint (seccion 5.4).

    ``kind`` es ``"class"`` o ``"enum"``. Para ``kind == "enum"``, ``fields`` queda
    vacio y ``enum_constants`` contiene los nombres de las constantes; para
    ``kind == "class"`` es al reves.
    """

    name: str
    kind: str
    fields: tuple[Field, ...] = field(default_factory=tuple)
    enum_constants: tuple[str, ...] = field(default_factory=tuple)
    evidence: Evidence | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "fields": [f.to_dict() for f in self.fields],
            "enum_constants": list(self.enum_constants),
            "evidence": asdict(self.evidence) if self.evidence else None,
        }


@dataclass(frozen=True)
class Response:
    """Informacion de respuesta de un endpoint (ver seccion 5.5 de la directriz V0.2).

    ``wrapper`` es el tipo contenedor (p. ej. ``"ResponseEntity"``) o ``None`` si el
    tipo de retorno no usa un wrapper reconocido. ``body_type`` es el texto del tipo
    del cuerpo (p. ej. ``"CustomerResponse"`` o ``"List<CustomerResponse>"``), o
    ``None`` si el metodo no retorna valor (``void``).
    """

    wrapper: str | None
    body_type: str | None
    is_collection: bool = False
    dto: DTO | None = None
    status: str | None = None
    evidence: Evidence | None = None

    def to_dict(self) -> dict:
        return {
            "wrapper": self.wrapper,
            "body_type": self.body_type,
            "is_collection": self.is_collection,
            "dto": self.dto.to_dict() if self.dto else None,
            "status": self.status,
            "evidence": asdict(self.evidence) if self.evidence else None,
        }


@dataclass(frozen=True)
class Parameter:
    name: str
    type: str | None
    source: ParameterSource
    required: bool
    default_value: str | None = None
    validations: tuple[Validation, ...] = field(default_factory=tuple)
    dto: DTO | None = None
    evidence: Evidence | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "source": self.source.value,
            "required": self.required,
            "default_value": self.default_value,
            "validations": [v.to_dict() for v in self.validations],
            "dto": self.dto.to_dict() if self.dto else None,
            "evidence": asdict(self.evidence) if self.evidence else None,
        }


@dataclass(frozen=True)
class Controller:
    """Clase Java que expone endpoints (``@RestController``/``@Controller``, seccion 5.1).

    Complementa a ``Endpoint.controller`` (que sigue siendo el nombre simple, por
    compatibilidad): ``Controller`` agrega anotaciones, modificadores y el base path
    a nivel de clase, sin duplicarlos en cada Endpoint.
    """

    name: str
    annotations: tuple[str, ...] = field(default_factory=tuple)
    modifiers: tuple[str, ...] = field(default_factory=tuple)
    base_path: str = ""
    evidence: Evidence | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "annotations": list(self.annotations),
            "modifiers": list(self.modifiers),
            "base_path": self.base_path,
            "evidence": asdict(self.evidence) if self.evidence else None,
        }


@dataclass(frozen=True)
class Endpoint:
    controller: str
    endpoint: str
    method: str
    parameters: tuple[Parameter, ...] = field(default_factory=tuple)
    evidence: Evidence | None = None
    java_method: str | None = None
    consumes: tuple[str, ...] = field(default_factory=tuple)
    produces: tuple[str, ...] = field(default_factory=tuple)
    response: Response | None = None
    security: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "controller": self.controller,
            "endpoint": self.endpoint,
            "method": self.method,
            "parameters": [p.to_dict() for p in self.parameters],
            "evidence": asdict(self.evidence) if self.evidence else None,
            "java_method": self.java_method,
            "consumes": list(self.consumes),
            "produces": list(self.produces),
            "response": self.response.to_dict() if self.response else None,
            "security": list(self.security),
        }


@dataclass
class AnalysisResult:
    """Resultado agregado del analisis de un proyecto Java/Spring Boot."""

    endpoints: list[Endpoint] = field(default_factory=list)
    files_analyzed: int = 0
    warnings: list[str] = field(default_factory=list)
    controllers: list[Controller] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "endpoints": [e.to_dict() for e in self.endpoints],
            "files_analyzed": self.files_analyzed,
            "warnings": list(self.warnings),
            "controllers": [c.to_dict() for c in self.controllers],
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
