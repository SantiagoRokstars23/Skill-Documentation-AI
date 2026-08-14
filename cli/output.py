"""Formateo de salida de la CLI (V0.5): humano y JSON.

Dos formatos independientes que nunca mezclan responsabilidades (decision
explicita de Fase 2): el reporte ``--json`` nunca incluye el documento OpenAPI
generado, solo referencias a su ubicacion via ``outputs``; el formato humano
nunca imprime el reporte de la operacion como JSON.
"""

from __future__ import annotations

import json
import sys
from typing import TextIO

from analyzer import Diagnostic

from .commands import AnalyzeOutcome, GenerateOutcome, ValidateOutcome


def _symbol(ok: bool, *, file: TextIO) -> str:
    """Resuelve el marcador contra la codificacion de ``file`` (el stream donde se
    va a imprimir), no siempre stdout: el banner puede ir a stderr cuando el
    documento OpenAPI ocupa stdout (ver print_analyze/print_generate). Usar la
    codificacion del stream equivocado puede aprobar un caracter que el stream
    real rechaza, provocando un UnicodeEncodeError no capturado al imprimir."""
    good, bad = "✓", "✗"
    encoding = getattr(file, "encoding", None) or "utf-8"
    try:
        (good if ok else bad).encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return "OK" if ok else "FAIL"
    return good if ok else bad


def _diagnostic_line(diagnostic: Diagnostic) -> str:
    return f"[{diagnostic.severity.value}] {diagnostic.code}: {diagnostic.message}"


def _print_report(
    lines: list[str],
    diagnostics: list[Diagnostic],
    *,
    file: TextIO,
    quiet: bool,
    is_failure: bool,
) -> None:
    """``quiet`` suprime el resumen humano solo cuando el resultado es ``ok``.
    ``is_failure`` refleja el ``status`` ya resuelto (incluye WARNING bajo
    --strict), no solo la presencia de diagnostics ERROR: de lo contrario un
    fallo causado por --strict quedaria completamente silencioso bajo --quiet."""
    if quiet and not is_failure:
        return
    for line in lines:
        print(line, file=file)
    for diagnostic in diagnostics:
        print(_diagnostic_line(diagnostic), file=file)


def print_analyze(
    outcome: AnalyzeOutcome,
    *,
    counts: dict[str, int],
    status: str,
    quiet: bool,
    json_mode: bool,
) -> None:
    if json_mode:
        report: dict = {
            "project": outcome.project,
            "status": status,
            "endpoints": outcome.endpoints,
            "controllers": outcome.controllers,
            "dtos": outcome.dtos,
            "diagnostics": counts,
        }
        if outcome.output_path:
            report["outputs"] = {"openapi": outcome.output_path}
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    banner_file = sys.stderr if outcome.document_text is not None else sys.stdout
    ok = status == "ok"
    lines = [
        f"{_symbol(ok, file=banner_file)} Analysis {'completed' if ok else 'failed'}",
        f"Controllers: {outcome.controllers}",
        f"Endpoints: {outcome.endpoints}",
        f"DTOs: {outcome.dtos}",
        f"Warnings: {counts['warnings']}",
        f"Errors: {counts['errors']}",
    ]
    if outcome.output_path:
        lines.append(f"OpenAPI written to: {outcome.output_path}")
    _print_report(lines, outcome.diagnostics, file=banner_file, quiet=quiet, is_failure=(status == "error"))
    if outcome.document_text is not None:
        print(outcome.document_text)


def print_generate(
    outcome: GenerateOutcome,
    *,
    counts: dict[str, int],
    status: str,
    quiet: bool,
    json_mode: bool,
) -> None:
    if json_mode:
        report = {
            "project": outcome.project,
            "status": status,
            "diagnostics": counts,
            "outputs": {"openapi": outcome.output_path},
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    banner_file = sys.stderr if outcome.document_text is not None else sys.stdout
    ok = status == "ok"
    lines = [f"{_symbol(ok, file=banner_file)} OpenAPI {'generated' if ok else 'generation failed'}"]
    if outcome.output_path:
        lines.append(f"OpenAPI written to: {outcome.output_path}")
    lines.append(f"Warnings: {counts['warnings']}")
    lines.append(f"Errors: {counts['errors']}")
    _print_report(lines, outcome.diagnostics, file=banner_file, quiet=quiet, is_failure=(status == "error"))
    if outcome.document_text is not None:
        print(outcome.document_text)


def print_validate(
    outcome: ValidateOutcome,
    *,
    counts: dict[str, int],
    status: str,
    quiet: bool,
    json_mode: bool,
) -> None:
    if json_mode:
        report = {"file": outcome.file, "status": status, "diagnostics": counts}
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    ok = status == "ok"
    lines = [
        f"{_symbol(ok, file=sys.stdout)} Validation {'completed' if ok else 'failed'}",
        f"Errors: {counts['errors']}",
        f"Warnings: {counts['warnings']}",
        f"Info: {counts['info']}",
    ]
    _print_report(lines, outcome.diagnostics, file=sys.stdout, quiet=quiet, is_failure=(status == "error"))
