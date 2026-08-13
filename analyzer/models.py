"""Modelo de metadata estructurada producido por el Analyzer.

Ver docs/07-Analisis.md y docs/14-Glosario.md para las definiciones conceptuales de
Endpoint, Parameter y Evidence.
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


@dataclass(frozen=True)
class Evidence:
    """Origen de la informacion extraida del codigo fuente.

    ``line`` es opcional en V0.1: el diseno queda preparado para trazabilidad a nivel
    de linea en fases futuras (ver docs/09-Auditoria.md), sin romper compatibilidad.
    """

    file: str
    line: int | None = None


@dataclass(frozen=True)
class Parameter:
    name: str
    type: str | None
    source: ParameterSource
    required: bool

    def to_dict(self) -> dict:
        data = asdict(self)
        data["source"] = self.source.value
        return data


@dataclass(frozen=True)
class Endpoint:
    controller: str
    endpoint: str
    method: str
    parameters: tuple[Parameter, ...] = field(default_factory=tuple)
    evidence: Evidence | None = None

    def to_dict(self) -> dict:
        return {
            "controller": self.controller,
            "endpoint": self.endpoint,
            "method": self.method,
            "parameters": [p.to_dict() for p in self.parameters],
            "evidence": asdict(self.evidence) if self.evidence else None,
        }


@dataclass
class AnalysisResult:
    """Resultado agregado del analisis de un proyecto Java/Spring Boot."""

    endpoints: list[Endpoint] = field(default_factory=list)
    files_analyzed: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "endpoints": [e.to_dict() for e in self.endpoints],
            "files_analyzed": self.files_analyzed,
            "warnings": list(self.warnings),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
