"""Orquestacion de los tres comandos de la CLI (V0.5): analyze, generate, validate.

Cada funcion ``run_*`` llama exclusivamente a las APIs publicas de ``analyzer``,
``generators`` y ``validator`` (ver docs/03-Arquitectura.md); no reimplementa
analisis, generacion ni validacion. No imprime nada: devuelve un resultado
("outcome") que ``cli/output.py`` se encarga de presentar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from analyzer import DTO, AnalysisResult, Diagnostic, DiagnosticSeverity, analyze_project
from generators import generate as generate_openapi
from generators import to_json as openapi_to_json
from generators import to_yaml as openapi_to_yaml
from validator import validate as validate_openapi
from validator import validate_json as validate_openapi_json
from validator import validate_yaml as validate_openapi_yaml

from .errors import CliUsageError

EXIT_OK = 0
EXIT_DIAGNOSTICS = 1
EXIT_USAGE = 2
EXIT_INTERNAL = 3


@dataclass
class AnalyzeOutcome:
    project: str
    endpoints: int
    controllers: int
    dtos: int
    diagnostics: list[Diagnostic] = field(default_factory=list)
    document_text: str | None = None
    output_path: str | None = None


@dataclass
class GenerateOutcome:
    project: str
    diagnostics: list[Diagnostic] = field(default_factory=list)
    document_text: str | None = None
    output_path: str | None = None


@dataclass
class ValidateOutcome:
    file: str
    diagnostics: list[Diagnostic] = field(default_factory=list)


def count_by_severity(diagnostics: list[Diagnostic]) -> dict[str, int]:
    counts = {"errors": 0, "warnings": 0, "info": 0}
    for diagnostic in diagnostics:
        if diagnostic.severity == DiagnosticSeverity.ERROR:
            counts["errors"] += 1
        elif diagnostic.severity == DiagnosticSeverity.WARNING:
            counts["warnings"] += 1
        else:
            counts["info"] += 1
    return counts


def resolve_status(counts: dict[str, int], *, strict: bool) -> str:
    if counts["errors"] > 0:
        return "error"
    if strict and counts["warnings"] > 0:
        return "error"
    return "ok"


def status_to_exit_code(status: str) -> int:
    return EXIT_DIAGNOSTICS if status == "error" else EXIT_OK


def _collect_dtos(dto: DTO, seen: dict[str, DTO]) -> None:
    if dto.name in seen:
        return
    seen[dto.name] = dto
    for dto_field in dto.fields:
        if dto_field.nested_dto is not None:
            _collect_dtos(dto_field.nested_dto, seen)


def count_dtos(result: AnalysisResult) -> int:
    """Cuenta DTOs distintos (por nombre) referenciados desde parametros o
    respuestas, incluyendo DTOs anidados de forma transitiva.

    ``AnalysisResult`` no expone una lista agregada de DTOs (estan embebidos en
    ``Parameter.dto``/``Response.dto``/``Field.nested_dto``): este calculo es
    agregacion de presentacion sobre la API publica existente, no un dato nuevo
    del Analyzer.
    """
    seen: dict[str, DTO] = {}
    for endpoint in result.endpoints:
        for parameter in endpoint.parameters:
            if parameter.dto is not None:
                _collect_dtos(parameter.dto, seen)
        if endpoint.response is not None and endpoint.response.dto is not None:
            _collect_dtos(endpoint.response.dto, seen)
    return len(seen)


def require_project_dir(project: str) -> Path:
    path = Path(project)
    if not path.is_dir():
        raise CliUsageError(f"El proyecto '{project}' no existe o no es un directorio.")
    return path


def require_existing_file(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_file():
        raise CliUsageError(f"El archivo '{path_str}' no existe o no es un archivo.")
    return path


def serialize_document(document: dict, fmt: str) -> str:
    return openapi_to_json(document) if fmt == "json" else openapi_to_yaml(document)


def write_output_file(path_str: str, text: str) -> None:
    path = Path(path_str)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise CliUsageError(f"No se pudo escribir en '{path_str}': {exc}") from exc


def run_analyze(
    project: str,
    *,
    openapi: bool,
    fmt: str,
    output: str | None,
    json_mode: bool,
) -> AnalyzeOutcome:
    if output and not openapi:
        raise CliUsageError("--output solo es valido junto con --openapi en 'analyze'.")
    if json_mode and openapi and not output:
        raise CliUsageError(
            "--json combinado con --openapi requiere --output: el reporte JSON y el "
            "documento OpenAPI no pueden compartir la salida estandar."
        )

    require_project_dir(project)
    result = analyze_project(project)
    diagnostics = list(result.diagnostics)
    document_text: str | None = None
    output_path: str | None = None

    if openapi:
        document, generator_diagnostics = generate_openapi(result)
        diagnostics.extend(generator_diagnostics)
        diagnostics.extend(validate_openapi(document))
        text = serialize_document(document, fmt)
        if output:
            write_output_file(output, text)
            output_path = output
        else:
            document_text = text

    return AnalyzeOutcome(
        project=project,
        endpoints=len(result.endpoints),
        controllers=len(result.controllers),
        dtos=count_dtos(result),
        diagnostics=diagnostics,
        document_text=document_text,
        output_path=output_path,
    )


def run_generate(
    project: str,
    *,
    fmt: str,
    output: str | None,
    json_mode: bool,
) -> GenerateOutcome:
    if json_mode and not output:
        raise CliUsageError(
            "--json requiere --output en 'generate': el reporte JSON y el documento "
            "OpenAPI no pueden compartir la salida estandar."
        )

    require_project_dir(project)
    result = analyze_project(project)
    document, generator_diagnostics = generate_openapi(result)
    diagnostics = list(result.diagnostics) + list(generator_diagnostics)
    text = serialize_document(document, fmt)

    document_text: str | None = None
    output_path: str | None = None
    if output:
        write_output_file(output, text)
        output_path = output
    else:
        document_text = text

    return GenerateOutcome(
        project=project,
        diagnostics=diagnostics,
        document_text=document_text,
        output_path=output_path,
    )


def run_validate(openapi_file: str) -> ValidateOutcome:
    path = require_existing_file(openapi_file)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CliUsageError(f"No se pudo leer '{openapi_file}': {exc}") from exc
    if path.suffix.lower() == ".json":
        diagnostics = validate_openapi_json(text)
    else:
        # YAML es superconjunto de JSON: cubre ".yaml"/".yml" y cualquier otra
        # extension sin --format propio para 'validate' (Fase 2, seccion 2: sin
        # --format en validate).
        diagnostics = validate_openapi_yaml(text)
    return ValidateOutcome(file=openapi_file, diagnostics=diagnostics)
