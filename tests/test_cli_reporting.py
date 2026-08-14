"""Tests de --strict, --quiet, --json y separacion --format/--json (V0.5, Fase 2:
decision explicita de que --format determina el formato del artefacto OpenAPI y
--json determina el formato del reporte de la CLI, nunca lo mismo)."""

from __future__ import annotations

import json
from dataclasses import dataclass

from cli.commands import count_by_severity, resolve_status
from cli.output import _symbol

from ._cli_helpers import EXAMPLE_PROJECT, run_cli


@dataclass
class _FakeStream:
    """Objeto minimo con una codificacion controlable, para simular stdout y
    stderr con codificaciones distintas (ver cli/output.py::_symbol). _symbol
    solo lee ``.encoding``, no necesita comportarse como un stream real."""

    encoding: str


def test_symbol_resolves_against_the_target_stream_not_always_stdout():
    """Regresion: _symbol() debe evaluar la codificacion del stream donde va a
    imprimirse (``file``), no siempre sys.stdout -- el banner puede ir a stderr
    cuando el documento OpenAPI ocupa stdout (--openapi/generate sin --output).
    Antes del fix, un stdout que aceptaba el glifo pero un stderr que lo
    rechazaba provocaba un UnicodeEncodeError no capturado al imprimir en
    stderr."""
    utf8_stream = _FakeStream("utf-8")
    ascii_stream = _FakeStream("ascii")

    assert _symbol(True, file=utf8_stream) == "✓"
    assert _symbol(True, file=ascii_stream) == "OK"
    assert _symbol(False, file=utf8_stream) == "✗"
    assert _symbol(False, file=ascii_stream) == "FAIL"


def test_strict_turns_warnings_into_failure(capsys):
    # el proyecto de ejemplo produce WARNING conocidos (ver examples/README.md); sin
    # --strict el comando es exitoso, con --strict falla.
    exit_code_normal, _, _ = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT)])
    exit_code_strict, _, _ = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT), "--strict"])
    assert exit_code_normal == 0
    assert exit_code_strict == 1


def test_resolve_status_semantics_directly():
    assert resolve_status({"errors": 0, "warnings": 0, "info": 0}, strict=False) == "ok"
    assert resolve_status({"errors": 0, "warnings": 3, "info": 0}, strict=False) == "ok"
    assert resolve_status({"errors": 0, "warnings": 3, "info": 0}, strict=True) == "error"
    assert resolve_status({"errors": 1, "warnings": 0, "info": 0}, strict=False) == "error"
    assert resolve_status({"errors": 1, "warnings": 0, "info": 0}, strict=True) == "error"


def test_count_by_severity_matches_totals():
    from analyzer import Diagnostic, DiagnosticSeverity

    diagnostics = [
        Diagnostic(severity=DiagnosticSeverity.ERROR, code="E", message="e"),
        Diagnostic(severity=DiagnosticSeverity.WARNING, code="W", message="w"),
        Diagnostic(severity=DiagnosticSeverity.WARNING, code="W2", message="w2"),
        Diagnostic(severity=DiagnosticSeverity.INFO, code="I", message="i"),
    ]
    counts = count_by_severity(diagnostics)
    assert counts == {"errors": 1, "warnings": 2, "info": 1}


def test_quiet_suppresses_human_summary_on_success(capsys):
    exit_code, out, err = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT), "--quiet"])
    assert exit_code == 0
    assert out == ""
    assert err == ""


def test_quiet_still_shows_output_when_strict_fails(capsys):
    exit_code, out, err = run_cli(
        capsys, ["analyze", str(EXAMPLE_PROJECT), "--strict", "--quiet"]
    )
    assert exit_code == 1
    # con --strict el resultado es "error": --quiet no debe ocultarlo.
    assert out != "" or err != ""


def test_format_flag_never_changes_json_report_shape(capsys, tmp_path):
    """--format controla el artefacto OpenAPI; --json controla el reporte de la CLI.
    Generar con --format json o --format yaml debe producir el MISMO reporte --json
    (mismas claves/valores salvo la ruta de output), nunca el documento mismo."""
    output_yaml = tmp_path / "out.yaml"
    output_json = tmp_path / "out.json"

    _, out_yaml, _ = run_cli(
        capsys,
        ["generate", str(EXAMPLE_PROJECT), "--format", "yaml", "--output", str(output_yaml), "--json"],
    )
    _, out_json, _ = run_cli(
        capsys,
        ["generate", str(EXAMPLE_PROJECT), "--format", "json", "--output", str(output_json), "--json"],
    )

    report_yaml = json.loads(out_yaml)
    report_json = json.loads(out_json)

    assert report_yaml["diagnostics"] == report_json["diagnostics"]
    assert report_yaml["status"] == report_json["status"]
    # ninguno de los dos reportes --json contiene el documento, independientemente
    # de --format.
    for report in (report_yaml, report_json):
        assert "document" not in report
        assert "paths" not in report
        assert "components" not in report


def test_json_flag_output_is_always_valid_json_regardless_of_format(capsys, tmp_path):
    output_path = tmp_path / "out.json"
    exit_code, out, _ = run_cli(
        capsys,
        ["generate", str(EXAMPLE_PROJECT), "--format", "json", "--output", str(output_path), "--json"],
    )
    assert exit_code == 0
    json.loads(out)  # no lanza excepcion: es JSON valido de punta a punta
